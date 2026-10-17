from networksecurity.components.data_ingestion import DataIngestionConfig, DataIngestion
from networksecurity.entity.config_entity import TraningPipelineConfig

if __name__ == "__main__":
    training_pipeline_config = TraningPipelineConfig()
    data_ingestion_config = DataIngestionConfig(training_pipeline_config)
    data_ingestion = DataIngestion(data_ingestion_config)

    data_ingestion_artifact = data_ingestion.initiate_data_ingestion()
