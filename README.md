# kaggle-join-bot

## 構成

- runtime.txt: heroku 用
- requirements.txt: heroku 用

## 準備

- スプレッドシートにアクセスするための API キーを発行
  - LAIME アカウントの GCP から

## ローカル環境構築

1. rye のインストール

   - https://rye-up.com/guide/installation/

### 実行方法

```
rye run rye run python src/main.py
```

## デプロイ

heroku 上にデプロイ
