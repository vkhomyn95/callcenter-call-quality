import logging
import sys
import pymysql
import pymysql.cursors

from celery_worker.variables import variables


class Database:
    """
        Singleton class of the logger system that will handle the logging system.
    ...

    Attributes
    ----------
    _database_instance: Database
        Represents the current running instance of VoicemailRecognitionDatabase,
        this will only be created once (by default set to None).

    """

    _database_instance = None

    @staticmethod
    def instance():
        """
            Obtains instance of VoicemailRecognitionDatabase.
        """

        return Database._database_instance

    def __init__(self) -> None:
        """
            Default constructor.
        """

        if Database._database_instance is None:
            try:
                conn = pymysql.connect(
                    user=variables.mariadb_database_user,
                    password=variables.mariadb_database_password,
                    host=variables.mariadb_database_host,
                    port=variables.mariadb_database_port,
                    database=variables.mariadb_database_name,
                    autocommit=True,
                    cursorclass=pymysql.cursors.DictCursor
                )
                Database._database_instance = self
            except pymysql.MySQLError as e:
                logging.error(f'  >> Error connecting to MySQL/MariaDB Platform: {e}')
                sys.exit(1)
            self.conn = conn
            self.cur = conn.cursor()

        else:
            raise Exception(f"{__file__}: Cannot construct, an instance is already running.")

    def load_user_postback_info_by_id(self, user_id: str):
        try:
            self.cur.execute(
                'SELECT u.id as user_id, u.audience as origin, u.api_key as api_key, t.id as tariff_id, '
                't.active as active, t.total as total from user u '
                'LEFT JOIN tariff t on t.user_id=u.id '
                'WHERE u.id=%s',  # PyMySQL uses %s for placeholders
                (user_id,)
            )
            return self.cur.fetchone()
        except pymysql.MySQLError as e:
            logging.error(f'  >> Error querying MySQL/MariaDB: {e}')
            self.conn.ping(reconnect=True)  # PyMySQL uses ping() to reconnect
            return self.load_user_postback_info_by_id(user_id)


# Instantiate the Database singleton
pymysql_db = Database()
