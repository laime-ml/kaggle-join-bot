import argparse
import logging
import os

import click
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from kaggle_api import extract_competition, fetch_accounts_info
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


@click.command()
@click.option("-d", "--debug", is_flag=True, default=False)
def main(debug: bool):
    load_env()

    # スプレッドシートからkaggleアカウントを取得
    kaggle_accounts = fetch_account_ids_from_spreadsheet()
    if debug:
        kaggle_accounts = kaggle_accounts[:3]
    logger.info(kaggle_accounts)

    # Kaggleの情報を取得
    competition_title_to_rank_members, competition_achievements_df = fetch_accounts_info(kaggle_accounts)
    competition_dict = extract_competition()

    # スプレッドシートに情報を更新
    changed_df = update_laime_ranking(competition_achievements_df)
    logger.info(changed_df)

    # slack api
    text = "*現在コンペに参加している人の一覧*\n"
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

    if len(changed_df) > 0:
        text += "\n\n*メダル獲得者*\n"
        for row in changed_df.iter_rows(named=True):
            if row["totalGoldMedals_new"] > row["totalGoldMedals"]:
                text += f" {row['username']} さんが {row['totalGoldMedals_new']} 枚目の金メダルを獲得しました！\n"
            if row["totalSilverMedals_new"] > row["totalSilverMedals"]:
                text += f" {row['username']} さんが {row['totalSilverMedals_new']} 枚目の銀メダルを獲得しました！\n"
            if row["totalBronzeMedals_new"] > row["totalBronzeMedals"]:
                text += f" {row['username']} さんが {row['totalBronzeMedals_new']} 枚目の銅メダルを獲得しました！\n"

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
