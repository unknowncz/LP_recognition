import csv
import logging


class DatabaseHandler:
    def __init__(self, path, logger=logging.getLogger(__name__)):
        self.logger = logger
        with open(path, "r") as f:
            reader = csv.reader(f)
            self.database = {}
            for row in reader:
                try:
                    self.database |= {row[0]:row[1]}
                except IndexError:
                    if len(row) == 0:
                        continue
                    logger.warning(f"Database entry {repr(row[0])} is invalid")
                    self.database |= {row[0]:''}
        self.logger.info(f"Database loaded from {path}")

    def __contains__(self, item):
        return self.database.get(item, None) is not None

    def __getitem__(self, item):
        return self.database.get(item, None)

    def __setitem__(self, key, value):
        self.database[key] = value

    def __iter__(self):
        return iter(self.database.items())
    
    def __len__(self):
        return len(self.database.items())