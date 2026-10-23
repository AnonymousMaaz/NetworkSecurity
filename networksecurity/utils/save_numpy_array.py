import numpy as np
import sys
import os

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging


def save_numpy_array_data(file_path: str, array: np.array) -> None:
    """
    Save numpy array data to a file.
    file_path: str = Location of the file to save.
    array: np.array = Numpy array to be saved
    """
    try:
        logging.info("Initializing: Saving the Numpy Array...")
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path, exist_ok=True)
        with open(file_path, "wb") as file_obj:
            np.save(file_obj, array)
            file_obj.close()
        logging.info(f"Saved the Numpy array at:{os.path.abspath(file_path)}")
    except Exception as e:
        raise NetworkSecurityException(e, sys) from e


def load_numpy_array_data(file_path: str) -> np.array:
    """
    Loads the numpy array from a given file path.
    """
    try:
        logging.info("Initializing: Loading the Numpy Array...")
        if not os.path.exists(file_path):
            raise Exception(f"The file at {file_path} does not exists.")
        with open(file_path, "rb") as file_obj:
            return np.load(file_obj)
    except Exception as e:
        raise NetworkSecurityException
