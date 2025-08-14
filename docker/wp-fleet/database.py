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
            print(db_password)
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
            path VARCHAR(255) NOT NULL,
            hostname varchar(255) NOT NULL,
            mariadb varchar(100) NOT NULL,
            database varchar(255) NOT NULL,
            s3_bucket varchar(255) NOT NULL,
            s3_secret varchar(255) NOT NULL,
            wp_cr varchar(255) NOT NULL,
            wp_cr_restore varchar(255) NOT NULL
            )''')
        except mariadb.Error as e:
            print(f"Error: {e}")

    @classmethod
    def upsert(cls):
        pass

    @classmethod
    def commit_and_close(cls):
        cls.conn.commit()
        cls.conn.close()
