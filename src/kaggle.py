import json
import os
from datetime import datetime
from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from tqdm.auto import tqdm

import kaggle
from kaggle.api.kaggle_api_extended import KaggleApi


def extract_kaggle(kaggleAccounts):
    driver_path = os.getenv("DRIVER_PATH", "/app/.chromedriver/bin/chromedriver")
    service = Service(executable_path=driver_path)
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(950, 800)
    extract_dict = {}
    for ka in tqdm(kaggleAccounts):
        URL = f"https://www.kaggle.com/{ka}/competitions"
        options = webdriver.ChromeOptions()
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        driver = webdriver.Chrome(options=options)
        driver.get(URL)
        sleep(1)
        logs = driver.get_log("performance")
        for entry in logs:
            message_data = json.loads(entry["message"])["message"]["params"]
            # リクエスト情報が存在する場合のみ処理
            if "request" in message_data:
                request_data = message_data["request"]
                request_url = request_data["url"]
                if request_url == "https://www.kaggle.com/api/i/search.SearchContentService/ListSearchContent":
                    post_data = request_data["postData"]
                    post_data = json.loads(post_data)
                    list_type = post_data["filters"]["listType"]
                    # activeのみ表示
                    if list_type.find("ACTIVE") > 0:
                        requestid = message_data["requestId"]
                        response = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": requestid})
                        break
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
            if name in extract_dict.keys():
                extract_dict[name].append(output)
            else:
                extract_dict[name] = [output]
        break
    return extract_dict


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
