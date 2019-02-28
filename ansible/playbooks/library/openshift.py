#!/usr/bin/python
# -*- coding: utf-8 -*-

# Imported from the Kubespray project and modified; see ../../../LICENSE

from ansible.module_utils.basic import *  # noqa
try:
    from ansible.errors import AnsibleError
except ImportError:
    AnsibleError = Exception


DOCUMENTATION = """
---
module: kube
short_description: Manage state in a Kubernetes Cluster
description:
  - Create, replace, remove, and stop resources within a Kubernetes Cluster
version_added: "2.0"
options:
  name:
    required: false
    default: null
    description:
      - The name associated with resource
  filename:
    required: false
    default: null
    description:
      - The path and filename of the resource(s) definition file(s).
      - To operate on several files this can accept a comma separated list of files or a list of files.
    aliases: [ 'files', 'file', 'filenames' ]
  content:
    required: false
    default: null
    description:
      - The plain-text YAML to pass to "oc create"'s standard input
  oc:
    required: false
    default: null
    description:
      - The path to the oc bin
  namespace:
    required: false
    default: null
    description:
      - The namespace associated with the resource(s)
  resource:
    required: false
    default: null
    description:
      - The resource to perform an action on. pods (po), replicationControllers (rc), services (svc)
  label:
    required: false
    default: null
    description:
      - The labels used to filter specific resources.
  server:
    required: false
    default: null
    description:
      - The url for the API server that commands are executed against.
  force:
    required: false
    default: false
    description:
      - A flag to indicate to force delete, replace, or stop.
  all:
    required: false
    default: false
    description:
      - A flag to indicate delete all, stop all, or all namespaces when checking exists.
  log_level:
    required: false
    default: 0
    description:
      - Indicates the level of verbosity of logging by oc.
  state:
    required: false
    choices: ['present', 'absent', 'latest', 'reloaded', 'stopped']
    default: present
    description:
      - present handles checking existence or creating if definition file provided,
        absent handles deleting resource(s) based on other options,
        latest handles creating or updating based on existence,
        reloaded handles updating resource(s) definition using definition file,
        stopped handles stopping resource(s) based on other options.
requirements:
  - oc
author: "Kenny Jones (@kenjones-cisco)"
"""

EXAMPLES = """
- name: test nginx is present
  kube: name=nginx resource=rc state=present

- name: test nginx is stopped
  kube: name=nginx resource=rc state=stopped

- name: test nginx is absent
  kube: name=nginx resource=rc state=absent

- name: test nginx is present
  kube: filename=/tmp/nginx.yml

- name: test nginx and postgresql are present
  kube: files=/tmp/nginx.yml,/tmp/postgresql.yml

- name: test nginx and postgresql are present
  kube:
    files:
      - /tmp/nginx.yml
      - /tmp/postgresql.yml
"""


