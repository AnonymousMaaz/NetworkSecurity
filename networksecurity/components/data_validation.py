from networksecurity.entity.artifact_entity import (
    DataIngestionArtifact,
    DataValidationArtifact,
)
from networksecurity.entity.config_entity import DataValidationConfig
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.constants.training_pipeline import SCHEMA_FILE_PATH
from networksecurity.utils.read_write_yaml import read_yaml_file, write_yaml_file
from scipy.stats import ks_2samp


import pandas as pd
import os, sys
import yaml


class DataValidation:
    def __init__(
        self,
        data_ingestion_artifact: DataIngestionArtifact,
        data_validation_config: DataValidationConfig,
    ):
        try:
            self.__data_ingestion_artifact = data_ingestion_artifact
            self.__data_validation_config = data_validation_config
            self.__schema_config = read_yaml_file(SCHEMA_FILE_PATH)
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    @staticmethod
    def read_data(file_path) -> pd.DataFrame:
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def _validate_number_of_columns(self, dataframe: pd.DataFrame) -> bool:
        try:
            number_of_columns = len(self.__schema_config["columns"])
            logging.info(f"Required Number of Columns: {number_of_columns}")
            logging.info(f"Data Frame has columns: {len(dataframe.columns.to_list())}")
            if number_of_columns == len(dataframe.columns):
                return True
            return False

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def _validate_data_types(self, dataframe: pd.DataFrame) -> bool:
        try:
            schema_columns = self.__schema_config["columns"]

            if isinstance(schema_columns, list):
                expected_dtypes = {}
                for column_info in schema_columns:
                    expected_dtypes.update(column_info)
            else:
                expected_dtypes = schema_columns

            errors = []

            for column, expected_dtype in expected_dtypes.items():
                if column not in dataframe.columns:
                    errors.append(f"Missing Column: {column}")
                    continue
                actual_dtype = str(dataframe[column].dtype)

                if actual_dtype != expected_dtype:
                    errors.append(
                        f"Column '{column}': expected {expected_dtype}, "
                        f"but got {actual_dtype}"
                    )
            if errors:
                for error in errors:
                    logging.error(error)
                return False
            return True
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def _detect_dataset_drift(self, base_df, current_df, threshold=0.05) -> bool:
        try:
            status = True
            report = {}
            for column in base_df.columns:
                d1 = base_df[column]
                d2 = current_df[column]

                is_same_dist = ks_2samp(d1, d2)

                if threshold <= is_same_dist.pvalue:
                    is_found = False
                else:
                    is_found = True
                    status = False

                report.update(
                    {
                        column: {
                            "p_value": float(is_same_dist.pvalue),
                            "drift_status": is_found,
                        }
                    }
                )

            drift_report_file_path = (
                self.__data_validation_config.drift_report_file_path
            )
            write_yaml_file(drift_report_file_path, report)
            return status

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def initiate_data_validation(self) -> DataValidationArtifact:
        try:
            train_file_path = self.__data_ingestion_artifact.training_file_path
            test_file_path = self.__data_ingestion_artifact.testing_file_path

            train_df = DataValidation.read_data(train_file_path)
            test_df = DataValidation.read_data(test_file_path)

            error_message = []
            # Validating the Number the Columns
            logging.info(" ==== Validation Started for 'Number of Columns' ====")
            logging.info("Training File Validation Started")
            status = self._validate_number_of_columns(train_df)

            if not status:
                error_message.append(
                    "Train dataframe does not contain the required number of columns."
                )

            logging.info("Test File Validation Started")
            status = self._validate_number_of_columns(test_df)
            if not status:
                error_message.append(
                    "Test dataframe does not contain the required number of columns."
                )

            # Validating for columns and dtypes
            logging.info(
                "==== Validation Started for 'Missing Columns and DataType Checking'"
            )
            if not self._validate_data_types(train_df):
                error_message.append(
                    "Training dataframe has incorrect column data types or missing columns."
                )
            if not self._validate_data_types(test_df):
                error_message.append(
                    "Test dataframe has incorrect column data types or missing columns."
                )
            if error_message:
                raise ValueError("\n".join(error_message))

            logging.info(" ==== Checking Data Drift ====")
            status = self._detect_dataset_drift(base_df=train_df, current_df=test_df)

            if status:
                dir_path = os.path.dirname(
                    self.__data_validation_config.valid_train_file_path
                )
                os.makedirs(dir_path, exist_ok=True)
                train_df.to_csv(
                    self.__data_validation_config.valid_train_file_path,
                    index=False,
                    header=True,
                )
                test_df.to_csv(
                    self.__data_validation_config.valid_test_file_path,
                    index=False,
                    header=True,
                )
                return DataValidationArtifact(
                    validation_status=status,
                    valid_train_file_path=self.__data_validation_config.valid_train_file_path,
                    valid_test_file_path=self.__data_validation_config.valid_test_file_path,
                    invalid_train_file_path=None,
                    invalid_test_file_path=None,
                    drift_report_file_path=self.__data_validation_config.drift_report_file_path,
                )
            else:
                dir_path = os.path.dirname(
                    self.__data_validation_config.invalid_train_file_path
                )
                os.makedirs(dir_path, exist_ok=True)
                train_df.to_csv(
                    self.__data_validation_config.invalid_train_file_path,
                    index=False,
                    header=True,
                )
                test_df.to_csv(
                    self.__data_validation_config.invalid_test_file_path,
                    index=False,
                    header=True,
                )
                return DataValidationArtifact(
                    validation_status=status,
                    valid_train_file_path=None,
                    valid_test_file_path=None,
                    invalid_train_file_path=self.__data_validation_config.invalid_train_file_path,
                    invalid_test_file_path=self.__data_validation_config.invalid_test_file_path,
                    drift_report_file_path=self.__data_validation_config.drift_report_file_path,
                )

        except Exception as e:
            raise NetworkSecurityException(e, sys)
