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

  SLACK_TOKEN=xxxx
  SLACK_CHANNEL=xxx

  # kaggle api 用
  KAGGLE_USERNAME=xxx
  KAGGLE_KEY=xxx

  # 存在しない場合は "/app/.chromedriver/bin/chromedriver"
  DRIVER_PATH=xxx/yyy
  ```

## ローカル環境構築

1. rye のインストール

   - https://rye-up.com/guide/installation/

2. ライブラリのインストール

```
rye sync
```

必要に応じて chronium のインストール

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
- heroku にloginする
  ```
  heroku login
  ```

- heroku のapplicationを作成する
  ```
  heroku create -a application_name
  ```

- herokuのapplicationページ(https://dashboard.heroku.com/apps), Settings, Buildpacksで下記のURLを追加する
  - https://github.com/heroku/heroku-buildpack-google-chrome
  - https://github.com/heroku/heroku-buildpack-chromedriver

- herokuのapplicationページ(https://dashboard.heroku.com/apps), Settings, COnfig Varsで下記の環境変数を設定する
  - SHEET_PROJECT_ID
  - SHEET_PRIVATE_KEY_ID
  - SHEET_PRIVATE_KEY
  - SHEET_CLIENT_EMAIL
  - SHEET_CLIENT_ID
  - SHEET_CLIENT_X509_CERT_URL
  - SPREADSHEET_KEY
  - SPREADSHEET_NAME_1
  - SLACK_TOKENx
  - SLACK_CHANNEL
  - KAGGLE_USERNAME
  - KAGGLE_KEY

- heroku にdeployする
  ```
  git add src/
  git add requirements.txt
  git add runtime.txt
  git commit -m "first commit"
  git push heroku main
  ```

- debug
  ```
  # local上でもherokuにloginしていれば実行することができる
  heroku run python src.main.py
  ```

- heroku applicationで定期実行を設定する