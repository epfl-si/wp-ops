from wordpresssites import WordpressSite
from database import MariaDB

if __name__ == '__main__':

    MariaDB.create_table()

    for wordpresssite in WordpressSite.all():
        MariaDB.upsert(wordpresssite.wp, wordpresssite.database, wordpresssite.backup)

    MariaDB.commit_and_close()

