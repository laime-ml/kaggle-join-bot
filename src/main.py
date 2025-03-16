import logging
import os
from datetime import datetime

import click
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from kaggle_api import fetch_accounts_info, fetch_award_competitions
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
    competitions_list = fetch_award_competitions()

    # スプレッドシートに情報を更新
    changed_df = update_laime_ranking(competition_achievements_df)
    logger.info(changed_df)

    # slack api
    text_list = [
        "*現在コンペに参加している人の一覧*",
    ]
    for com in competitions_list:
        if com.title in competition_title_to_rank_members.keys():
            remain_days = (com.deadline - datetime.now()).days
            text_list.extend(
                [
                    f"＊ ＊<{com.url}|{com.title}>＊ \n \t(残り{remain_days}日,\t 参加{com.team_count}チーム)",
                    f"\t\t>>>>\t\t[{', '.join(sort_rank_members(competition_title_to_rank_members[com.title]))}]",
                ]
            )
    if len(changed_df) > 0:
        text_list.append("\n\n*メダル獲得者*")
        for row in changed_df.iter_rows(named=True):
            for medal in ["Gold", "Silver", "Bronze"]:
                if row[f"total{medal}Medals_new"] > row[f"total{medal}Medals"]:
                    text_list.append(
                        f" {row['username']} さんが {row[f'total{medal}Medals_new']} 枚目の{medal}メダルを獲得しました！"
                    )
    text_list.append(
        "\n\n<https://docs.google.com/spreadsheets/d/1W9lXy62Ed6EkwfDWFRGxzkWA2iqzz9M73UfRC_1qdiI/edit#gid=1003970766|LAIMEランキング>"
    )
    text = "\n".join(text_list)

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
