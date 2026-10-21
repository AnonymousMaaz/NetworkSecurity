import yaml
import os
import sys

from networksecurity.exception.exception import NetworkSecurityException


def read_yaml_file(SCHEMA_FILE_PATH):
    with open(SCHEMA_FILE_PATH, "r") as file:
        schema = yaml.safe_load(file)
        file.close()
    return schema


def write_yaml_file(file_path: str, content: object, replace: bool = False) -> None:
    try:
        if replace:
            if os.path.exists(file_path):
                os.remove(file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w") as file:
            yaml.dump(content, file)
    except Exception as e:
        raise NetworkSecurityException(e, sys)
