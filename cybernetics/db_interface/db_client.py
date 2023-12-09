from abc import ABC, abstractmethod


class DBClient(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def connect_db(self):
        pass

    @abstractmethod
    def close_connection(self):
        pass

    @abstractmethod
    def execute_and_fetch_results(self, sql, json=True):
        pass

    @abstractmethod
    def execute(self, sql):
        pass
