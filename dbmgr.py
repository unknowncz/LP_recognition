import csv
import logging

class DatabaseHandler:
    """Helper class to work with data.
    """
    def __init__(self, path:str, logger=logging.getLogger(__name__)):
        """Initialize the class and load the data.

        Args:
            path (str): Path to the .csv data source.
            logger (logging.Logger, optional): logger. Defaults to logging.getLogger(__name__).
        """
        self.logger = logger
        self.path = path
        with open(path, "r", encoding='UTF-8') as f:
            reader = csv.reader(f)
            self.database = {}
            for row in reader:
                try:
                    self.database |= {row[0].strip().upper():row[1].strip()}
                except IndexError:
                    if len(row) == 0:
                        continue
                    logger.warning(f"Database entry {repr(row[0])} has an empty value")
                    self.database |= {row[0].strip().upper():''}
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
