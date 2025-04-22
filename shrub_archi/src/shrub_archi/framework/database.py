
from sqlite3 import Connection as SQLiteConnection
from sqlite3 import connect as sqlite_connect



class Cursor:
    def __init__(self, cursor):
        self.cursor = cursor

    def get_meta_data(self):
        return self.cursor.description

    def execute(self, query: str):
        return self.cursor.execute(query)


class Connection:
    def __init__(self, connection):
        self.connection = connection
    def execute(self, query) -> Cursor:
        ...

    def cursor(self) -> Cursor:
        return Cursor(self.connection.cursor())


    def close(self):
        return self.connection.close()

    def get_meta_data(self):
        # Connect to your database
        conn = Connection(sqlite_connect('your_database.db'))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS your_table (
                ID NUMBER,
                NAME TEXT,
                DESCRIPTION TEXT
            )
        """)
        cursor = conn.cursor()

        # Execute a query
        cursor.execute("SELECT * FROM your_table LIMIT 1")

        meta_data = cursor.get_meta_data()

        # Extract the column names
        column_names = [description[1] for description in meta_data]

        print(column_names)

        # Close the connection
        conn.close()



if __name__ == "__main__":
    Connection(None).get_meta_data()