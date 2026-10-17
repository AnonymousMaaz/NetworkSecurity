import os
import sys
import json
import certifi
import pandas as pd
import numpy as np


from pymongo import MongoClient
from networksecurity.utils.load_env import load_mongo_database_crendetials
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

MONGO_CLIENT_URI, MONGODB_DATABASE, MONGODB_COLLECTION = (
    load_mongo_database_crendetials()
)


ca = certifi.where()


class NetworkDataExtract:
    def csv_to_json_convertor(self, file_path):
        try:
            dataset = pd.read_csv(file_path)
            dataset.reset_index(drop=True, inplace=True)

            records = list(json.loads(dataset.T.to_json()).values())

            return records
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def insert_data_to_mongodb(self, records, database, collection):
        try:
            self.database = database
            self.collection = collection
            self.records = records

            logging.info("Initializing MongoDB Client...")
            self.mongo_client = MongoClient(MONGO_CLIENT_URI)
            logging.info("MongoDB Client Initialization Successfull")
            self.database = self.mongo_client[self.database]

            self.collection = self.database[self.collection]

            logging.info("Initializing push sequence...")
            self.collection.insert_many(self.records)
            logging.info("Pushing Data Completed")
            return len(self.records)
        except Exception as e:
            logging.error("Exception Occurred")
            raise NetworkSecurityException(e, sys)


if __name__ == "__main__":
    network_etl = NetworkDataExtract()

    records = network_etl.csv_to_json_convertor("Network_Data/phisingData.csv")

    records_length = network_etl.insert_data_to_mongodb(
        records, MONGODB_DATABASE, MONGODB_COLLECTION
    )

    print(records_length)
