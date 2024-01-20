import requests
from modules.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from time import sleep
from tqdm.auto import tqdm

# from datetime import datetime, timedelta
# import json


class Scraping:
    def __init__(self, category=0, count=99999, status=0, rank=0):
        """
        Scrapingクラスのコンストラクタ

        Args:
            category (str): カテゴリー名
            count (int): 取得する書籍数
            status (int): 読書状況
            rank (int): ランキング

        Returns:
            None
        """
        self.wait_time = 3
        self.category = category
        self.count = count
        self.status = status
        self.rank = rank
        self.webdriver = WebDriver()
        self.webdriver.clear()
        self.driver = self.webdriver.driver()
        self.wait = WebDriverWait(self.driver, self.wait_time)

    def get_popular_profile_tags(self):
        """
        Booklogの人気のプロフィールタグを取得する

        Args:
            None

        Returns:
            list: プロフィールタグのリスト
        """
        url = "https://booklog.jp/profiletags"
        driver = self.driver
        self.webdriver.get(url)
        sleep(self.wait_time)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        tags = soup.select("ul.tagList > li > a")
        # tagのテキストを取得。()内の文字列を削除
        tags = [tag.text.split("(")[0] for tag in tags]
        return tags

    def get_users_from_profile_tag(self, tag: str, page: int = 1):
        """
        Get Booklog users from profile tag.

        Args:
            tag (str): profile tag
            page (int): number of pages to scrape. 0 means all pages. Defaults to 1.

        Returns:
            list: list of users
        """
        users = []
        if page == 0:
            page = 9999
        for i in tqdm(range(page)):
            _users = self._get_users(tag, i + 1)
            users += _users
            if len(_users) < 10:
                break
        return users

    def get_book_urls_from_ranking(self, year: int, page: int = 6) -> list[str]:
        """
        Get Booklog users from popular books.

        Args:
            year (int): year
            page (int): number of pages to scrape. 0 means all pages. Defaults to 1.

        Returns:
            list: list of users
        """
        if page > 6:
            page = 6
        elif page < 1:
            page = 1

        book_urls = []
        for p in range(1, page + 1):
            url = f"https://booklog.jp/ranking/annual/{str(year)}/book?page={p}"
            driver = self.driver
            self.webdriver.get(url)
            sleep(self.wait_time)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            books_a = soup.select(
                "div.autopagerize_page_element > ul.ranking-list > li > div.desc > h3 > a"
            )
            book_urls.extend([book.get("href") for book in books_a])
        return book_urls

    def get_users_from_book_url(self, book_url: str, page: int = 1) -> list[str]:
        if page > 10:
            page = 10
        elif page < 1:
            page = 1

        user_id_list = []
        for p in range(1, page + 1):
            url = f"https://booklog.jp{book_url}?page={p}"
            driver = self.driver
            self.webdriver.get(url)

            try:
                self.wait.until(EC.presence_of_element_located((By.ID, "reviewLine")))
            except TimeoutException:
                raise TimeoutException(f"Timeout: {url}")

            soup = BeautifulSoup(driver.page_source, "html.parser")
            reviewers_a = soup.select(
                "div#reviewLine > ul > li > div.summary > div.user-info-area > div > div.user-name-area > p > a"
            )
            user_id_list.extend(
                [user.get("href").split("/")[-1] for user in reviewers_a]  # type: ignore
            )
        return user_id_list

    def _get_users(self, tag: str, page: int):
        url = f"https://booklog.jp/profiletag/{tag}?page={page}"
        driver = self.driver
        self.webdriver.get(url)

        try:
            self.wait.until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "autopagerize_page_element")
                )
            )
        except TimeoutException:
            raise TimeoutException(f"Timeout: {url}")

        soup = BeautifulSoup(driver.page_source, "html.parser")
        users_div = soup.select("div.autopagerize_page_element > div.tagListArea")
        users = []
        for user in users_div:
            a = user.select_one("div > a")
            user = a.get("href").split("/")[-1]  # type: ignore
            users.append(user)
        return users

    def load_books(self, user_id):
        """
        Get information of books from Booklog.

        Args:
            None

        Returns:
            list: list of information of book.
        """
        url = f"https://api.booklog.jp/json/{user_id}"
        params = {
            "category": self.category,
            "status": self.status,
            "rank": self.rank,
            "count": self.count,
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return []

        try:
            data = response.json()
        except Exception as e:
            raise Exception(f"Error: {e} \n Response: {response.text}")

        return self.format2list(data)

    def format2list(self, data: dict) -> list[dict]:
        """
        Format JSON data to list of dictionary.

        Args:
            data (dict): JSON data

        Returns:
            list[dict]: list of dictionary
        """
        books = data.get("books", [])
        new_books = []
        for book in books:
            book = {
                "BOOK_ID": book["url"].split("/")[-1],
                "TITLE": book["title"]
                # "CATALOG": book["catalog"],
            }
            new_books.append(book)
        return new_books
