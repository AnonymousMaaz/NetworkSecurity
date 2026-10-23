import os
import sys

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import accuracy_score


def evaluate_models(X_train, Y_train, models, params):
    try:
        logging.info(
            "Initializing Randomized Search Model Training and HyperParameter Tuning..."
        )

        model_report = {}
        best_estimator = {}

        for name, model in models.items():
            logging.info(f"Training and Tuning: {name}")

            search = RandomizedSearchCV(
                estimator=model,
                param_distributions=params[name],
                n_iter=20,
                scoring="accuracy",
                cv=3,
                n_jobs=-1,
                refit=True,
                error_score="raise",
            )

            search.fit(X_train, Y_train)

            model_report[name] = search.best_score_
            best_estimator[name] = search.best_estimator_

            logging.info(f"{name} best CV accuracy: {search.best_score_}")
            logging.info(f"{name} best parameters: {search.best_params_}")

        return model_report, best_estimator

    except Exception as e:
        raise NetworkSecurityException(e, sys) from e
