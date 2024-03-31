
import json
import os

from google.oauth2 import service_account


def load_json_to_env(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            for key, value in data.items():
                os.environ[key] = str(value)
        print("環境変数の設定が完了しました。")
    except FileNotFoundError:
        print(f"ファイル '{file_path}' が見つかりません。")
    except json.JSONDecodeError:
        print(f"ファイル '{file_path}' のJSONフォーマットが正しくありません。")
    except Exception as e:
        print(f"環境変数の設定中にエラーが発生しました: {str(e)}")

def extract_spreadsheet():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    # 辞書オブジェクト。認証に必要な情報をHerokuの環境変数から呼び出している
    credential = {
                    "type": "service_account",
                    "project_id": os.environ['SHEET_PROJECT_ID'],
                    "private_key_id": os.environ['SHEET_PRIVATE_KEY_ID'],
                    "private_key": os.environ['SHEET_PRIVATE_KEY'],
                    "client_email": os.environ['SHEET_CLIENT_EMAIL'],
                    "client_id": os.environ['SHEET_CLIENT_ID'],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url":  os.environ['SHEET_CLIENT_X509_CERT_URL']
                }
    
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(credential, scope)
    client = gspread.authorize(credentials)

    #共有設定したスプレッドシートの1枚目のシートを開く
    SpreadSheet = client.open_by_key(os.environ['SPREADSHEET_KEY'])
    RawData = SpreadSheet.worksheet(os.environ['SPREADSHEET_NAME_1'])

    data = RawData.get_all_values()
    name_list = np.array(data)[:, 8][1:]

    return list(name_list)
