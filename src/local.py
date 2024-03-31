import json
import logging

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def load_env():
    if load_dotenv():
        logger.info("環境変数の設定が完了しました。")
    else:
        logger.info("key.jsonファイルが存在しません。")
