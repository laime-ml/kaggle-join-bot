import logging
import os

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from kaggle import extract_competition, extract_kaggle
from local import load_env
from spreadsheet import fetch_account_ids_from_spreadsheet

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],  # logging.FileHandler("app.log"),
)

logger = logging.getLogger(__name__)


def main():
    load_env()
    kaggle_accounts = fetch_account_ids_from_spreadsheet()
    logger.info(kaggle_accounts)

    channel = os.getenv("SLACK_CHANNEL", "30_kaggle共有")
    logger.info(channel)

    extract_dict = extract_kaggle(kaggle_accounts)
    competition_dict = extract_competition()

    # slack api
    slack_token = os.environ["SLACK_TOKEN"]
    client = WebClient(token=slack_token)

    text = "現在コンペに参加している人の一覧(順位は今出すことができません)\n"

    competition_dict = {k: v for k, v in sorted(competition_dict.items(), key=lambda x: x[1][2])}

    for k, v in competition_dict.items():
        if k in extract_dict.keys():
            text += f"＊ ＊<{v[4]}|{k}>＊ \n \t(残り{v[2]}日,\t 参加{v[3]}チーム)\n \t\t>>>>\t\t["
            members = extract_dict[k]

            for n in members:
                text += f"{n},  "
            text += "]\n"

    # slackに通知する
    try:
        response = client.chat_postMessage(channel=channel, text=text)
        logger.info(response)
    except SlackApiError as e:
        assert e.response["error"]


if __name__ == "__main__":
    main()
