import requests
import datetime

class Sitemap:

    @classmethod
    def create(cls):
        hour = datetime.datetime.now().hour
        if hour == 1:
            response = requests.get("https://menu-api:3001/generateSitemap")
