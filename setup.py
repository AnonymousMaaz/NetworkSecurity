from setuptools import find_packages, setup
from pathlib import Path
from typing import List

import os

HYPHEN_E_DOT = "-e ."


def get_requirements(path: str) -> List[str]:
    """
    This function will return list of requirements
    """

    try:
        if os.path.exists(path):
            with open(path, "r") as file:
                content = file.readlines()

            content = [requirement.strip() for requirement in content]

            if HYPHEN_E_DOT in content:
                content.remove(HYPHEN_E_DOT)

            return content

    except FileNotFoundError:
        raise FileNotFoundError(f"The requirements file at {path} does not exist")


setup(
    name="Network Security",
    version="0.0.1",
    author="Maaz Khan",
    author_email="maazkhan01.work@gmail.com",
    packages=find_packages(),
    install_requires=get_requirements("requirements.txt"),
)
