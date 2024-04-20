import logging

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def load_env():
    if load_dotenv(override=True):  # ローカルなどで既に環境変数が設定されている場合は.envで上書きする
        logger.info("環境変数の設定が完了しました。")
    else:
        # herokuでの実行など.envファイルが存在しない場合
        logger.info(".envファイルが存在しません。")
