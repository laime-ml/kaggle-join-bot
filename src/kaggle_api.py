import json
import logging
import os
from collections import defaultdict
from datetime import datetime
from time import sleep

import polars as pl
from kaggle import KaggleApi
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from tenacity import retry, stop_after_attempt
from tqdm.auto import tqdm

logger = logging.getLogger(__name__)


def create_driver() -> webdriver.Chrome:
    driver_path = os.getenv("DRIVER_PATH", "/app/.chromedriver/bin/chromedriver")
    print(f"{driver_path=}")
    service = Service(executable_path=driver_path)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(950, 800)  # 画面サイズを固定してメモリを節約
    return driver


def get_kaggle_users_kaggle_data(driver: webdriver.Chrome, ka: str) -> tuple[dict[str, list[str]], list[dict]]:
    (
        competition_title_to_rank,
        competition_achievements,
        active_comp_flag,
        achievements_flag,
    ) = fetch_kaggle_users_kaggle_data(driver, ka)

    if not active_comp_flag:
        logger.warning(f"{ka}: not active_comp_flag")
    else:
        logger.info(f"{ka}: {competition_title_to_rank}")

    if not achievements_flag:
        logger.warning(f"{ka}: not achievements_flag")
    else:
        logger.info(f"{ka}: {competition_achievements}")

    return competition_title_to_rank, competition_achievements


@retry(stop=stop_after_attempt(4))
def fetch_kaggle_users_kaggle_data(
    driver,
    ka: str,
):
    print(f"{fetch_kaggle_users_kaggle_data.retry.statistics}")
    retry_cnt = fetch_kaggle_users_kaggle_data.retry.statistics.get("attempt_number", 0)
    URL = f"https://www.kaggle.com/{ka}/competitions"
    driver.get(URL)
    sleep(2**retry_cnt)  # 通信環境によっては待ち時間が必要。logsが不完全になることがある
    network_logs = driver.get_log("performance")

    competition_title_to_rank: dict[str, str] = defaultdict(list)
    competition_achievements: list[dict] = []
    active_comp_flag: bool = False
    achievements_flag: bool = False

    for entry in network_logs:
        message_data = json.loads(entry["message"])["message"]["params"]

        if "request" not in message_data:
            continue

        request_data = message_data["request"]
        request_url = request_data["url"]

        # 参加中コンペの情報を取得
        if (
            not active_comp_flag
            and request_url == "https://www.kaggle.com/api/i/search.SearchContentService/ListSearchContent"
        ):
            if json.loads(request_data["postData"])["filters"]["listType"] != "LIST_TYPE_ACTIVE_COMPETITIONS":
                continue

            try:
                response = json.loads(
                    driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": message_data["requestId"]})["body"]
                )
                if "documents" not in response.keys():
                    continue

                documents = response["documents"]
                for res in documents:
                    if "teamRank" in res["competitionDocument"].keys():
                        output = f"{int(res['competitionDocument']['teamRank'])}位@{ka}"
                    else:
                        output = f"順位なし@{ka}"
                    competition_title_to_rank[res["title"]] = output
                active_comp_flag = True

            except Exception as e:
                logger.error(f"{ka}, ListSearchContent, retry count: {retry_cnt}")
                logger.error(e)

        # 現在のメダル数・tierを取得
        elif (
            not achievements_flag
            and request_url == "https://www.kaggle.com/api/i/routing.RoutingService/GetPageDataByUrl"
        ):
            try:
                response = json.loads(
                    driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": message_data["requestId"]})["body"]
                )
                # 4つのtier情報がリストで格納されている
                achievementSummaries = response["userProfile"]["achievementSummaries"]
                competition_achievement = achievementSummaries[0]
                """
                competition_achievementの例
                {'tier': 'MASTER', 'summaryType': 'USER_ACHIEVEMENT_TYPE_COMPETITIONS', 'rankPercentage': 0.00031350303, 'rankOutOf': 200955, 'rankCurrent': 63, 'rankHighest': 47, 'totalGoldMedals': 3, 'totalSilverMedals': 4, 'totalBronzeMedals': 3}
                """
                competition_achievement["username"] = ka
                competition_achievements.append(competition_achievement)
                achievements_flag = True
            except Exception as e:
                logger.error(f"{ka}, GetPageDataByUrl, retry count: {retry_cnt}")
                logger.error(e)

    return competition_title_to_rank, competition_achievements, active_comp_flag, achievements_flag


def fetch_accounts_info(kaggleAccounts: list[str]) -> tuple[dict[str, list[str]], pl.DataFrame]:
    """Kaggleアカウントから

    Args:
        kaggleAccounts (list[str]): _description_

    Returns:
        tuple[dict[str, list[str]], pl.DataFrame]: _description_
    """
    driver = create_driver()

    competition_title_to_rank_members: dict[str, list[str]] = defaultdict(list)
    competition_achievements: list[dict] = []

    for ka in tqdm(kaggleAccounts):
        competition_title_to_rank, _competition_achievements = get_kaggle_users_kaggle_data(driver, ka)
        for k, v in competition_title_to_rank.items():
            competition_title_to_rank_members[k].append(v)
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
        if "Usd" in reward:
            d = com.deadline - datetime.now()
            competition_dict[com.title] = [com.ref[com.ref.rfind("/") + 1 :], reward, d.days, com.team_count, com.url]

    return competition_dict
