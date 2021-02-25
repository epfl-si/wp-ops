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
      rest_api_url = "https://memento.epfl.ch/api/v1/categories/?format=json"
      response = requests.get(rest_api_url)
      return response.json()

    def get_memento_category_label(self, memento_category_id):
      for category in self._get_memento_categories()['results']:
        if category['id'] == memento_category_id:
          return category['en_label']
        

    def find_block(self, content, block_name='wp:epfl/memento'):
      regex = '(<!-- {} .*? /-->)'.format(block_name)
      matching_reg = re.compile("{}".format(regex))

      raise ValueError( matching_reg.findall(content) )
      return matching_reg.findall(content)

    def convert_category_to_categories(self, html_content):
        
        html_content = html_content.replace("category", "categories", 1)
        #print(html_content)
        
        regex = '<!-- wp:epfl/memento (.*?) /-->'
        matching_reg = re.compile("{}".format(regex))
        json_attributes = matching_reg.findall(html_content)
        attributes = json.loads(json_attributes[0])
        
        category_id = attributes['categories'] 
        category_label = self.get_memento_category_label(int(category_id))
        
        attributes['categories'] = "[{\u0022label\u0022:\u0022" + category_label + "\u0022,\u0022id\u0022:" + category_id + "}]"
        
        return '<!-- wp:epfl/memento {' + json.dumps(attributes)[1:-1] + '} /-->'

    def run(self, tmp=None, task_vars=None):

        self.result = super(ActionModule, self).run(tmp, task_vars)

        # Handling --check execution mode
        if task_vars['ansible_check_mode']:
            self.result['skipped'] = True
            return self.result

        # Obtenir la liste des pages d'un site
        # wp post list --post_type=page --field=ID
        pages = self._query_wp_cli("post list --post_type=page --field=ID")

        for page_id in pages['stdout_lines']:
          
          # Obtenir le contenu d'une page
          # wp post get 32 --field=content
          page_content = self._query_wp_cli("post get {} --field=content".format(page_id))['stdout_lines'][0]
          html_blocks = self.find_block(page_content)

          raise ValueError( html_blocks )
          for html_block in html_blocks:
              before_html_block = html_block
              after_html_block = self.convert_category_to_categories(html_block)
              new_page_content = page_content.replace(before_html_block, after_html_block)
              raise ValueError(new_page_content)
              #self._run_wp_cli_change("post update 123 --post_content={}".format(new_page_content))

        return self.result
