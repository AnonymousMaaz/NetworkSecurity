from networksecurity.entity.config_entity import DataTransformationConfig
from networksecurity.entity.artifact_entity import (
    DataTransformationArtifact,
    DataValidationArtifact,
)
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.constants.training_pipeline import (
    TARGET_COLUMN,
    DATA_TRANSFORMATION_IMPUTER_PARAMS,
)
from networksecurity.utils.save_numpy_array import save_numpy_array_data
from networksecurity.utils.save_pickle_object import save_object

from sklearn.impute import KNNImputer
from sklearn.pipeline import Pipeline

import os
import sys
import pandas as pd
import numpy as np


class DataTransformation:
    def __init__(
        self,
        data_transformation_config: DataTransformationConfig,
        data_validation_artifact: DataValidationArtifact,
    ):
        try:
            self.__data_transformation_config: DataTransformationConfig = (
                data_transformation_config
            )
            self.__data_validation_artifact: DataValidationArtifact = (
                data_validation_artifact
            )
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    @staticmethod
    def __read_data(file_path) -> pd.DataFrame:
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    @classmethod
    def __get_data_transformer_object(cls) -> Pipeline:
        """
        It initializes a KNNImputer object with the parameters specified in the training_pipeline/__init__.py file and returns a Pipeline object with the KNNImputer object as the first step.

        Args:
            cls: DataTransformation
        Returns:
            A Pipeline object
        """
        logging.info("Entered the class method for the Pipeline Object...")
        try:
            imputer: KNNImputer = KNNImputer(**DATA_TRANSFORMATION_IMPUTER_PARAMS)
            logging.info(
                f"Initialized KNN Imputer with the following params: {DATA_TRANSFORMATION_IMPUTER_PARAMS}"
            )
            processor: Pipeline = Pipeline([("imputer", imputer)])
            return processor
        except Exception as e:
            raise NetworkSecurityException(e, sys) from e

    def initiate_data_transformation(self) -> DataTransformationArtifact:
        try:
            logging.info("Initiating the Data Transformation...")
            train_df = DataTransformation.__read_data(
                self.__data_validation_artifact.valid_train_file_path
            )
            test_df = DataTransformation.__read_data(
                self.__data_validation_artifact.valid_test_file_path
            )
            ## ======== Training DataFrame ===========
            input_feature_train_df = train_df.drop(columns=[TARGET_COLUMN], axis=1)
            target_feature_train_df = train_df[TARGET_COLUMN]

            target_feature_train_df = target_feature_train_df.replace(-1, 0)

            ## ============= Testing DataFrame ===================
            input_feature_test_df = test_df.drop(columns=[TARGET_COLUMN], axis=1)
            target_feature_test_df = test_df[TARGET_COLUMN]
            target_feature_test_df = target_feature_test_df.replace(-1, 0)

            ## Applying the Imputer
            imputer_object = self.__get_data_transformer_object()
            transformed_input_train_feature = imputer_object.fit_transform(
                input_feature_train_df
            )
            transformed_input_test_feature = imputer_object.transform(
                input_feature_test_df
            )
            train_arr = np.c_[
                transformed_input_train_feature, np.array(target_feature_train_df)
            ]
            test_arr = np.c_[
                transformed_input_test_feature, np.array(target_feature_test_df)
            ]
            logging.info("Initializing the save sequence...")
            save_numpy_array_data(
                self.__data_transformation_config.transformed_train_file_path,
                array=train_arr,
            )
            save_numpy_array_data(
                self.__data_transformation_config.transformed_test_file_path,
                array=test_arr,
            )

            save_object(
                self.__data_transformation_config.transformed_object_file_path,
                imputer_object,
            )
            logging.info("Save Sequence Completed Successfully...")
            logging.info("Packing the Data Transformation Artifacts...")
            data_transformation_artifact = DataTransformationArtifact(
                transformed_object_file_path=self.__data_transformation_config.transformed_object_file_path,
                transformed_train_file_path=self.__data_transformation_config.transformed_train_file_path,
                transformed_test_file_path=self.__data_transformation_config.transformed_test_file_path,
            )
            return data_transformation_artifact

        except Exception as e:
            raise NetworkSecurityException(e, sys)
