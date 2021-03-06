import json
import logging
import os
import random
import time
from typing import List

from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options

import settings

log = logging.getLogger(__name__ + str(os.getpid()))


class FireFoxBrowser:
    def __init__(self, cookie_path: str = None) -> None:
        log.info("Creating firefox instance.")
        if settings.ads_block:
            firefox_profile = FirefoxProfile(settings.firefox_profile_rich_config)
        else:
            firefox_profile = FirefoxProfile(settings.firefox_profile_blank)
        # Disable cache to deal with overload issue when crawling lots of videos
        firefox_profile.set_preference("browser.cache.disk.enable", False)
        firefox_profile.set_preference("browser.cache.memory.enable", False)
        firefox_profile.set_preference("browser.cache.offline.enable", False)
        firefox_profile.set_preference("network.http.use-cache", False)
        log.info("Current firefox profile: {}".format(str(firefox_profile)))
        firefox_option = Options()
        firefox_option.headless = settings.headless
        firefox_option.binary = settings.firefox_binary_path
        log.info("Current firefox headless status: {}, binary path: {}".
                 format(settings.headless, firefox_option.binary_location))
        self.browser: webdriver.Firefox = \
            webdriver.Firefox(firefox_profile=firefox_profile, options=firefox_option)
        self.browser.maximize_window()
        self.browser.delete_all_cookies()
        self.__COOKIE_LOAD_RETRY: int = 3
        self.__cookie_path: str = cookie_path
        if cookie_path and os.path.isfile(cookie_path):
            self.browser.get(settings.initial_website)
            time.sleep(5)
            log.info("Loading cookie from {}.".format(cookie_path))
            cookie_file = None
            while not cookie_file:
                try:
                    with open(cookie_path) as f:
                        cookie_file: List[str] = json.load(f)
                except Exception as e:
                    log.warning("Failed to read cookie file from {}.".format(cookie_path))
                    self.__COOKIE_LOAD_RETRY -= 1
                    if self.__COOKIE_LOAD_RETRY <= 0:
                        raise
                    time.sleep(random.randint(1, 5))
            for cookie in cookie_file:
                try:
                    self.browser.add_cookie(cookie)
                except Exception as e:
                    if "youtube" not in repr(cookie).lower():
                        log.info("Failed to load cookie unrelated to YouTube {}. {}"
                                 .format(cookie, e))
                    else:
                        log.error("Failed to load YouTube related cookie {}. {}.".format(cookie, e),
                                  exc_info=True)
        self.browser.get(settings.initial_website)
        log.info("Open initial website: {}".format(settings.initial_website))
        self.SHORT_WAIT = 5
        time.sleep(self.SHORT_WAIT)

    def __enter__(self) -> webdriver.Firefox:
        log.info("Created firefox browser instance.")
        return self.browser

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.browser:
            if self.__cookie_path and self.browser.get_cookies():
                with open(self.__cookie_path, "w") as f:
                    json.dump(self.browser.get_cookies(), f)
                log.info("Cookie saved at {}.".format(self.__cookie_path))
            self.browser.quit()
            log.info("Closed firefox browser instance.")


if __name__ == '__main__':
    subreddits = ["enoughtrumpspam", "blank", "the_donald"]
    tag = "stateful"
    for subreddit in subreddits:
        cookie_path = os.path.join(settings.ROOT_DIR, settings.INPUT_DATA,
                                   f"{tag}_cookies", f"{subreddit}.json")
        with FireFoxBrowser(cookie_path=cookie_path) as browser:
            # browser.get("https://www.youtube.com/watch?v=740wIinb4-Q")
            time.sleep(30)
