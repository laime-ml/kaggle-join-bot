import logging
import os

import gspread
import numpy as np
import polars as pl
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


def get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # 辞書オブジェクト。認証に必要な情報をHerokuの環境変数から呼び出している
    json_acct_info = {
        "type": "service_account",
        "project_id": os.environ["SHEET_PROJECT_ID"],
        "private_key_id": os.environ["SHEET_PRIVATE_KEY_ID"],
        "private_key": os.environ["SHEET_PRIVATE_KEY"],
        "client_email": os.environ["SHEET_CLIENT_EMAIL"],
        "client_id": os.environ["SHEET_CLIENT_ID"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.environ["SHEET_CLIENT_X509_CERT_URL"],
    }

    credentials = service_account.Credentials.from_service_account_info(json_acct_info, scopes=scope)
    client = gspread.authorize(credentials)
    return client


def fetch_account_ids_from_spreadsheet() -> list[str]:
    client = get_client()
    SpreadSheet = client.open_by_key(os.environ["SPREADSHEET_KEY"])
    RawData = SpreadSheet.worksheet("フォームの回答 1")
    data = RawData.get_all_values()
    name_list = np.array(data)[:, 2][1:]

    return list(name_list)


def update_laime_ranking(competition_achievements_df: pl.DataFrame):
    columns = [
        "rank",
        "username",
        "tier",
        "rankCurrent",
        "rankHighest",
        "totalGoldMedals",
        "totalSilverMedals",
        "totalBronzeMedals",
    ]
    df = competition_achievements_df.sort(["rankCurrent", "tier"], nulls_last=True)
    df = df.with_row_index(name="rank", offset=1).select(columns)

    client = get_client()
    SpreadSheet = client.open_by_key(os.environ["SPREADSHEET_KEY"])
    worksheet = SpreadSheet.worksheet("KaggleRankCurrent")
    sheet_columns = worksheet.get_all_values()[0]
    old_df = pl.DataFrame(data=np.array(worksheet.get_values())[1:, : len(columns)], schema=columns)
    logger.info(old_df)
    logger.info(df)

    worksheet.clear()
    worksheet.batch_update(
        [
            {"range": "A1", "values": [sheet_columns]},
            {
                "range": "A2",
                "values": df.rows(),
            },
        ]
    )
