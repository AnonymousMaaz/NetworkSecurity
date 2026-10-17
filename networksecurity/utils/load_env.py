from dotenv import load_dotenv
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

import sys
import os


def load_mongo_database_crendetials():
    try:
        env_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../.env")
        )

        load_dotenv()

        MONGO_CLIENT_URL = os.getenv("MONGO_CLIENT_URI")
        MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")
        MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION")
        if not MONGO_CLIENT_URL or not MONGODB_DATABASE or not MONGODB_COLLECTION:
            logging.error("MongoDB credentials incomplete/missing")
            raise ValueError("Mongo credentials are missing/incomplete.")

        return MONGO_CLIENT_URL, MONGODB_DATABASE, MONGODB_COLLECTION
    except Exception as e:
        raise NetworkSecurityException(e, sys)