class KubeManager(object):

    def __init__(self, module):

        self.module = module

        self.oc = module.params.get('oc')
        if self.oc is None:
            self.oc = module.get_bin_path('oc', True, ['/opt/bin'])
        self.base_cmd = [self.oc]

        if module.params.get('server'):
            self.base_cmd.append('--server=' + module.params.get('server'))

        if module.params.get('log_level'):            self.base_cmd.append('--v=' + str(module.params.get('log_level')))

        if module.params.get('namespace'):
            self.base_cmd.append('--namespace=' + module.params.get('namespace'))

        self.all = module.params.get('all')
        self.force = module.params.get('force')
        self.name = module.params.get('name')
        self.filename = [f.strip() for f in module.params.get('filename') or []]
        self.content = module.params.get('content', None)
        self.resource = module.params.get('resource')
        self.label = module.params.get('label')

    def _execute(self, cmd, **kwargs):
        args = self.base_cmd + cmd
        try:
            rc, out, err = self.module.run_command(args, **kwargs)
            if rc != 0:
                raise AnsibleError(
                    'error running oc (%s) command (rc=%d), out=\'%s\', err=\'%s\'' % (' '.join(args), rc, out, err))
        except Exception as exc:
            raise AnsibleError(
                'error running oc (%s) command: %s' % (' '.join(args), str(exc)))
        return self.module.exit_json(changed=True, rc=rc, stdout=out)

    def _execute_nofail(self, cmd):
        args = self.base_cmd + cmd
        rc, out, err = self.module.run_command(args)
        return rc == 0

    def create(self, check=True, force=True):
        if check and self.exists():
            return self.module.exit_json(changed=False)

        cmd = ['apply']

        if force:
            cmd.append('--force')

        if self.content is not None:
            cmd.extend(['-f', '-'])
            return self._execute(cmd, data=self.content)
        elif self.filename:
            cmd.append('--filename=' + ','.join(self.filename))
            return self._execute(cmd)
        else:
            raise AnsibleError('filename or content required')


    def replace(self, force=True):

        cmd = ['apply']

        if force:
            cmd.append('--force')

        if self.content is not None:
            cmd.extend(['-f', '-'])
            return self._execute(cmd, data=self.content)
        elif self.filename:
            cmd.append('--filename=' + ','.join(self.filename))
            return self._execute(cmd)
        else:
            raise AnsibleError('filename required to reload')

    def delete(self):

        if not self.force and not self.exists():
            return self.module.exit_json(changed=False)

        cmd = ['delete']

        if self.filename:
            cmd.append('--filename=' + ','.join(self.filename))
        else:
            if not self.resource:
                raise AnsibleError('resource required to delete without filename')

            cmd.append(self.resource)

            if self.name:
                cmd.append(self.name)

            if self.label:
                cmd.append('--selector=' + self.label)

            if self.all:
                cmd.append('--all')

            if self.force:
                cmd.append('--ignore-not-found')

        return self._execute(cmd)

    def exists(self):
        cmd = ['get']

        if self.filename:
            cmd.append('--filename=' + ','.join(self.filename))
        else:
            if not self.resource:
                raise AnsibleError('resource required without filename')

            cmd.append(self.resource)

            if self.name:
                cmd.append(self.name)

            if self.label:
                cmd.append('--selector=' + self.label)

            if self.all:
                cmd.append('--all-namespaces')

        cmd.append('--no-headers')

        return self._execute_nofail(cmd)

    # TODO: This is currently unused, perhaps convert to 'scale' with a replicas param?
    def stop(self):

        if not self.force and not self.exists():
            return self.module.exit_json(changed=False)

        cmd = ['stop']

        if self.filename:
            cmd.append('--filename=' + ','.join(self.filename))
        else:
            if not self.resource:
                raise AnsibleError('resource required to stop without filename')

            cmd.append(self.resource)

            if self.name:
                cmd.append(self.name)

            if self.label:
                cmd.append('--selector=' + self.label)

            if self.all:
                cmd.append('--all')

            if self.force:
                cmd.append('--ignore-not-found')

        return self._execute(cmd)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(),
            filename=dict(type='list', aliases=['files', 'file', 'filenames']),
            content=dict(type='str'),
            namespace=dict(),
            resource=dict(),
            label=dict(),
            server=dict(),
            oc=dict(),
            force=dict(default=False, type='bool'),
            all=dict(default=False, type='bool'),
            log_level=dict(default=0, type='int'),
            state=dict(default='present', choices=['present', 'absent', 'latest', 'reloaded', 'stopped']),
            ),
            mutually_exclusive=[['filename', 'content']]
        )

    manager = KubeManager(module)
    state = module.params.get('state')
    if state == 'present':
        return manager.create()

    elif state == 'absent':
        return manager.delete()

    elif state == 'reloaded':
        return manager.replace()

    elif state == 'stopped':
        return manager.stop()

    elif state == 'latest':
        return manager.replace()

    else:
        raise AnsibleError('Unrecognized state %s.' % state)

if __name__ == '__main__':
    main()
