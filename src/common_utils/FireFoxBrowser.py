import logging
import random
import time
import os
import json

from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options

import settings

log = logging.getLogger(__name__)


class FireFoxBrowser:
    def __init__(self, cookie_path: str = None) -> None:
        log.info("Creating firefox instance.")
        if settings.ads_block:
            firefox_profile = FirefoxProfile(settings.firefox_profile_rich_config)
        else:
            firefox_profile = FirefoxProfile(settings.firefox_profile_blank)
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
        if cookie_path:
            if not os.path.isfile(cookie_path):
                log.error("Cookie path {} is not a file.".format(cookie_path))
                raise RuntimeError
            log.info("Loading cookie from {}.".format(cookie_path))
            cookie_file = None
            while not cookie_file:
                try:
                    with open(cookie_path) as f:
                        cookie_file = json.load(f)
                except Exception as e:
                    log.warning("Failed to read cookie file from {}.".format(cookie_path))
                    self.__COOKIE_LOAD_RETRY -= 1
                    if self.__COOKIE_LOAD_RETRY <= 0:
                        raise RuntimeError(e)
                    time.sleep(random.randint(1, 5))
            try:
                self.browser.add_cookie(cookie_file)
            except Exception as e:
                if "youtube" not in str(e).lower():
                    log.info("Failed to load cookie unrelated to YouTube. {}".format(e))
                else:
                    log.error("Failed to load YouTube related cookie. {}.".format(e),
                              exec_info=True)
                    raise RuntimeError(e)
            log.info("All cookies loaded.")
        self.browser.get(settings.initial_website)
        log.info("Open initial website: {}".format(settings.initial_website))
        self.SHORT_WAIT = 5
        time.sleep(self.SHORT_WAIT)

    def __enter__(self) -> webdriver.Firefox:
        log.info("Created firefox browser instance.")
        return self.browser

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.browser:
            if self.__cookie_path:
                with open(self.__cookie_path, "w") as f:
                    json.dump(self.browser.get_cookies(), f)
                log.info("Cookie saved at {}.".format(self.__cookie_path))
            self.browser.quit()
            log.info("Closed firefox browser instance.")
