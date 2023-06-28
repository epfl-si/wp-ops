# Ansible variables

The variables in the table can be set from the wpsible command line to alter the behavior of the configuration-as-code.

| Variable              | Used in                                   | Explanation                                                                                                                                                            |
|-----------------------|-------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `awx_playbook_branch` | ansible/roles/awx-instance/tasks/main.yml | Set this to override the branch that AWX (previously known as Ansible Tower) shall check out playbooks from (default is `master` in production, and the operator's current branch in test) |
|                       |                                           |                                                                                                                                                                        |
|                       |                                           |                                                                                                                                                                        |
