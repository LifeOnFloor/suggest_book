from flask import Flask, render_template, request, Response
from typing import Union
from modules.book2vec import Model
from modules.database import Database
from modules.book_data import BookData
from datetime import datetime


app = Flask(__name__)
model = Model()
model.load_model()


def get_book_info_from_df(dataframe):
    result_list = []
    for row in dataframe.itertuples(index=False):
        book_id = row.book_id
        book_info = BookData(str(book_id)).get_data()
        book_info["amazon_link"] = f"https://www.amazon.co.jp/dp/{row.book_id}"
        book_info["book_id"] = book_id
        result_list.append(book_info)
    return result_list


def error_handler(predicted_title, error: str, year=datetime.now().year):
    return render_template(
        "index.html",
        results=False,
        predicted_title=predicted_title,
        error=error,
        year=year,
    )


@app.route("/", methods=["GET", "POST"])
def index() -> Union[str, Response]:
    result_num = 4
    year = datetime.now().year

    try:
        if request.method == "POST":
            action_type = request.form["action_type"]
            if action_type == "search":
                search_word = request.form["search"]
                if not search_word:
                    return render_template("index.html", year=year)

                db = Database()
                book_id_list = db.search_books_by_title_and_authors(search_word)
                print(book_id_list)
                if not book_id_list:
                    return error_handler(search_word, "わーお、博識！", year=year)

                book_list = []
                for book_id in book_id_list[:result_num]:
                    # book_id = book_id["_id"]
                    book_info = db.get_book(book_id)

                    if not book_info:
                        raise Exception(f"Search keyword: {search_word} not found")

                    # book_info のkeyが足りない場合は、BookDataから取得
                    if not book_info.get("authors"):
                        print(f"Book ID {book_id} not found in database")
                        book_info = BookData(str(book_id)).get_data()

                    # データが欠けている場合は、Google Books APIから取得
                    if not book_info.get("authors"):
                        print(f"Book ID {book_id} not found in Google Books API")
                        book_info = BookData(str(book_id)).get_data()

                    book_info["amazon_link"] = f"https://www.amazon.co.jp/dp/{book_id}"
                    book_info["book_id"] = book_id
                    print(book_info)
                    book_list.append(book_info)

                return render_template(
                    "index.html",
                    results=book_list,
                    predicted_title=search_word,
                    first_search=True,
                    year=year,
                )

            elif action_type == "book_title_click":
                book_id = request.form["search"]
                db = Database()
                title = db.get_book_title(str(book_id))
                print(title, book_id)

                if not book_id:
                    return render_template("index.html", year=year)

                try:
                    result_df = model.get_similar_books(str(book_id), topn=result_num)
                    if not result_df.values.all():
                        return error_handler(title, "その本はオンリーワンだ！", year=year)
                    results = get_book_info_from_df(result_df)
                    return render_template(
                        "index.html", results=results, predicted_title=title, year=year
                    )
                except KeyError as e:
                    print(e)
                    return error_handler(title, "ごめんなさい、その本はよくわからないです…", year=year)
    except Exception as e:
        print(e)
        text = "こういうことが起こったみたい \n"
        text += str(e)
        return error_handler("", text, year=year)

    return render_template("index.html", year=year)


if __name__ == "__main__":
    app.run(debug=True)
