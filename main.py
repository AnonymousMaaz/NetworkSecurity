from networksecurity.components.data_ingestion import DataIngestionConfig, DataIngestion
from networksecurity.entity.config_entity import (
    TraningPipelineConfig,
    DataValidationConfig,
)
from networksecurity.components.data_validation import DataValidation

if __name__ == "__main__":
    training_pipeline_config = TraningPipelineConfig()
    data_ingestion_config = DataIngestionConfig(training_pipeline_config)
    data_ingestion = DataIngestion(data_ingestion_config)

    data_ingestion_artifact = data_ingestion.initiate_data_ingestion()

    data_validation_config = DataValidationConfig(
        training_pipeline_config=training_pipeline_config
    )
    data_validation = DataValidation(
        data_ingestion_artifact=data_ingestion_artifact,
        data_validation_config=data_validation_config,
    )

    data_validation_artifact = data_validation.initiate_data_validation()
