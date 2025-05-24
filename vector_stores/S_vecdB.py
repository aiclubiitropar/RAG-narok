import chromadb
from chromadb.config import Settings
from L_vecdB import LongTermDatabase

class ShortTermDatabase:
    def __init__(self, max_indexes=100, persist_directory="shortterm_db", longterm_persist_directory="longterm_db"):
        """
        Initialize the short-term database using ChromaDB.
        :param max_indexes: Maximum number of indexes before transferring to long-term.
        :param persist_directory: Directory to store the persistent database.
        :param longterm_persist_directory: Directory for the long-term database.
        """
        self.max_indexes = max_indexes
        self.persist_directory = persist_directory
        self.longterm_persist_directory = longterm_persist_directory
        self.client = chromadb.Client(Settings(persist_directory=self.persist_directory, chroma_db_impl="duckdb+parquet"))
        self.collection = self.client.get_or_create_collection(name="shortterm")

    def add_data(self, data):
        """
        Add data to the short-term database.
        :param data: Data to be added.
        """
        self.collection.add(**data)
        if len(self.collection.get()) >= self.max_indexes:
            self.transfer_to_longterm()

    def query_data(self, query):
        """
        Query data from the short-term database.
        :param query: Query parameters.
        :return: Query results.
        """
        return self.collection.query(**query)

    def transfer_to_longterm(self):
        """Transfer data from short-term to long-term database."""
        longterm_db = LongTermDatabase(persist_directory=self.longterm_persist_directory)
        data = self.collection.get()
        longterm_db.add_data(data)
        longterm_db.save()
        self.collection.clear()

    def save(self):
        """Save the short-term database to persistent storage."""
        self.client.persist()