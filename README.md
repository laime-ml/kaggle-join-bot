# kaggle-join-bot

## 構成

- runtime.txt: heroku 用
- requirements.txt: heroku 用

- .env: ローカル用。クレデンシャルの環境変数を設定

## 準備

- スプレッドシートにアクセスするための API キーを発行
  - LAIME アカウントの GCP から
- 環境変数の設定
  ```
  SHEET_PROJECT_ID
  SHEET_PRIVATE_KEY_ID
  SHEET_PRIVATE_KEY
  SHEET_CLIENT_EMAIL
  SHEET_CLIENT_ID
  SHEET_CLIENT_X509_CERT_URL
  ```

## ローカル環境構築

1. rye のインストール

   - https://rye-up.com/guide/installation/

### 実行方法

```
rye run rye run python src/main.py
```

## デプロイ

heroku 上にデプロイ
