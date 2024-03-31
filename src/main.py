import logging
import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By

from local import load_env
from spreadsheet import fetch_account_ids_from_spreadsheet

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],  # logging.FileHandler("app.log"),
)


def main():
    load_env()
    name_list = fetch_account_ids_from_spreadsheet()
    print(name_list)

    channel = os.getenv("SLACK_CHANNEL", "30_kaggle共有")
    print(channel)


if __name__ == "__main__":
    main()
