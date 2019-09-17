import json
import logging
import os
from typing import List

import settings
from src.common_utils.FireFoxBrowser import FireFoxBrowser
from src.common_utils.LogSetup import setup_log
from src.common_utils.VirtualScreen import VirtualScreen
from src.profile_query_tester.YouTubeQueryTester import YouTubeQueryTester
from src.profile_trainer.FireFoxSimpleAutoBrowsing import FireFoxSimpleAutoBrowsing


def stateful_train_and_test(video_json_path: str, cookie_path: str) -> None:
    label: str = os.path.basename(video_json_path).strip(".json")
    setup_log(__name__ + label)
    log = logging.getLogger(__name__)
    if video_json_path == "":
        log.info("Start stateful control experiment, i.e. no training.")
        with VirtualScreen() as display, FireFoxBrowser(cookie_path) as browser:
            # Notice, no training part here.
            tester = YouTubeQueryTester(browser, __name__, "blank", settings.keyword)
            tester.search_by_keyword(settings.report_results_number)
            tester.click_and_get_right_column_recommendations_from_record(
                tester.query_result[-1], settings.recommend_results_number)
    else:
        if not os.path.isfile(video_json_path):
            log.error("Video json file {} not exists.".format(video_json_path))
            raise RuntimeError("Invalid file path.")
        with open(video_json_path) as f:
            videos: List[str] = json.load(f)
        if not videos:
            log.error("No videos read from json file {}.".format(video_json_path))
        log.info("State stateful experiment. Total training size: {}.".format(len(videos)))
        for i in range(len(videos), settings.training_batch_size):
            sub_video_list: List[str] = videos[i:i + settings.training_batch_size]
            with VirtualScreen() as display, FireFoxBrowser(cookie_path) as browser:
                FireFoxSimpleAutoBrowsing.browse_video_list(sub_video_list, browser)
                tester = YouTubeQueryTester(browser, __name__, label, settings.keyword)
                tester.search_by_keyword(settings.report_results_number)
                tester.click_and_get_right_column_recommendations_from_record(
                    tester.query_result[-1], settings.recommend_results_number)