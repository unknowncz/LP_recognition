import csv
from multiprocessing import get_logger
import mysql.connector


class DatabaseHandler:
    """Helper class to work with data.
    """
    def __init__(self, path:str, logger=get_logger(), overridedb:dict=None):
        """Initialize the class and load the data.

        Args:
            path (str): Path to the .csv data source.
            logger (logging.Logger, optional): logger. Defaults to logging.getLogger(__name__).
        """
        self.logger = logger
        self.path = path
        with open(path, "r", encoding='UTF-8') as f:
            reader = csv.reader(f)
            self.database = overridedb or {}
            for row in reader:
                try:
                    self.database.update({row[0].strip().upper():row[1].strip()})
                except IndexError:
                    if len(row) == 0:
                        continue
                    logger.warning(f"Database entry {repr(row[0])} has an empty value")
                    self.database.update({row[0].strip().upper():''})
        self.logger.info(f"Database loaded from {path}")

    def save(self):
        """Write the data to the .csv file.
        """
        with open(self.path, "w", encoding='UTF-8') as f:
            writer = csv.writer(f)
            for k, v in self.database.items():
                writer.writerow([str(k), str(v)])

    def __contains__(self, item:str):
        return self.database.get(item, None) is not None

    def __getitem__(self, item:str):
        return self.database.get(item, None)

    def __setitem__(self, key:str, value):
        self.database[key] = value

    def __iter__(self):
        return iter(self.database.items())

    def __len__(self):
        return len(self.database.items())

class SQLDatabaseHandler:
    def __init__(self, dblogin:dict=None, logger=get_logger()):
        self.logger = logger
        self.dblogin = dblogin
        self.conn = mysql.connector.connect(**dblogin)
        self.logger.info(f"Connected to MySQL database {dblogin['host']} {dblogin['database']} as {dblogin['user']}")

    def check_user(self, username:str, password:str):
        return self._exec_one("SELECT * FROM users WHERE username=%s AND password=%s", [username, password]) is not None
        #cursor.execute(f"SELECT * FROM users WHERE username=%s AND password=%s", (username, password))

    def get_user(self, username:str):
        return self._exec_one("SELECT * FROM users WHERE username=%s", [username,])
        #cursor.execute(f"SELECT * FROM users WHERE username=%s", (username,))

    def set_user(self, username:str, password:str):
        self._exec_none(f"INSERT INTO users (username, password) VALUES (%s, %s)", [username, password])
        #cursor.execute(f"INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))

    def check_licence_plate(self, licence_plate:str):
        return self._exec_one("SELECT * FROM lp WHERE licence_plate=%s", [licence_plate,]) is not None
        #cursor.execute(f"SELECT * FROM lp WHERE licence_plate=%s", (licence_plate,))

    def get_license_plate(self, licence_plate:str):
        return self._exec_one("SELECT * FROM lp WHERE licence_plate=%s", [licence_plate,])
        #cursor.execute(f"SELECT * FROM lp WHERE licence_plate=%s", (licence_plate,))

    def get_all_license_plates(self):
        return self._exec_all("SELECT licence_plate FROM lp")
        #cursor.execute("SELECT licence_plate FROM lp")

    def add_licence_plate(self, licence_plate:str, name:str='', surname:str=''):
        self._exec_none(f"INSERT INTO lp (licence_plate, name, surname) VALUES (%s, %s, %s)", [licence_plate, name, surname])
        #cursor.execute(f"INSERT INTO lp (licence_plate, name, surname) VALUES (%s, %s, %s)", (licence_plate, name, surname))

    def remove_licence_plate(self, licence_plate:str):
        self._exec_none(f"DELETE FROM lp WHERE licence_plate=%s", [licence_plate,])
        #cursor.execute(f"DELETE FROM lp WHERE licence_plate=%s", (licence_plate,))

    def edit_licence_plate(self, licence_plate:str, name:str='', surname:str=''):
        self._exec_none(f"UPDATE lp SET name=%s, surname=%s WHERE licence_plate=%s", [name, surname, licence_plate])
        #f"UPDATE lp SET name=%s, surname=%s WHERE licence_plate=%s", (name, surname, licence_plate))

    def __del__(self):
        self.conn.close()
        self.logger.info("Disconnected from MySQL database")

    def _exec_none(self, query:str, args):
        cursor = self.conn.cursor()
        cursor.execute(query, args)
        self.conn.commit()
        cursor.close()

    def _exec_one(self, query:str, args):
        cursor = self.conn.cursor()
        cursor.execute(query, args)
        res = cursor.fetchone()
        cursor.close()
        return res
    
    def _exec_all(self, query:str, args):
        cursor = self.conn.cursor()
        cursor.execute(query, args)
        res = cursor.fetchall()
        cursor.close()
        return res
