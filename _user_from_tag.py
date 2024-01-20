from modules.scraping import Scraping
from modules.database import Database
import logging


# 共通のロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# user_functionのロギング設定
user_logger = logging.getLogger("user")
user_handler = logging.FileHandler("D:/programming/book_suggest/log/user.log")
user_logger.addHandler(user_handler)
user_handler.setLevel(logging.INFO)
user_handler.setFormatter(
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


def user_function():
    user_logger.info("Start scraping users from profile tags.")

    scraper = Scraping()
    db = Database()

    # 本の人気ランキングからユーザーIDを取得
    # https://booklog.jp/profiletags の人気のプロフィールタグを取得
    tags = scraper.get_popular_profile_tags()

    cnt = count_users(db)

    exclude_tag_list = []
    exclude_user_cnt = 0

    for tnum, tag in enumerate(tags, 1):
        if tag in exclude_tag_list:
            cnt += 1000
            continue

        user_logger.info(f"Processing tag: {tag}")
        users = scraper.get_users_from_profile_tag(tag, 100)

        # ユーザーの書籍リストをデータベースに保存
        for num, user in enumerate(users, 1):
            cnt += 1
            if cnt < exclude_user_cnt:
                continue

            user_logger.info(
                f"{tag} : {tnum} / {len(tags)} - {user} : {num} / {len(users)} - {cnt} / {len(tags) * len(users)}"
            )
            if db.is_user_exists(user):
                user_logger.error(f"User [{user}] already exists in the database")
                continue
            try:
                insert(scraper, db, user)
            except TimeoutError:
                user_logger.error(f"TimeoutError: {user}")
                return


def count_users(db):
    c = db.count_all_users()
    user_logger.info(f"Current number of users: {c}")
    return c


if __name__ == "__main__":
    user_function()
