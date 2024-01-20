import optuna
from gensim.models import Word2Vec
from modules.database import Database
import pandas as pd
import os


class Model:
    MODEL_FILE = "book2vec.model"
    MODEL_TYPE_MAPPING = {"skipgram": 1, "cbow": 0}
    APPROXIMATION_MAPPING = {"hierarchical": 1, "negative": 0}

    def __init__(self):
        self.model = None
        self.sentences = None
        self.default_params = {
            "model_type": "cbow",
            "approximation": "negative",
            "size": 208,
            "window": 29,
            "epochs": 5,
            "negative_size": 9,
            "min_count": 1,
        }

    def _load_data_from_db(self):
        db = Database()
        users_books = db.get_all_user_books()
        return pd.DataFrame(users_books, columns=["user_id", "book_id"])

    def _generate_sentences(self):
        users_books = self._load_data_from_db()
        users_books.drop_duplicates(inplace=True)
        users_books.dropna(subset=["book_id"], inplace=True)
        data = users_books.groupby("user_id").agg({"book_id": list})
        self.sentences = data["book_id"].values.tolist()

    def _get_model_params(self, params):
        sg = self.MODEL_TYPE_MAPPING[params["model_type"]]
        hs = self.APPROXIMATION_MAPPING[params["approximation"]]
        return {
            "sentences": self.sentences,
            "sg": sg,
            "hs": hs,
            "negative": params["negative_size"],
            "vector_size": params["size"],
            "window": params["window"],
            "epochs": params["epochs"],
            "compute_loss": True,
            "min_count": params["min_count"],
        }

    def train_model(self, update=False):
        """
        Train the model using all the books in the database
        """
        if not self.sentences:
            print("Generating sentences...")
            self._generate_sentences()

        # train or update the model
        if update and os.path.exists(self.MODEL_FILE):
            self.model = Word2Vec.load(self.MODEL_FILE)
            self.model.train(
                self.sentences,
                total_examples=len(self.sentences),  # type: ignore
                epochs=self.model.epochs,
            )
        else:
            print("Training the model...")
            self.model = Word2Vec(**self._get_model_params(self.default_params))
            print(f"Loss: {self.model.get_latest_training_loss()}")

        # save the model
        print("Saving the model...")
        self.model.save(self.MODEL_FILE)

    def load_model(self):
        self.model = Word2Vec.load(self.MODEL_FILE)

    def get_similar_books(self, book_id, topn: int = 10) -> pd.DataFrame:
        if not self.model:
            raise Exception("Model is not loaded or trained")

        if book_id not in self.model.wv.key_to_index:
            raise KeyError(f"Key '{book_id}' not present in vocabulary")

        similar_books = self.model.wv.most_similar(book_id, topn=topn)
        df = pd.DataFrame(similar_books, columns=["book_id", "similarity"])
        df.similarity = (df.similarity * 100).round(2)
        return df

    def objective(self, trial):
        params = {
            "size": trial.suggest_int("size", 50, 300),
            "window": trial.suggest_int("window", 5, 30),
            "epochs": trial.suggest_int("epochs", 5, 20),
            "negative_size": trial.suggest_int("negative_size", 5, 20),
            "model_type": trial.suggest_categorical("model_type", ["cbow"]),
            "approximation": trial.suggest_categorical("approximation", ["negative"]),
            "hs": trial.suggest_categorical("hs", ["negative"]),
            "sg": trial.suggest_categorical("sg", ["cbow"]),
            "min_count": 1,
        }

        model = Word2Vec(**self._get_model_params(params))
        return model.get_latest_training_loss()

    def optimize(self, n_trials=100):
        if not self.sentences:
            self._generate_sentences()

        study = optuna.create_study(direction="minimize")
        study.optimize(self.objective, n_trials=n_trials)

        print(f"Best parameters: {study.best_params}")
        print(f"Best loss: {study.best_value}")
        self.save_parameters(study.best_params)

    def save_parameters(self, params):
        with open("book2vec_ver.params", "w") as f:
            f.write(str(params))

    def update_parameters(self):
        with open("book2vec_ver.params", "r") as f:
            params = eval(f.read())
        self.default_params = params
        print(f"Parameters updated: {self.default_params}")
