#!/usr/bin/env python3
# -*- coding: utf-8; -*-

# All rights reserved. © ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland, 2021

import os

from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.plugins.inventory.script import InventoryModule as ScriptInventory
from ansible.plugins.inventory.yaml   import InventoryModule as YAMLInventory


DOCUMENTATION = '''
    inventory: lazy_inventory
    plugin_type: inventory
    short_description: Only render the inventory for real the second time it gets called.
    description: |
      This is to implement “lazy” inventory sources, that only do real work after
      `meta: refresh_inventory` gets called on purpose (after the playbook
      figures out that it does need the full inventory, e.g. from the set of
      tags in use).
    options:
      lazy_inventory:
        description: Describes the fake inventory to return the first time around
        type: dict
      full_inventory:
        description: Describes the complete inventory to return the second time around
        type: dict
'''


EXAMPLES = '''
plugin: lazy_inventory
lazy_inventory:
  # The first time around (i.e. at ansible-playbook initialization time),
  # render an empty group:
  literal:
    this_group_intentionally_left_blank:
      hosts: {}
full_inventory:
  # The second time around (i.e. after `meta: refresh_inventory`),
  # jump to the "real" script (whose path may be specified relative
  # to the inventory plugin YAML configuration file):
  script: my-costly-inventory-script.py
'''


class Counter:
    def __init__(self):
        self._counter = 0

    def get_value_and_increment(self):
        retval = self._counter
        self._counter += 1
        return retval


class InventoryModule(BaseInventoryPlugin):
    _execution_counter = Counter()

    def parse(self, inventory, loader, path, cache):
        super(InventoryModule, self).parse(inventory, loader, path, cache)
        self._lazy_config_path = path
        self.homedir = os.path.dirname(path)

        self.set_options(
            # ... from DOCUMENTATION, above, with...
            direct=loader.load_from_file(path, cache=False))
        lazy_inventory = self.get_option("lazy_inventory")
        full_inventory = self.get_option("full_inventory")
        self._delegate_parse(
            inventory,
            full_inventory if self._execution_counter.get_value_and_increment() >= 1
                           else lazy_inventory)

    def _delegate_parse(self, inventory, descriptor):
        """Delegate to one of the Ansible inventory plug-ins according to `descriptor`."""
        if "literal" in descriptor:
            inventory_data = descriptor["literal"]
            class FakeLoader:
                def load_from_file(_self, path, **kwargs):
                    return inventory_data
                def get_basedir(_self):
                    return self.homedir

            delegate_class = YAMLInventory
            loader = FakeLoader()
            path = self._lazy_config_path

        elif "script" in descriptor:
            delegate_class = ScriptInventory
            loader = self.loader
            path = os.path.join(self.homedir, descriptor["script"])

        else:
            raise ValueError("Cannot figure out what to do from configuration keys: " +
                             ", ".join(descriptor.keys()))


        class DelegateLoader(delegate_class):
            def set_options(self):
                pass
        return DelegateLoader().parse(inventory, loader, path, cache=False)
