import sys, os
import pickle

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging


def save_object(file_path: str, obj: object) -> None:
    """
    Saves a pickle object to a given file.
    """
    try:
        logging.info("Initializing: Saving the Pickle Object...")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as file_obj:
            pickle.dump(obj, file_obj)
            file_obj.close()
        logging.info(f"Saved the pickle object to: {os.path.abspath(file_path)}")
    except Exception as e:
        raise NetworkSecurityException(e, sys) from e


def load_object(
    file_path: str,
) -> object:
    """
    Loads the pickle object from a given file
    """
    try:
        logging.info("Initializing: Reading the Pickle Object...")
        if not os.path.exists(file_path):
            raise Exception(f"The file: {file_path} does not exists.")
        with open(file_path, "rb") as file_obj:
            return pickle.load(file_obj)
    except Exception as e:
        raise NetworkSecurityException(e, sys) from e
