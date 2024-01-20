from modules.database import Database
import requests
from time import sleep
import pandas as pd
from bs4 import BeautifulSoup


class BookData:
    GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes?q={}"
    AMAZON_URL = "https://www.amazon.co.jp/dp/{}"
    COLUMN_NAMES = [
        "title",
        "authors",
        "published_date",
        "page",
        "print_type",
        "description",
        "identifier",
    ]

    def __init__(self, book_id: str):
        self.wait_time = 1
        self.db = Database()
        self.book_id = book_id

    def _get_current_data(self) -> pd.DataFrame:
        row = self.db.get_book(self.book_id)
        return pd.DataFrame([row], columns=self.COLUMN_NAMES)

    def get_data(self) -> dict:
        db_data = self._get_current_data()

        if db_data.isnull().values.any():
            google_data = self._fetch_data_from_google_books()
            if google_data:
                self.db.update_book(self.book_id, **google_data)
                return google_data

        return db_data.to_dict("records")[0]

    def _fetch_data_from_amazon(self):
        response = requests.get(self.AMAZON_URL.format(self.book_id))
        print(response)
        sleep(self.wait_time)

        if response.status_code != 200:
            return print("error", response.status_code, response.text, sep="\n")

        return self.__parse_amazon_response(response.text)

    def __parse_amazon_response(self, html: str) -> dict:
        print(html)
        soup = BeautifulSoup(html, "html.parser")
        print("-" * 20)
        print(soup)
        title = soup.find(id="productTitle").text.strip()  # type: ignore
        authors = soup.find_all(class_="author a-link-normal")
        authors = [author.text.strip() for author in authors]
        # page = soup.find(id="detailBulletsWrapper_feature_div")
        return {"title": title}  # , "authors": ", ".join(authors)}  #  "page": page}

    def _fetch_data_from_google_books(self) -> dict:
        response = requests.get(self.GOOGLE_BOOKS_URL.format(self.book_id))
        sleep(self.wait_time)

        if response.status_code != 200 or not response.json().get("totalItems"):
            return {}

        return self._parse_google_books_response(response.json())

    def _parse_google_books_response(self, json_data) -> dict:
        for item in json_data.get("items", []):
            volume_info = item.get("volumeInfo", {})
            book_data = {
                "title": volume_info.get("title"),
                "authors": self._format_authors(volume_info.get("authors")),
                "published_date": volume_info.get("publishedDate"),
                "page": volume_info.get("pageCount"),
                "print_type": volume_info.get("printType"),
                "description": volume_info.get("description"),
                "identifier": self._extract_identifier(
                    volume_info.get("industryIdentifiers")
                ),
            }
            if any(book_data.values()):
                return book_data
        return {}

    @staticmethod
    def _format_authors(authors) -> str:
        if not authors:
            return None
        return ", ".join(authors)

    @staticmethod
    def _extract_identifier(industry_identifiers) -> str:
        if not industry_identifiers:
            return None
        return ", ".join([i["identifier"] for i in industry_identifiers])
