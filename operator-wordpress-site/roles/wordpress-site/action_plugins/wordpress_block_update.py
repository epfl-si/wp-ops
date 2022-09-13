import sys
import os.path
import re
import json
import requests

# To be able to import wordpress_action_module
sys.path.append(os.path.dirname(__file__))

from wordpress_action_module import WordPressActionModule

class ActionModule(WordPressActionModule):

    def _get_memento_categories(self):
        """
        Returns the Memento categories in json format
        """
        rest_api_url = "https://memento.epfl.ch/api/v1/categories/?format=json&limit=100"
        response = requests.get(rest_api_url)
        return response.json()

    def get_memento_category_label(self, memento_category_id):
        """
        Returns the label of the category id 'memento_category_id'
        """
        for category in self._get_memento_categories()['results']:
            if category['id'] == memento_category_id:
              return category['en_label']

    def find_blocks(self, page_content, block_name='wp:epfl/memento'):
        """
        Returns all Gutenberg blocks with the name "block_name" present in the page content.
        """
        regex = '(<!-- {} .*? /-->)'.format(block_name)
        matching_reg = re.compile("{}".format(regex))
        return matching_reg.findall(page_content)

    def convert_category_to_categories(self, html_block):
        """
        Converts the attribute "category" to "categories".

        html_block: <!-- wp:epfl/memento {"category":"9"} -->
        return <!-- wp:epfl/memento {"categories":"[{"label":"Cultural events","value":9}]"} -->
        """
        html_block = html_block.replace("category", "categories", 1)
        regex = '<!-- wp:epfl/memento (.*?) /-->'
        matching_reg = re.compile("{}".format(regex))
        json_attributes = matching_reg.findall(html_block)
        attributes = json.loads(json_attributes[0])
        category_id = str(attributes['categories'])
        category_label = self.get_memento_category_label(int(category_id))
        attributes['categories'] = '[{"label":"' + category_label + '","value":' + category_id + "}]"
        return '<!-- wp:epfl/memento {' + json.dumps(attributes)[1:-1] + '} /-->'

    def run(self, tmp=None, task_vars=None):

        self.result = super(ActionModule, self).run(tmp, task_vars)

        # Handling --check execution mode
        if task_vars['ansible_check_mode']:
            self.result['skipped'] = True
            return self.result

        pages_id = json.loads(self._query_wp_cli("post list --post_type=page --field=ID --format=json")["stdout"])
        for page_id in pages_id:
            page_content = self._query_wp_cli("post get {} --field=content".format(page_id))['stdout']

            if len(page_content) > 0:
                html_blocks = self.find_blocks(page_content)

                new_page_content = page_content
                page_change = False
                for html_block in html_blocks:
                    if "category" in html_block:
                        # Backup memento block
                        before_html_block = html_block
                        # Convert attribut category to categorie of this memento block
                        after_html_block = self.convert_category_to_categories(html_block)
                        new_page_content = new_page_content.replace(before_html_block, after_html_block)
                        page_change = True

                if page_change:
                    try:
                      # Update page with new content
                      cmd = "post update {} --post_content='{}'".format(page_id, new_page_content)
                      self._run_wp_cli_change(cmd)
                    except:
                      site = self._get_ansible_var("wp_hostname") + "/" + self._get_ansible_var("wp_path")
                      print("WP_UPDATE_MEMENTO_BLOCK page_id: {} site: {}".format(page_id, site))

        return self.result
