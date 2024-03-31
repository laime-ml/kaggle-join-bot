# kaggle-join-bot

## 構成

- runtime.txt: heroku 用
- requirements.txt: heroku 用
- .env: 追加の環境変数の設定。

## 準備

- スプレッドシートにアクセスするための API キーを発行(LAIME アカウントの GCP から)
- .env に環境変数の設定

  ```
  # apiキーの
  SHEET_PROJECT_ID=xxx
  SHEET_PRIVATE_KEY_ID=xxx
  SHEET_PRIVATE_KEY=xxx
  SHEET_CLIENT_EMAIL=xxx
  SHEET_CLIENT_ID=xxx
  SHEET_CLIENT_X509_CERT_URL=xxx

  SPREADSHEET_KEY={LAIMEランキングスプレッドシートのURLに記載のID}
  SPREADSHEET_NAME_1=KaggleRankCurrent

  SLACK_TOKEN=xxxx

  # kaggle api 用
  KAGGLE_USERNAME=xxx
  KAGGLE_KEY=xxx

  # 存在しない場合は "/app/.chromedriver/bin/chromedriver"
  DRIVER_PATH=xxx/yyy
  ```

## ローカル環境構築

1. rye のインストール

   - https://rye-up.com/guide/installation/

### 実行方法

```
rye run python src/main.py
```

## デプロイ

heroku 上にデプロイ

- requirements.txt を出力
  ```
  rye run pip freeze > requirements.txt
  ```
