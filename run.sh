#!/bin/bash

# 現在の曜日を取得（1:月曜日, 2:火曜日, …, 7:日曜日）
DAY=$(date +%u)

if [ "$DAY" -eq 1 ] || [ "$DAY" -eq 3 ] || [ "$DAY" -eq 6 ]; then
  echo "今日は実行日です。コマンドを実行します。"
  python src/main.py
else
  echo "今日は実行日ではありません。"
fi
