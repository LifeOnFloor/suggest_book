from mysql.connector import connect, Error


class Database:
    """
    Database class for MySQL
    """

    columns = [
        "book_id",
        "title",
        "published_date",
        "authors",
        "page",
        "print_type",
        "description",
        "identifier",
    ]

    def __init__(self):
        self.conn = self.create_connection()
        self.cursor = self.conn.cursor(buffered=True)

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def create_connection(self):
        conn = connect(
            host="localhost", user="root", password="####", database="booklog"
        )
        return conn

    def include_tables(self, table_name_list: list) -> bool:
        """Returns True if all the tables in the list exist in the database"""
        self.cursor.execute("SHOW TABLES")
        existing_tables = [table[0] for table in self.cursor.fetchall()]
        return all(table in existing_tables for table in table_name_list)

    def delete_tables(self):
        """Deletes all the tables in the database"""
        # Drop tables that have foreign key constraints first
        self.cursor.execute("DROP TABLE IF EXISTS user_books")
        # Drop the main tables
        self.cursor.execute("DROP TABLE IF EXISTS books")
        self.cursor.execute("DROP TABLE IF EXISTS users")
        self.conn.commit()

    def create_tables(self):
        """Creates the tables if they do not exist"""
        # If the tables already exist, return
        if self.include_tables(["users", "books", "users_books"]):
            return

        # Users table
        self.cursor.execute(
            """
            CREATE TABLE users (
                id VARCHAR(255) PRIMARY KEY
            );
        """
        )

        # Books table
        self.cursor.execute(
            """
            CREATE TABLE books (
                id VARCHAR(99) PRIMARY KEY,
                title TEXT NOT NULL,
                published_date DATE,
                authors TEXT,
                page INT,
                print_type VARCHAR(99),
                description TEXT,
                identifier VARCHAR(255)
            );
        """
        )

        # User-Books relation table
        self.cursor.execute(
            """
            CREATE TABLE user_books (
                user_id VARCHAR(255),
                book_id VARCHAR(13),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
                PRIMARY KEY (user_id, book_id)
            );
        """
        )
        self.conn.commit()

    def insert(self, query, values):
        """Inserts a row into the database and commits the changes
        If the row already exists, it will not be inserted
        """
        try:
            self.cursor.execute(query, values)
            self.conn.commit()
        except Error as e:
            if e.errno != 1062:  # Duplicate entry
                print(f"Error: {e}")

    def insert_user(self, user_id):
        query = "INSERT INTO users (id) VALUES (%s)"
        values = (user_id,)
        self.insert(query, values)

    def insert_book(self, book_id, title):
        query = "INSERT INTO books (id, title) VALUES (%s, %s)"
        values = (book_id, title)
        self.insert(query, values)

    def insert_user_book(self, user_id, book_id):
        query = "INSERT INTO user_books (user_id, book_id) VALUES (%s, %s)"
        values = (user_id, book_id)
        self.insert(query, values)

    def search_book_from_title(self, keyword: str):
        """if title includes keyword, return a book_id"""
        self.cursor.execute(
            "SELECT id, title FROM books WHERE title LIKE %s",
            ("%" + keyword + "%",),
        )
        rows = self.cursor.fetchall()
        if not rows:
            return None
        return rows[0]

    def search_books_from_title(self, keyword: str):
        """if title includes keyword, return a book_id"""
        self.cursor.execute(
            """
            SELECT id, title, COUNT(user_books.book_id)
            FROM books
            INNER JOIN user_books ON books.id = user_books.book_id
            WHERE title LIKE %s
            GROUP BY id
            ORDER BY CHAR_LENGTH(title) ASC, COUNT(user_books.book_id) DESC
            LIMIT 5
            """,
            ("%" + keyword + "%",),
        )
        rows = self.cursor.fetchall()
        if not rows:
            return None
        return rows

    def search_book_id_from_author(self, keyword: str) -> list:
        """if title includes keyword, return book_id"""
        self.cursor.execute(
            "SELECT id FROM books WHERE authors LIKE %s", ("%" + keyword + "%",)
        )
        return self.cursor.fetchall()

    def get_user_books_row(self, user_id):
        self.cursor.execute(
            "SELECT * FROM books INNER JOIN user_books ON books.id = user_books.book_id WHERE user_books.user_id = %s LIMIT 1",
            (user_id,),
        )
        return self.cursor.fetchall()

    def get_book_row(self, book_id):
        self.cursor.execute("SELECT * FROM books WHERE id = %s LIMIT 1", (book_id,))
        rows = self.cursor.fetchall()
        if not rows:
            return None
        return rows[0]

    def get_book_title(self, book_id: str):
        self.cursor.execute(
            """
            SELECT title, COUNT(user_books.book_id)
            FROM books
            INNER JOIN user_books ON books.id = user_books.book_id
            WHERE id = %s
            GROUP BY id
            ORDER BY COUNT(user_books.book_id) DESC
            LIMIT 1
            """,
            (book_id,),
        )
        rows = self.cursor.fetchall()
        if not rows:
            return None
        return rows[0][0]

    def get_book_id(self, title: str):
        try:
            self.cursor.execute(
                """
                SELECT id, COUNT(user_books.book_id)
                FROM books
                INNER JOIN user_books ON books.id = user_books.book_id
                WHERE title LIKE %s
                GROUP BY id
                ORDER BY COUNT(user_books.book_id) DESC
                LIMIT 1
                """,
                ("%" + title + "%",),
            )
            rows = self.cursor.fetchall()
            if not rows:
                return None
            return rows[0][0]
        except Error as e:
            print(f"Error: {e}")
            return None

    def get_book_rows(self, book_id_list):
        self.cursor.execute("SELECT * FROM books WHERE id IN %s", (book_id_list,))
        return self.cursor.fetchall()

    def get_all_users_books(self):
        self.cursor.execute(
            "SELECT user_books.user_id, books.id, books.title FROM books INNER JOIN user_books ON books.id = user_books.book_id"
        )
        return self.cursor.fetchall()

    def is_any_null(self, book_id):
        """
        Returns True if any of the columns are null
        """
        self.cursor.execute("SELECT * FROM books WHERE id = %s LIMIT 1", (book_id,))
        rows = self.cursor.fetchall()
        if not rows:
            return True
        return False

    def update_book_row(
        self,
        book_id,
        title,
        published_date,
        authors,
        page,
        print_type,
        description,
        identifier,
    ):
        self.cursor.execute(
            "UPDATE books SET title = %s, published_date = %s, authors = %s, page = %s, print_type = %s, description = %s, identifier = %s WHERE id = %s",
            (
                title,
                published_date,
                authors,
                page,
                print_type,
                description,
                identifier,
                book_id,
            ),
        )
        self.conn.commit()

    def delete_book(self, book_id):
        self.cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
        self.conn.commit()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
