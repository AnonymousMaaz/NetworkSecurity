from dotenv import load_dotenv
from networksecurity.exception.exception import NetworkSecurityException

import sys
import os


def load_mongo_database_crendetials():
    try:
        env_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../.env")
        )

        load_dotenv()

        MONGO_CLIENT_URL = os.getenv("MONGO_CLIENT_URI")

        if not MONGO_CLIENT_URL:
            raise ValueError("Mongo Client Url are missing.")

        return MONGO_CLIENT_URL
    except Exception as e:
        raise NetworkSecurityException(e, sys)
