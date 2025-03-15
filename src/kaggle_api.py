import json
import logging
import os
from datetime import datetime
from time import sleep

import polars as pl
from kaggle import KaggleApi
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from tqdm.auto import tqdm
from tenacity import retry, stop_after_attempt

logger = logging.getLogger(__name__)


def get_kaggle_users_kaggle_data(ka: str) -> tuple[dict[str, list[str]], list[dict]]:
    options = webdriver.ChromeOptions()
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    driver = webdriver.Chrome(options=options)

    (
        competition_title_to_rank_members,
        competition_achievements,
        active_comp_flag,
        achievements_flag,
    ) = fetch_kaggle_users_kaggle_data(driver, ka)

    if not active_comp_flag:
        logger.error(f"not active_comp_flag: {ka}")
    if not achievements_flag:
        logger.error(f"not achievements_flag: {ka}")

    return competition_title_to_rank_members, competition_achievements


@retry(stop=stop_after_attempt(4))
def fetch_kaggle_users_kaggle_data(
    driver,
    ka: str,
):
    retry_cnt = fetch_kaggle_users_kaggle_data.retry.statistics["attempt_number"]
    URL = f"https://www.kaggle.com/{ka}/competitions"
    driver.get(URL)
    sleep(2**retry_cnt)  # 通信環境によっては待ち時間が必要。logsが不完全になることがある
    logs = driver.get_log("performance")

    competition_title_to_rank_members: dict[str, list] = {}
    competition_achievements: list[dict] = []
    active_comp_flag: bool = False
    achievements_flag: bool = False

    for entry in logs:
        message_data = json.loads(entry["message"])["message"]["params"]
        # リクエスト情報が存在する場合のみ処理
        if "request" in message_data:
            request_data = message_data["request"]
            request_url = request_data["url"]

            # 参加中コンペの情報を取得
            if (
                not active_comp_flag
                and request_url == "https://www.kaggle.com/api/i/search.SearchContentService/ListSearchContent"
            ):
                post_data = request_data["postData"]
                post_data = json.loads(post_data)
                list_type = post_data["filters"]["listType"]
                # activeのみ表示
                if list_type.find("ACTIVE") > 0:
                    try:
                        requestid = message_data["requestId"]
                        response = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": requestid})
                        response = response["body"]
                        response = json.loads(response)
                        if "documents" in response.keys():
                            response = response["documents"]
                            for res in response:
                                if "teamRank" in res["competitionDocument"].keys():
                                    rank = res["competitionDocument"]["teamRank"]
                                    name = res["title"]
                                    output = f"{int(rank)}位@{ka}"
                                else:
                                    name = res["title"]
                                    output = f"順位なし@{ka}"
                                competition_title_to_rank_members.setdefault(name, []).append(output)
                        active_comp_flag = True
                    except Exception as e:
                        logger.error(f"{ka}, ListSearchContent, retry count: {retry_cnt}")
                        logger.error(e)
            # 現在のメダル数・tierを取得
            if (
                not achievements_flag
                and request_url == "https://www.kaggle.com/api/i/routing.RoutingService/GetPageDataByUrl"
            ):
                try:
                    post_data = request_data["postData"]
                    post_data = json.loads(post_data)
                    requestid = message_data["requestId"]
                    response = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": requestid})
                    response = response["body"]
                    response = json.loads(response)
                    # 4つのtier情報がリストで格納されている
                    achievementSummaries = response["userProfile"]["achievementSummaries"]
                    competition_achievement = achievementSummaries[0]
                    # e.g.) {'tier': 'MASTER', 'summaryType': 'USER_ACHIEVEMENT_TYPE_COMPETITIONS', 'rankPercentage': 0.00031350303, 'rankOutOf': 200955, 'rankCurrent': 63, 'rankHighest': 47, 'totalGoldMedals': 3, 'totalSilverMedals': 4, 'totalBronzeMedals': 3}
                    competition_achievement["username"] = ka
                    competition_achievements.append(competition_achievement)
                    achievements_flag = True
                except Exception as e:
                    logger.error(f"{ka}, GetPageDataByUrl, retry count: {retry_cnt}")
                    logger.error(e)

    return competition_title_to_rank_members, competition_achievements, active_comp_flag, achievements_flag


def extract_kaggle(kaggleAccounts: list[str]) -> tuple[dict[str, list[str]], pl.DataFrame]:
    driver_path = os.getenv("DRIVER_PATH", "/app/.chromedriver/bin/chromedriver")
    service = Service(executable_path=driver_path)
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(950, 800)  # 画面サイズを固定してメモリを節約

    competition_title_to_rank_members: dict[str, list[str]] = {}
    competition_achievements: list[dict] = []

    for ka in tqdm(kaggleAccounts):
        _competition_title_to_rank_members, _competition_achievements = get_kaggle_users_kaggle_data(ka)
        competition_title_to_rank_members |= _competition_title_to_rank_members
        competition_achievements.extend(_competition_achievements)

    driver.quit()
    competition_achievements_df = pl.DataFrame(competition_achievements).unique(subset=["username"])
    return competition_title_to_rank_members, competition_achievements_df


def extract_competition():
    # Kaggle APIの定義
    api = KaggleApi()
    api.authenticate()

    competitions_list = api.competitions_list()
    competition_dict = {}

    for com in competitions_list:
        reward = com.reward
        if "$" in reward:
            d = com.deadline - datetime.now()
            competition_dict[com.title] = [com.ref[com.ref.rfind("/") + 1 :], reward, d.days, com.teamCount, com.url]

    return competition_dict
