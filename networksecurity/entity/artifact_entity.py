from dataclasses import dataclass


@dataclass
class DataIngestionArtifact:
    training_file_path: str = None
    testing_file_path: str = None


@dataclass
class DataValidationArtifact:
    validation_status: bool
    valid_train_file_path: str | None = None
    valid_test_file_path: str | None = None
    invalid_train_file_path: str | None = None
    invalid_test_file_path: str | None = None
    drift_report_file_path: str = None


@dataclass
class DataTransformationArtifact:
    transformed_object_file_path: str
    transformed_train_file_path: str
    transformed_test_file_path: str


@dataclass
class ClassificationMetricArtifact:
    f1_score: float
    precision_score: float
    recall_score: float


@dataclass
class ModelTrainerArtifact:
    trained_model_file_path: str
    train_metric_artifact: ClassificationMetricArtifact
    test_metric_artifact: ClassificationMetricArtifact
