from networksecurity.components.data_ingestion import DataIngestionConfig, DataIngestion
from networksecurity.entity.config_entity import (
    TraningPipelineConfig,
    DataValidationConfig,
    DataTransformationConfig,
)
from networksecurity.components.data_validation import DataValidation
from networksecurity.components.data_transformation import DataTransformation

if __name__ == "__main__":

    # ================= Training Pipeline =========================
    training_pipeline_config = TraningPipelineConfig()

    # ==================== Data Ingestion ==========================
    data_ingestion_config = DataIngestionConfig(training_pipeline_config)
    data_ingestion = DataIngestion(data_ingestion_config)
    data_ingestion_artifact = data_ingestion.initiate_data_ingestion()

    # ================ Data Validation =============================
    data_validation_config = DataValidationConfig(
        training_pipeline_config=training_pipeline_config
    )
    data_validation = DataValidation(
        data_ingestion_artifact=data_ingestion_artifact,
        data_validation_config=data_validation_config,
    )
    data_validation_artifact = data_validation.initiate_data_validation()

    # ====================== Data Transformation ======================
    data_transformation_config = DataTransformationConfig(
        training_pipeline_config=training_pipeline_config
    )
    data_transformation = DataTransformation(
        data_transformation_config=data_transformation_config,
        data_validation_artifact=data_validation_artifact,
    )
    data_transformation_artifact = data_transformation.initiate_data_transformation()
