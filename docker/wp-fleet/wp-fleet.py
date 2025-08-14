from wordpresssites import WordpressSite
from database import MariaDB

if __name__ == '__main__':

    MariaDB.create_table()

    for wordpresssite in WordpressSite.all():
        print(wordpresssite.moniker, wordpresssite.database_name, wordpresssite.mariadb_name)
        MariaDB.upsert()

    MariaDB.commit_and_close()

