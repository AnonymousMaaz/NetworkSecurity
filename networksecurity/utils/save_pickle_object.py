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
