from selenium import webdriver
import time


class WebDriver:
    """
    WebDriverクラス
    """

    def __init__(self):
        self._driver = None
        self.options = webdriver.ChromeOptions()

        # for running in background
        self.options.add_argument("--headless")

        # for loading page faster
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument('--proxy-server="direct://"')
        self.options.add_argument("--proxy-bypass-list=*")
        self.options.add_argument("--blink-settings=imagesEnabled=false")

        # for japanese
        self.options.add_argument("--lang=ja")

        # for avoiding error
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            + "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
        )
        self.options.page_load_strategy = "eager"
        self.options.add_argument("log-level=3")
        self.options.add_argument("disable-logging")
        self.options.add_experimental_option("excludeSwitches", ["enable-logging"])

        # for avoiding detection
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option("useAutomationExtension", False)

    def clear(self):
        """clear driver instance and close browser"""
        if self._driver is not None:
            self._driver.quit()
            self._driver = None

    def driver(self):
        if self._driver is None:
            self._driver = webdriver.Chrome(options=self.options)
            self._driver.implicitly_wait(60)
            self._driver.set_page_load_timeout(60)
        return self._driver

    def get(self, url: str, sleep_time: float = 1):
        """call get method of selenium webdriver
        Args:
            url (str): url
            sleep_time (float, optional): sleep time. Defaults to 1.

        Returns:
            None
        """
        if self._driver is not None:
            self._driver.get(url)
            time.sleep(sleep_time)
        else:
            raise Exception("driver is None")
