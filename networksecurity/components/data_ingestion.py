from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.entity.config_entity import (
    DataIngestionConfig,
)
from networksecurity.entity.artifact_entity import DataIngestionArtifact
from networksecurity.utils.load_env import load_mongo_database_crendetials
from sklearn.model_selection import train_test_split
from pymongo import MongoClient


import os
import sys
import pandas as pd

try:
    logging.info("Loading MONGODB URL from env file...")
    MONGODB_URI, _, _ = load_mongo_database_crendetials()
except Exception as e:
    logging.error(f"Error occured while loading the MONGODB URL: {e}")
    raise NetworkSecurityException(e, sys)


class DataIngestion:
    def __init__(self, data_ingestion_config: DataIngestionConfig):
        try:
            self.data_ingestion_config = data_ingestion_config
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def export_collection_as_dataframe(self):
        try:
            client = MongoClient(MONGODB_URI)
            database = client[self.data_ingestion_config.database_name]
            collection = database[self.data_ingestion_config.collection_name]

            records = list(collection.find())
            df = pd.DataFrame(records)
            df.drop(columns=["_id"], inplace=True)

            client.close()
            return df
        except Exception as e:
            client.close()
            raise NetworkSecurityException(e, sys)

    def export_data_into_feature_store(self, dataframe: pd.DataFrame):
        try:
            self.feature_store_file_path = (
                self.data_ingestion_config.feature_store_file_path
            )
            dir_path = os.path.dirname(self.feature_store_file_path)
            logging.info("Exporting Data to CSV...")
            os.makedirs(dir_path, exist_ok=True)
            dataframe.to_csv(self.feature_store_file_path, index=False, header=True)
            logging.info("Data exporting to csv completed successfully.")
            return dataframe
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def split_data_into_train_test(self, dataframe: pd.DataFrame):
        try:
            logging.info("Initializing Train Test Split...")
            train_set, test_set = train_test_split(
                dataframe, test_size=self.data_ingestion_config.train_test_split_ratio
            )
            logging.info("Train Test Split Completed.")

            dir_path = os.path.dirname(self.data_ingestion_config.training_file_path)
            os.makedirs(dir_path, exist_ok=True)
            logging.info("Exporting Train and Test File path")
            train_set.to_csv(
                self.data_ingestion_config.training_file_path, index=False, header=True
            )
            test_set.to_csv(
                self.data_ingestion_config.testing_file_path, index=False, header=True
            )
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def initiate_data_ingestion(self):
        try:
            dataframe = self.export_collection_as_dataframe()
            dataframe = self.export_data_into_feature_store(dataframe)
            self.split_data_into_train_test(dataframe)
            data_ingestion_artifact = DataIngestionArtifact(
                training_file_path=self.data_ingestion_config.training_file_path,
                testing_file_path=self.data_ingestion_config.testing_file_path,
            )
            return data_ingestion_artifact
        except Exception as e:
            raise NetworkSecurityException(e, sys)
