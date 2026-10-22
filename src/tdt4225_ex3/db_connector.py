import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


class DbConnector:
    """
    Connects to the MongoDB server on the Ubuntu virtual machine.
    Connector needs HOST, USER and PASSWORD to connect.

    Example:
    HOST = "tdt4225-00.idi.ntnu.no" // Your server IP address/domain name
    USER = "testuser" // This is the user you created and added privileges for
    PASSWORD = "test123" // The password you set for said user
    """

    def __init__(
        self,
        DATABASE=None,
        HOST=None,
        USER=None,
        PASSWORD=None,
        PORT=None,
    ):
        DATABASE = default_if_none(DATABASE, os.getenv("MONGO_INITDB_DATABASE"))
        HOST = default_if_none(HOST, os.getenv("MONGO_HOST", "tdt4225-01.idi.ntnu.no"))
        USER = default_if_none(USER, os.getenv("MONGO_INITDB_USER"))
        PASSWORD = default_if_none(PASSWORD, os.getenv("MONGO_INITDB_PWD"))
        PORT = default_if_none(PORT, os.getenv("MONGO_PORT", "27017"))

        uri = f"mongodb://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
        # Connect to the databases
        self.client = MongoClient(uri)
        print(self.client)
        self.db = self.client[DATABASE]

        # get database information
        print("You are connected to the database:", self.db.name)
        print("-----------------------------------------------\n")

    def close_connection(self):
        # close the cursor
        # close the DB connection
        self.client.close()
        print("\n-----------------------------------------------")
        print(f"Connection to {self.db.name}-db is closed")


def default_if_none(value, default):
    return value if value is not None else default


if __name__ == "__main__":
    db_connector = DbConnector()
    db_connector.close_connection()
