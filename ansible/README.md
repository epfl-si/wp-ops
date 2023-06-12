# Ansible and Ansible Tower (AWX)

This directory contains the support code for Ansible and Ansible Tower
(aka AWX), which the WordPress uses extensively as its
infrastructure-as-code.

Theoretically, the entire serving infrastructure can be brought up
from a backup into an OpenShift namespace that the operator has access
to (through `oc login`). This is done with the `wpsible` wrapper
script. Additionnally, `wpsible` brings up Ansible Tower, which also
can perform the day-to-day subset of the same operations, either on a
crontab-like basis, or interactively from the Ansible Tower Web UI.

| Filename                           | Purpose                                                                                                 |
|------------------------------------|---------------------------------------------------------------------------------------------------------|
| `wpsible`                          | The shell wrapper that the operator runs interactively. Always `cd`s to the `ansible` directory first.  |
| `ansible.cfg`                      | The configuration file for `wpsible` - Unused by AWX                                                    |
| `requirements.yml`                 | The general Ansible Galaxy requirements for `wpsible`                                                   |
| `roles`                            | The Ansible roles, available to both `wpsible` and AWX                                                  |
| `inventory`                        | The inventory files and executable inventory scripts for `wpsible`                                      |
| `inventory/wordpress-instances.py` | This one script is automatically synced into AWX, and executed from there                               |
| `playbooks`                        | The playbooks that both `wpsible` and AWX can run                                                       |
| `.interactive-playbooks`           | The playbooks that only `wpsible` can run (hidden so that AWX won't find them)                          |
| `vars`                             | Variables that are common to multiple Ansible roles                                                     |
| `eyaml`                            | The public keys used to encrypt secrets. (The secret keys are on Keybase)                               |
| `state`                            | Non-infrastructure-as-code state (e.g., backups)                                                        |

