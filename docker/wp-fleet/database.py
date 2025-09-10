import json
import os
import mariadb


class classproperty:
    def __init__(self, func):
        self.fget = func
    def __get__(self, instance, owner):
        return self.fget(owner)


class MariaDB:
    __singleton = None

    @classmethod
    def __get(cls):
        if cls.__singleton is None:
            cls.__singleton = cls()

        return cls.__singleton

    def __init__(self):
        self._conn = self.connection()
        if self._conn:
            self._cursor = self._conn.cursor()

    @classproperty
    def cursor(cls):
        return cls.__get()._cursor

    @classproperty
    def conn(cls):
        return cls.__get()._conn

    def connection(self):
        try:
            db_password = os.getenv("MARIADB_PASSWORD")
            db_host = os.getenv("MARIADB_HOST")
            return mariadb.connect(
                user="wp-fleet",
                password=db_password,
                host=db_host,
                port=3306,
                database="wp-fleet"
            )
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            return None

    @classmethod
    def create_table(cls):
        try:
            cls.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS sites_index (
            uid varchar(64) PRIMARY KEY,
            name varchar(255) NOT NULL,
            path VARCHAR(255) NOT NULL,
            hostname varchar(255) NOT NULL,
            mariadb varchar(100) NOT NULL,
            database varchar(255) NOT NULL,
            wp_cr JSON NOT NULL,
            wp_cr_restore JSON NOT NULL
            )''')
        except mariadb.Error as e:
            print(f"Error: {e}")

    @classmethod
    def upsert(cls, wordpresssite, database, backup):
        wp = {'apiVersion': wordpresssite['apiVersion'], 'kind': "WordpressSite"}
        wp['metadata'] = {'name': wordpresssite['metadata']['name'], 'namespace': wordpresssite['metadata']['namespace']}
        wp['metadata']['labels'] = {}
        wp['metadata']['labels']['app.kubernetes.io/managed-by'] = 'wp-veritas'
        wp['spec'] = wordpresssite['spec']
        try:
            wp = replace_in_dict(wp, '"', '\\"')
            wp = replace_in_dict(wp, "'", "''")
            wp_cr = json.dumps(wp, indent=2, ensure_ascii=False)

            restore = wp
            restore['restore'] = {}
            restore['restore']['s3'] = {}
            restore['restore']['s3']['bucket'] = backup['spec']['storage']['s3']['bucket']
            restore['restore']['s3']['endpoint'] = backup['spec']['storage']['s3']['endpoint']
            restore['restore']['s3']['secretKeyName'] = backup['spec']['storage']['s3']['accessKeyIdSecretKeyRef']['name']
            restore['restore']['s3']['wordpresssiteSource'] = wordpresssite['metadata']['name']
            restore_cr = json.dumps(restore, indent=2, ensure_ascii=False)
            # TODO the JSON must be correctly formatted by the library
            # TODO update the restore tags with the new of the CRD
            cls.cursor.execute(f'''
           INSERT INTO sites_index (uid,name,hostname,path,mariadb,database,wp_cr,wp_cr_restore) 
           values (
           '{wordpresssite["metadata"]["uid"]}',
           '{wordpresssite["metadata"]["name"]}',
           '{wordpresssite["spec"]["hostname"]}',
           '{wordpresssite["spec"]["path"]}',
           '{database["spec"]["mariaDbRef"]["name"]}',
           '{database["metadata"]["name"]}',
           '{wp_cr}',
           '{restore_cr}'
           )
           ON DUPLICATE KEY UPDATE
           name = values(name),
           hostname = values(hostname),
           path = values(path),
           mariadb = values(mariadb),
           database = values(database),
           wp_cr = values(wp_cr),
           wp_cr_restore = values(wp_cr_restore)
           ''')
        except mariadb.Error as e:
            print(wp)
            print(f"Error: {e}")

    @classmethod
    def commit_and_close(cls):
        cls.conn.commit()
        cls.conn.close()


def replace_in_dict(obj, old, new):
    if isinstance(obj, dict):
        return {k: replace_in_dict(v, old, new) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_in_dict(item, old, new) for item in obj]
    elif isinstance(obj, str):
        return obj.replace(old, new)
    else:
        return obj
