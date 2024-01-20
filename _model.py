# ssh -L 27018:localhost:27017 -i C:\Users\floor\.ssh\sakuraVPS floor@219.94.245.100

from modules.book2vec import Model
from modules.database import Database
import logging


# 共通のロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# model_functionのロギング設定
model_logger = logging.getLogger("model")
model_handler = logging.FileHandler("D:/programming/book_suggest/log/model.log")
model_logger.addHandler(model_handler)
model_handler.setLevel(logging.INFO)
model_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)


def model_function():
    model = Model()
    db = Database()

    # データベースから各テーブルの総数を取得
    num_users = db.count_all_users()
    num_books = db.count_all_books()
    num_user_books = db.count_all_user_books()
    model_logger.info(
        f"Loaded {num_users} users, {num_books} books, {num_user_books} user_books from the database."
    )

    model_logger.info("Optimizing the model...")
    # model.optimize(n_trials=100)
    # model.update_parameters()

    model_logger.info("Training the model...")
    model.train_model(update=False)
    model_logger.info("Model training completed.")


if __name__ == "__main__":
    model_function()
