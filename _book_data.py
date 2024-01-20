from modules.book_data import BookData
from modules.database import Database
import logging
from time import sleep


# 共通のロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# book_data_functionのロギング設定
book_data_logger = logging.getLogger("book_data")
book_data_handler = logging.FileHandler(
    "/var/www/public_html/book-suggest.com/log/book_data.log"
)
book_data_logger.addHandler(book_data_handler)


def get_book_data(book_id):
    book_data = BookData(book_id)
    book_data.get_data()
    return


def book_data_function():
    """
    Get information of books from Booklog.
    """
    book_data_logger.info("start...")

    db = Database()

    book_ids = db.get_book_ids_without_authors()
    books_len = len(list(book_ids))
    book_data_logger.info(f"total books: {books_len}")

    for i, book_id in enumerate(db.get_book_ids_without_authors()):
        if i % 100 == 0:
            sleep(10)

        book_id = book_id["_id"]
        book_data_logger.info(f"{i+1}/{books_len} : {book_id}")
        get_book_data(book_id)


if __name__ == "__main__":
    book_data_function()
