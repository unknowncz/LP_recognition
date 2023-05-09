import csv
import logging


class DatabaseHandler:
    def __init__(self, path, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.path = path
        with open(path, "r") as f:
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
        with open(self.path, "w") as f:
            writer = csv.writer(f)
            for k, v in self.database.items():
                writer.writerow([k, v])

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