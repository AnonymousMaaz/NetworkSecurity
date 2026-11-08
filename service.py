import csv
import io
import logging
import pickle
from pathlib import Path

import bentoml
import numpy as np
import pandas as pd
from bentoml.exceptions import InternalServerError, InvalidArgument
from frontend import web_app

BASE_DIR = Path(__file__).resolve().parent
MAX_BYTES = 2 * 1024 * 1024
MAX_ROWS = 5000

logger = logging.getLogger(__name__)

TERNARY_FEATURES = {
    "URL_Length",
    "having_Sub_Domain",
    "SSLfinal_State",
    "URL_of_Anchor",
    "Links_in_tags",
    "SFH",
    "web_traffic",
    "Links_pointing_to_page",
}


@bentoml.service(traffic={"timeout": 60})
@bentoml.asgi_app(web_app, path="/ui")
class NetworkSecurityService:
    def __init__(self):
        with (BASE_DIR / "final" / "preprocessor.pkl").open("rb") as file:
            self.preprocessor = pickle.load(file)

        with (BASE_DIR / "final" / "model.pkl").open("rb") as file:
            self.model = pickle.load(file=file)

        self.features = list(self.preprocessor.feature_names_in_)

        if len(self.features) != 30:
            raise RuntimeError("Expected a preprocessor with 30 features.")
        if set(self.model.classes_) != {0, 1}:
            raise RuntimeError("Expected model classes 0 and 1.")

    @bentoml.api
    def input_schema(self) -> dict:
        return {
            "features": self.features,
            "max_rows": MAX_ROWS,
            "max_bytes": MAX_BYTES,
            "model": type(self.model).__name__,
        }

    @bentoml.api
    def predict(self, csv_text: str) -> dict:
        if len(csv_text.encode("utf-8")) > MAX_BYTES:
            raise InvalidArgument("CSV content must be 2 MiB or smaller.")

        csv_text = csv_text.removeprefix("\ufeff")

        try:
            reader = csv.reader(io.StringIO(csv_text), strict=True)
            header = next(reader, [])

            if not header:
                raise InvalidArgument("The CSV is empty.")

            if len(header) != len(set(header)):
                raise InvalidArgument("CSV column names must be unique.")

            row_count = 0

            for row in reader:
                if not row:
                    continue

                if len(row) != len(header):
                    raise InvalidArgument(
                        "Every row must have the same number of columns as the header."
                    )

                row_count += 1

                if row_count > MAX_ROWS:
                    raise InvalidArgument("Upload at most 5,000 rows.")

            frame = pd.read_csv(io.StringIO(csv_text))

        except (csv.Error, ValueError, pd.errors.ParserError) as error:
            raise InvalidArgument("The CSV could not be parsed.") from error

        if frame.empty:
            raise InvalidArgument("The CSV needs at least one data row.")

        # The repository dataset includes Result. It is never a model input.
        frame = frame.drop(columns=["Result"], errors="ignore")

        missing = sorted(set(self.features) - set(frame.columns))
        unexpected = sorted(set(frame.columns) - set(self.features))

        if missing or unexpected:
            messages = []

            if missing:
                messages.append("Missing columns: " + ", ".join(missing))

            if unexpected:
                messages.append("Unexpected columns: " + ", ".join(unexpected))

            raise InvalidArgument(" | ".join(messages))

        # Always restore the feature order used during training.
        frame = frame.loc[:, self.features]

        try:
            frame = frame.apply(pd.to_numeric, errors="raise")
        except (ValueError, TypeError) as error:
            raise InvalidArgument("All feature values must be numeric.") from error

        invalid_columns = []

        for column in self.features:
            if column == "Redirect":
                allowed_values = [0, 1]
            elif column in TERNARY_FEATURES:
                allowed_values = [-1, 0, 1]
            else:
                allowed_values = [-1, 1]

            if not frame[column].isin(allowed_values).all():
                invalid_columns.append(column)

        if invalid_columns:
            raise InvalidArgument(
                "Missing or invalid encoded values in: " + ", ".join(invalid_columns)
            )

        try:
            transformed = self.preprocessor.transform(frame)
            predictions = np.asarray(self.model.predict(transformed))

            if not np.isin(predictions, [0, 1]).all():
                raise RuntimeError("Unexpected prediction classes.")

        except Exception as error:
            logger.exception("Model prediction failed")

            raise InternalServerError(
                "Prediction failed. Check the server log."
            ) from error

        records = frame.astype(int).to_dict(orient="records")

        for position, (record, prediction) in enumerate(
            zip(records, predictions),
            start=1,
        ):
            record["row_number"] = position
            record["prediction"] = int(prediction)

        return {
            "total": len(records),
            "class_0": int((predictions == 0).sum()),
            "class_1": int((predictions == 1).sum()),
            "columns": ["row_number", "prediction"] + self.features,
            "rows": records,
        }
