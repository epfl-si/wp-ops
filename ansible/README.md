# Ansible playbook

This directory contains the support code for Ansible, which the
WordPress project uses extensively as its infrastructure-as-code.

Theoretically, the entire serving infrastructure can be brought up
from a backup into an OpenShift namespace that the operator has access
to (through `oc login`). This is done with the `wpsible` wrapper
script.

| Filename                           | Purpose                                                                                                 |
|------------------------------------|---------------------------------------------------------------------------------------------------------|
| `wpsible`                          | The shell wrapper that the operator runs interactively. Always `cd`s to the `ansible` directory first.  |
| `ansible.cfg`                      | The configuration file for `wpsible`                                                                    |
| `requirements.yml`                 | The general Ansible Galaxy requirements for `wpsible`                                                   |
| `roles`                            | The Ansible roles                                                                                       |
| `inventory`                        | The inventory files for `wpsible`                                                                       |
| `playbook.yml`                     | The playbook that applies all roles                                                                     |
| `vars`                             | Variables that are common to multiple Ansible roles                                                     |
| `eyaml`                            | The public keys used to encrypt secrets. (The secret keys are on Keybase)                               |
| `state`                            | Non-infrastructure-as-code state (e.g., backups)                                                        |

