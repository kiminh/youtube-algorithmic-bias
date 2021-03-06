import logging
import os
import time
from typing import List

from selenium import webdriver
from selenium.common.exceptions import JavascriptException, InvalidSessionIdException

import settings
from src.common_utils.YouTubePlayerException import YouTubePlayerException

log = logging.getLogger(__name__ + str(os.getpid()))


class FireFoxSimpleAutoBrowsing:
    RETRY_CHANCES = 3
    SCREENSHOT_PATH = os.path.join(settings.LOG_ROOT, "screenshot", str(os.getpid()))
    if not os.path.exists(SCREENSHOT_PATH):
        os.makedirs(SCREENSHOT_PATH)
    STATUS_CHECK_INTERVAL = 5
    log.info("Class variables: retry changes: {}, screenshot saving path: {}, "
             "status check interval: {} seconds. Current process id {}."
             .format(RETRY_CHANCES, SCREENSHOT_PATH, STATUS_CHECK_INTERVAL, os.getpid()))

    @staticmethod
    def __trim_youtube_link(link: str):
        """
        Remove time stamp from link, start watching from beginning.
        :param link: youtube link
        :return: trimed youtube link, without start time query
        """
        if "t=" in link:
            # chop off "&t=", "?t=" or "#t="
            link = link.split('t=')[0][:-1]
        return link

    @staticmethod
    def __play_at_fastest_speed(browser: webdriver.Firefox):
        js = 'return document.getElementById("movie_player").getAvailablePlaybackRates()'
        playback_rates: list = list(browser.execute_script(js))
        fast_js = 'document.getElementById("movie_player").setPlaybackRate({})' \
            .format(playback_rates[-1])
        browser.execute_script(fast_js)
        log.info("\tPlay at fastest speed {}.".format(playback_rates[-1]))

    @staticmethod
    def __get_player_status(browser: webdriver.Firefox) -> str:
        status_check_list = {-1: 'unstarted', 0: 'ended', 1: 'playing',
                             2: 'paused', 3: 'buffering', 5: 'video cued'}
        js = 'return document.getElementById("movie_player").getPlayerState()'
        return status_check_list[browser.execute_script(js)]

    @staticmethod
    def __get_video_elapsed_time(browser: webdriver.Firefox) -> float:
        js = 'return document.getElementById("movie_player").getCurrentTime()'
        return browser.execute_script(js)

    @staticmethod
    def browse_video_list(video_list: List[str], browser: webdriver.Firefox):
        """
        Auto browsing a list of videos in YouTube
        :param video_list: list of videos
        :param browser: FireFox browser instance
        """
        if not video_list or len(video_list) == 0:
            log.warning("Empty video list or null list.")
        log.debug("Video list to be watched: {}".format(video_list))
        unknown_failure_counter: int = 0
        js_execution_failure_counter: int = 0
        success_count: int = 0
        total_video_length: int = len(video_list)
        log.info("Start watching list of videos, total size: {}".format(total_video_length))
        for i, video in enumerate(video_list):
            current_success: bool = False
            retry_count: int = 0
            video: str = FireFoxSimpleAutoBrowsing.__trim_youtube_link(video)
            log.info("Index: {}, watching: {}".format(i + 1, video))
            current_video_screenshot_dir: str = os.path.join(
                FireFoxSimpleAutoBrowsing.SCREENSHOT_PATH,
                video.replace('/', '-').replace(':', '-').replace('.', '-'))
            if not os.path.exists(current_video_screenshot_dir):
                os.makedirs(current_video_screenshot_dir)
                log.debug("\tCreate dir {} for screenshot".format(current_video_screenshot_dir))
            log.info("\tScreenshot for video {} saved at {}."
                     .format(video, current_video_screenshot_dir))
            while not current_success and retry_count < FireFoxSimpleAutoBrowsing.RETRY_CHANCES:
                try:
                    refreshed: bool = False
                    browser.get(video)
                    if settings.fast:
                        FireFoxSimpleAutoBrowsing.__play_at_fastest_speed(browser)
                    current_status: str = FireFoxSimpleAutoBrowsing.__get_player_status(browser)
                    video_time: float = FireFoxSimpleAutoBrowsing.__get_video_elapsed_time(browser)
                    while current_status != "ended" and video_time < settings.watch_time:
                        previous_video_time: float = video_time
                        previous_status: str = current_status
                        log.debug("\tStatus: {}, video time: {:7.2f}s"
                                  .format(current_status, video_time))
                        time.sleep(FireFoxSimpleAutoBrowsing.STATUS_CHECK_INTERVAL)
                        screenshot_file_name: str = \
                            os.path.join(current_video_screenshot_dir, str(time.ctime()) + ".png")
                        browser.save_screenshot(screenshot_file_name)
                        video_time = FireFoxSimpleAutoBrowsing.__get_video_elapsed_time(browser)
                        current_status = FireFoxSimpleAutoBrowsing.__get_player_status(browser)
                        if abs(previous_video_time - video_time) < 10e-3 \
                                and previous_status == current_status \
                                and current_status in ['unstarted', 'paused', 'buffering']:
                            if not refreshed:
                                browser.refresh()
                                log.warning("\tVideo playing frozen. "
                                            "Try resolve by browser refreshed..")
                                refreshed = True
                            else:
                                raise YouTubePlayerException(
                                    "\tYouTube video play frozen, video stopped time: {}, "
                                    "current play status: {}.".format(video_time, current_status),
                                    video)
                    current_success = True
                    success_count += 1
                except JavascriptException:
                    js_execution_failure_counter += 1
                    log.warning("JavascriptException during watching video {}, "
                                "most like caused by unavailable video. "
                                "Traceback is provided for analysis. Jump to next video (if any)."
                                .format(video), exc_info=True)
                    break
                except InvalidSessionIdException as e:
                    log.critical("Lost connection to Firefox browser, or Firefox browser crashed."
                                 " Probably due to previous viewing too many videos. There is no "
                                 "point to continue current test. Quit the whole experiment.")
                    raise
                except Exception as e:
                    retry_count += 1
                    log.error("Exception during watching video {}, caused by: {},"
                              " retry count: {}".format(video, e, retry_count),
                              exc_info=True)
                    if retry_count >= FireFoxSimpleAutoBrowsing.RETRY_CHANCES:
                        unknown_failure_counter += 1
                        log.error("Video {} failed after retry {} times."
                                  .format(video, retry_count))
        log.info("Finished watching list, total {}, succeed count: {}, "
                 "unknown failed count: {}, possible video unavailable count: {}".
                 format(total_video_length, success_count, unknown_failure_counter,
                        js_execution_failure_counter))
        return
