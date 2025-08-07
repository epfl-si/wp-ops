import requests

class Sitemap:

    @classmethod
    def create(cls):
        response = requests.get("https://menu-api:3001/sitemap")
        print(response.content)
