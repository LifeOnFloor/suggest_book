from pymongo import MongoClient
from sshtunnel import SSHTunnelForwarder
from pymongo.errors import DuplicateKeyError


class Database:
    """
    Database class for MongoDB
    """

    def __init__(
        self,
        ssh_host="####",
        ssh_username="####",
        ssh_pkey_path="####",
        ssh_private_key_password="####",
        mongo_host="####",
        mongo_port=27017,
        db_username="####",
        db_password="####",
        authSource="####",
    ):
        self.server = SSHTunnelForwarder(
            ssh_host,
            ssh_username=ssh_username,
            ssh_pkey=ssh_pkey_path,
            ssh_private_key_password=ssh_private_key_password,
            remote_bind_address=(mongo_host, mongo_port),
        )
        self.server.start()

        self.client = MongoClient(
            host="127.0.0.1",
            port=self.server.local_bind_port,  # 使用するポートはSSHトンネルのローカルポート
            username=db_username,
            password=db_password,
            authSource=authSource,
        )

        self.db = self.client["booklog"]
        self.users = self.db["users"]
        self.books = self.db["books"]
        self.user_books = self.db["user_books"]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def insert_user(self, user_id):
        try:
            self.users.insert_one({"_id": user_id})
        except DuplicateKeyError as e:
            print(f"DuplicateKeyError: {e}")

    def insert_book(self, book_id, title, authors=None):
        try:
            data = {"_id": book_id, "title": title}
            if authors:
                data["authors"] = authors
            self.books.insert_one(data)
        except DuplicateKeyError as e:
            print(f"DuplicateKeyError: {e}")

    def insert_user_books(self, user_id, book_id):
        try:
            self.user_books.insert_one({"user_id": user_id, "book_id": book_id})
        except DuplicateKeyError as e:
            print(f"DuplicateKeyError: {e}")

    def search_books_from_title(self, keyword: str):
        return list(self.books.find({"title": {"$regex": keyword, "$options": "i"}}))

    def search_book_id_from_author(self, keyword: str):
        return [
            x["_id"]
            for x in self.books.find({"authors": {"$regex": keyword, "$options": "i"}})
        ]

    def search_books_by_title_and_authors(self, keywords: str):
        """
        Search books by title and authors using the provided keywords.
        Keywords can be space-separated and will be split to search individually.

        :param keywords: Space-separated string of keywords to search for.
        :return: List of book_ids that match the search, sorted by their counts in user_books.
        """
        search_queries = self._generate_search_queries(keywords)

        pipeline = self._construct_pipeline(search_queries)

        # Execute the pipeline and extract book_ids
        sorted_books = list(self.books.aggregate(pipeline))
        return [book["_id"] for book in sorted_books]

    def _generate_search_queries(self, keywords: str):
        """
        Generates a list of search queries for titles and authors based on provided keywords.

        :param keywords: Space-separated string of keywords.
        :return: List of search queries for MongoDB.
        """
        keyword_list = keywords.split()
        return [
            {
                "$or": [
                    {"title": {"$regex": keyword, "$options": "i"}},
                    {"authors": {"$regex": keyword, "$options": "i"}},
                ]
            }
            for keyword in keyword_list
        ]

    def _construct_pipeline(self, search_queries: list):
        """
        Constructs the MongoDB aggregation pipeline based on search queries.

        :param search_queries: List of search queries.
        :return: MongoDB aggregation pipeline.
        """
        return [
            {"$match": {"$or": search_queries}},
            {
                "$lookup": {
                    "from": "user_books",
                    "localField": "_id",
                    "foreignField": "book_id",
                    "as": "entries",
                }
            },
            # {"$addFields": {"count": {"$size": "$entries"}}},
            # {"$sort": {"count": -1}},
            # {"$project": {"_id": 1}},
            {"$limit": 4},
        ]

    def get_user_books(self, user_id):
        return list(self.user_books.find({"user_id": user_id}))

    def get_all_user_books(self):
        return list(self.user_books.find({}))

    def get_book(self, book_id):
        return self.books.find_one({"_id": book_id})

    def get_user(self, user_id):
        return self.users.find_one({"_id": user_id})

    def get_book_title(self, book_id: str):
        book = self.get_book(book_id)
        return book["title"] if book else None

    def get_book_id(self, title: str):
        book = self.books.find_one({"title": title})
        return book["_id"] if book else None

    def get_book_ids_without_authors(self):
        # booksテーブルのすべての_idとタイトルを取得。ただし、authorsがあるものは除く
        book_ids = self.books.find(
            {"authors": {"$exists": False}},
            {
                "_id": 1,
            },
        )
        return book_ids

    def count_all_books(self):
        return self.books.count_documents({})

    def count_all_users(self):
        return self.users.count_documents({})

    def count_all_user_books(self):
        return self.user_books.count_documents({})

    def count_books_not_having_count(self):
        return self.books.count_documents({"count": {"$exists": False}})

    def is_book_exists(self, book_id):
        return bool(self.get_book(book_id))

    def is_user_exists(self, user_id):
        return bool(self.get_user(user_id))

    def update_book(self, book_id, **kwargs):
        update_fields = {k: v for k, v in kwargs.items() if v is not None}
        if update_fields:
            self.books.update_one({"_id": book_id}, {"$set": update_fields})

    def delete_book(self, book_id):
        self.books.delete_one({"_id": book_id})

    def close(self):
        self.client.close()
        self.server.stop()
