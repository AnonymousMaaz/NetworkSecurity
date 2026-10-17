from dataclasses import dataclass


@dataclass
class DataIngestionArtifact:
    training_file_path: str = None
    testing_file_path: str = None
