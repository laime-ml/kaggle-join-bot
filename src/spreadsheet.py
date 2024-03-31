import os

import gspread
import numpy as np
from google.oauth2 import service_account


def fetch_account_ids_from_spreadsheet() -> list[str]:
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

    # 共有設定したスプレッドシートの1枚目のシートを開く
    SpreadSheet = client.open_by_key(os.environ["SPREADSHEET_KEY"])
    RawData = SpreadSheet.worksheet(os.environ["SPREADSHEET_NAME_1"])

    data = RawData.get_all_values()
    name_list = np.array(data)[:, 8][1:]

    return list(name_list)
