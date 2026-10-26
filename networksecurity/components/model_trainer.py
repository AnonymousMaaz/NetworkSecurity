from networksecurity.entity.config_entity import ModelTrainerConfig
from networksecurity.entity.artifact_entity import (
    DataTransformationArtifact,
    ModelTrainerArtifact,
)
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

from networksecurity.utils.save_pickle_object import save_object, load_object
from networksecurity.utils.save_numpy_array import (
    load_numpy_array_data,
)
from networksecurity.utils.ml_utils.metric.classification_metric import (
    get_classification_score,
)
from networksecurity.utils.ml_utils.model.estimator import NetworkModel
from networksecurity.utils.ml_utils.model.model_train_and_evaluation import (
    evaluate_models,
)

from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (
    AdaBoostClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier,
)
from scipy.stats import loguniform

import os
import sys
import dagshub
import mlflow

try:
    dagshub.init(repo_owner="maazkhan01.work", repo_name="NetworkSecurity", mlflow=True)
except Exception as e:
    raise NetworkSecurityException(e, sys)


class ModelTrainer:
    def __init__(
        self,
        model_trainer_config: ModelTrainerConfig,
        data_transformation_artifact: DataTransformationArtifact,
    ):
        self.model_trainer_config = model_trainer_config
        self.data_transformation_artifact = data_transformation_artifact

    def __track_mlflow(self, model, model_name, train_metrics, test_metrics):
        """
        Track Classification metrics using MLFLOW

        Args:
            model: Best model found after hyperparamater tuning
            model_name: The best model name.
            train_metrics: classification train artifact generated during the model hyperparamater tuning
            test_metrics: classification test artifact generated during the model hyperparamater tuning and testing
        """
        # For Local Saving Only (Turn of for dagshub)
        # mlflow.set_tracking_uri("sqlite:///mlflow.db")
        mlflow.set_experiment("NetworkSecurity")

        print("MLflow tracking URI:", mlflow.get_tracking_uri())
        with mlflow.start_run():

            mlflow.log_param("model_name", model_name)

            # Log the train metrics
            mlflow.log_metric("train_f1_score", train_metrics.f1_score)
            mlflow.log_metric("train_precision_score", train_metrics.precision_score)
            mlflow.log_metric("train_recall_score", train_metrics.recall_score)

            # Log the test metrics
            mlflow.log_metric("test_f1_score", test_metrics.f1_score)
            mlflow.log_metric("test_precision_score", test_metrics.precision_score)
            mlflow.log_metric("test_recall_score", test_metrics.recall_score)

            # Save the trained model as a MLFLOW artifact
            mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path="model",
                serialization_format="pickle",
            )

    def ___train_and_evaluate_model(
        self, X_train, Y_train, X_test, Y_test
    ) -> ModelTrainerArtifact:
        models = {
            "Random Forest": RandomForestClassifier(verbose=1),
            "Decision Tree": DecisionTreeClassifier(),
            "Gradient Boosting": GradientBoostingClassifier(verbose=1),
            "Logistic Regression": LogisticRegression(verbose=1, max_iter=2000),
            "AdaBoost Classifier": AdaBoostClassifier(),
            "K-Neighbors Classifier": KNeighborsClassifier(),
        }

        params = {
            "Random Forest": {
                "n_estimators": [50, 100, 200, 300, 500],
                "criterion": ["gini", "entropy"],
                "min_samples_split": [2, 4, 6, 8, 10],
                "min_samples_leaf": [1, 2, 3, 4, 5],
            },
            "Decision Tree": {
                "criterion": ["gini", "entropy", "log_loss"],
                "splitter": ["best", "random"],
                "min_samples_split": [2, 4, 6, 8, 10],
                "min_samples_leaf": [1, 2, 3, 4, 5],
            },
            "Gradient Boosting": {
                "loss": ["log_loss", "exponential"],
                "learning_rate": [0.1, 0.05, 0.1, 0.2],
                "n_estimators": [50, 100, 200, 300],
                "subsample": [0.6, 0.7, 0.8, 0.9, 1.0],
            },
            "Logistic Regression": {
                "penalty": ["l2"],
                "C": loguniform(0.001, 100),
            },
            "AdaBoost Classifier": {
                "n_estimators": [50, 100, 200, 300, 500],
                "learning_rate": [1.0, 0.1, 0.01, 0.001, 2.0, 0.5],
            },
            "K-Neighbors Classifier": {
                "n_neighbors": [3, 5, 7, 9, 11, 15, 21, 31],
                "weights": ["uniform", "distance"],
                "algorithm": ["auto", "ball_tree", "kd_tree"],
            },
        }

        model_report, best_estimator = evaluate_models(X_train, Y_train, models, params)

        best_model_name = max(model_report, key=model_report.get)
        best_model = best_estimator[best_model_name]

        y_train_pred = best_model.predict(X_train)
        y_test_pred = best_model.predict(X_test)

        classification_train_artifact = get_classification_score(Y_train, y_train_pred)
        classification_test_artifact = get_classification_score(Y_test, y_test_pred)

        # MLFLOW Tracking
        self.__track_mlflow(
            best_model,
            best_model_name,
            classification_train_artifact,
            classification_test_artifact,
        )

        preprocessor = load_object(
            file_path=self.data_transformation_artifact.transformed_object_file_path
        )

        model_dir_path = os.path.dirname(
            self.model_trainer_config.trainer_model_file_path
        )
        os.makedirs(model_dir_path, exist_ok=True)

        Network_Model = NetworkModel(preprocessor=preprocessor, model=best_model)
        save_object(
            self.model_trainer_config.trainer_model_file_path, obj=Network_Model
        )
        save_object(file_path="final/model.pkl", obj=best_model)

        model_trainer_artifact = ModelTrainerArtifact(
            trained_model_file_path=self.model_trainer_config.trainer_model_file_path,
            train_metric_artifact=classification_train_artifact,
            test_metric_artifact=classification_test_artifact,
        )
        logging.info(f"Model Trainer Artifact Generated: {model_trainer_artifact}")
        return model_trainer_artifact

    def initiate_model_trainer(self) -> ModelTrainerArtifact:
        try:
            train_file_path = (
                self.data_transformation_artifact.transformed_train_file_path
            )
            test_file_path = (
                self.data_transformation_artifact.transformed_test_file_path
            )

            # Loading the Training Array and Testing Array
            train_arr = load_numpy_array_data(train_file_path)
            test_arr = load_numpy_array_data(test_file_path)

            X_train, Y_train, X_test, Y_test = (
                train_arr[:, :-1],
                train_arr[:, -1],
                test_arr[:, :-1],
                test_arr[:, -1],
            )

            model_trainer_artifact: ModelTrainerArtifact = (
                self.___train_and_evaluate_model(X_train, Y_train, X_test, Y_test)
            )
            return model_trainer_artifact
        except Exception as e:
            raise NetworkSecurityException(e, sys)
