from modules.scraping import Scraping
from modules.database import Database
import logging
from winsound import Beep


# 共通のロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# scraper_functionのロギング設定
scraper_logger = logging.getLogger("scraper")
scraper_handler = logging.FileHandler("D:/programming/book_suggest/log/user.log")
scraper_logger.addHandler(scraper_handler)
scraper_handler.setLevel(logging.INFO)
scraper_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)


def insert(scraper, db, user_id):
    db.insert_user(user_id)
    books = scraper.load_books(user_id)
    for book in books:
        book_id = book["BOOK_ID"]
        title = book["TITLE"]
        db.insert_book(book_id, title)
        db.insert_user_books(user_id, book_id)


def scraper_function():
    scraper = Scraping()
    db = Database()

    # 本の人気ランキングからユーザーIDを取得
    start_year = 2015
    end_year = 2014  # 2009

    _start_year = start_year
    _start_book_num = 0
    _start_user_num = 0

    for year in range(start_year, end_year, -1):
        scraper_logger.info(f"Processing year: {year}")
        try:
            book_urls = scraper.get_book_urls_from_ranking(year)
        except Exception as e:
            scraper_logger.error(e)
            raise e
        for num, book_url in enumerate(book_urls, 1):
            if year == _start_year and num < _start_book_num:
                continue
            try:
                user_id_list = scraper.get_users_from_book_url(book_url)
            except Exception as e:
                scraper_logger.error(e)
                raise e

            # ユーザーの書籍リストをデータベースに保存
            for u_num, user_id in enumerate(user_id_list, 1):
                if (
                    year == _start_year
                    and num == _start_book_num
                    and u_num < _start_user_num
                ):
                    continue
                scraper_logger.info(
                    f"Year: {year}, Book: {num}/{len(book_urls)}, User: {u_num}/{len(user_id_list)}, UserID: {user_id}"
                )

                # ユーザーが既にデータベースに存在する場合はスキップ
                # ただし、スクレイピングを再開してから最初のユーザーの場合はスキップしない
                if db.is_user_exists(user_id) and not (
                    year == _start_year
                    and num == _start_book_num
                    and u_num == _start_user_num
                ):
                    scraper_logger.error(
                        f"User [{user_id}] already exists in the database"
                    )
                    continue
                try:
                    insert(scraper, db, user_id)
                except TimeoutError:
                    scraper_logger.error("TimeoutError")
                    raise TimeoutError


def count_users():
    db = Database()
    c = db.count_all_users()
    scraper_logger.info(f"Current number of users: {c}")


if __name__ == "__main__":
    try:
        count_users()
        scraper_function()
    except Exception as e:
        scraper_logger.error(e)
        Beep(400, 1000)
