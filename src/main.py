import logging
import os

import polars as pl
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from kaggle_api import extract_competition, extract_kaggle
from local import load_env
from spreadsheet import fetch_account_ids_from_spreadsheet, update_laime_ranking

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],  # logging.FileHandler("app.log"),
)

logger = logging.getLogger(__name__)


def sort_rank_members(rank_members: list[str]):
    def extract_key(string):
        try:
            # '@'より前の部分を取り出し、'位'を削除して数値に変換
            return int(string.split("@")[0].replace("位", ""))
        except ValueError:
            # 数値に変換できない場合は、大きな値を返して一番後ろに配置
            return float("inf")

    # extract_key関数をキーとして使用してソート
    sorted_list = sorted(rank_members, key=extract_key)
    return sorted_list


def main():
    # 環境変数の読み込み
    load_env()

    # スプレッドシートからkaggleアカウントを取得
    kaggle_accounts = fetch_account_ids_from_spreadsheet()
    kaggle_accounts = kaggle_accounts[:5]
    logger.info(kaggle_accounts)

    # ChromeDriver, kaggle apiを使ってKaggleの情報を取得
    competition_title_to_rank_members, competition_achievements_df = extract_kaggle(kaggle_accounts)
    competition_dict = extract_competition()

    # スプレッドシートに情報を更新
    update_laime_ranking(competition_achievements_df)

    # slack api
    text = "現在コンペに参加している人の一覧\n"
    competition_dict = {
        competition_title: v for competition_title, v in sorted(competition_dict.items(), key=lambda x: x[1][2])
    }
    for competition_title, v in competition_dict.items():
        if competition_title in competition_title_to_rank_members.keys():
            text += f"＊ ＊<{v[4]}|{competition_title}>＊ \n \t(残り{v[2]}日,\t 参加{v[3]}チーム)\n \t\t>>>>\t\t["
            rank_members = competition_title_to_rank_members[competition_title]
            rank_members = sort_rank_members(rank_members)
            for n in rank_members:
                text += f"{n},  "
            text += "]\n"

    slack_token = os.environ["SLACK_TOKEN"]
    client = WebClient(token=slack_token)
    channel = os.getenv("SLACK_CHANNEL", "30_kaggle共有")
    logger.info(channel)
    try:
        response = client.chat_postMessage(channel=channel, text=text)
        logger.info(response)
    except SlackApiError as e:
        logger.error(e.response["error"])
        assert e.response["error"]


if __name__ == "__main__":
    main()
