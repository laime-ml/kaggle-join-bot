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

1. uv のインストール
   - https://docs.astral.sh/uv/getting-started/installation/

2. ライブラリのインストール

    ```sh
    uv sync
    ```

3. 必要に応じて chromedriver のインストール & .envのDRIVER_PATHを書き換え
    - https://googlechromelabs.github.io/chrome-for-testing/#stable

### 実行方法
```sh
uv run python src/main.py
```

## デプロイ

heroku 上にデプロイ

- heroku登録＆クレカ登録

- heroku CLI のインストール

- requirements.txt を出力
  ```
  uv sync --no-dev
  uv pip freeze > requirements.txt 
  uv sync # 必要に応じて戻す
  ```

- heroku にloginする
  ```
  heroku login
  ```

- heroku のapplicationを作成する
  ```
  APPLICATION_NAME={application_name}
  heroku create $APPLICATION_NAME
  ```

- herokuのapplicationページ(https://dashboard.heroku.com/apps), Settings, Buildpacksで下記のURLを追加する
  ```
  heroku addons:create scheduler:standard --app $APPLICATION_NAME

  # https://github.com/heroku/heroku-buildpack-chrome-for-testing
  heroku buildpacks:add -i 1 heroku-community/chrome-for-testing --app $APPLICATION_NAME

  # python環境: https://elements.heroku.com/buildpacks/heroku/heroku-buildpack-python
  heroku buildpacks:add https://github.com/heroku/heroku-buildpack-python.git
  ```

- herokuのapplicationページ(https://dashboard.heroku.com/apps), Settings, Config Varsで下記の環境変数を設定する
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

  まとめてセットする場合はスペースを含む SHEET_PRIVATE_KEY などを削除してから.envの内容をセットできる。SHEET_PRIVATE_KEYは上記の方法でセット
  ```sh
  heroku config:set $(grep -vE '^\s*(#|$)' .env | sed 's/\\n/\\\\n/g' | paste -sd " " -)
  heroku config:set SLACK_CHANNEL='30_kaggle共有' DRIVER_PATH="/app/.chrome-for-testing/chromedriver-linux64/chromedriver"
  ```

- heroku にdeployする
  ```
  # コミット
  git push heroku main
  ```

- debug
  ```
  # local上でもherokuにloginしていれば実行することができる
  heroku run python src/main.py
  ```

- heroku applicationで定期実行を設定する
  ```
  python src/main.py
  ```