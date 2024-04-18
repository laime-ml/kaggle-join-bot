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

logger = logging.getLogger(__name__)


def extract_kaggle(kaggleAccounts: list[str]) -> (dict[str, list[str]], pl.DataFrame):
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
    competition_title_to_rank_members = {}
    competition_achievements = []
    for ka in tqdm(kaggleAccounts):
        URL = f"https://www.kaggle.com/{ka}/competitions"
        options = webdriver.ChromeOptions()
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        driver = webdriver.Chrome(options=options)

        active_comp_flag = False
        achievements_flag = False
        for retry_cnt in range(4):
            driver.get(URL)
            sleep(2**retry_cnt)  # 通信環境によっては待ち時間が必要。logsが不完全になることがある
            logs = driver.get_log("performance")
            for entry in logs:
                message_data = json.loads(entry["message"])["message"]["params"]
                # リクエスト情報が存在する場合のみ処理
                if "request" in message_data:
                    request_data = message_data["request"]
                    request_url = request_data["url"]

                    # 参加中コンペの情報を取得
                    if request_url == "https://www.kaggle.com/api/i/search.SearchContentService/ListSearchContent":
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
                                        if name in competition_title_to_rank_members.keys():
                                            competition_title_to_rank_members[name].append(output)
                                        else:
                                            competition_title_to_rank_members[name] = [output]
                                active_comp_flag = True
                            except Exception as e:
                                logger.error(str(ka) + ", ListSearchContent, retry count: " + str(retry_cnt))
                                logger.error(e)
                                break
                    # 現在のメダル数・tierを取得
                    if request_url == "https://www.kaggle.com/api/i/routing.RoutingService/GetPageDataByUrl":
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
                            logger.error(str(ka) + ", GetPageDataByUrl, retry count: " + str(retry_cnt))
                            logger.error(e)
                            break

            if active_comp_flag and achievements_flag:
                break

        if not active_comp_flag:
            logger.error(f"not active_comp_flag: {ka}")
        if not achievements_flag:
            logger.error(f"not achievements_flag: {ka}")

    driver.quit()
    competition_achievements_df = pl.DataFrame(competition_achievements)
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
