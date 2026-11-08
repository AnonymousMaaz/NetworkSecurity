import sys

import pandas as pd
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.utils.ml_utils.model.estimator import NetworkModel
from networksecurity.utils.save_pickle_object import load_object
from starlette.responses import RedirectResponse
from uvicorn import run as app_run

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="./templates")


@app.get("/", tags=["authentication"])
async def index():
    return RedirectResponse(url="/docs")


@app.post("/predict")
async def predict_route(request: Request, file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)
        preprocessor = load_object("final/preprocessor.pkl")
        model = load_object("final/model.pkl")

        network_model = NetworkModel(preprocessor=preprocessor, model=model)

        print(df.iloc[0])

        y_pred = network_model.predict(df)
        print(y_pred)
        df["predicted_column"] = y_pred
        print(df["predicted_column"])

        table_html = df.to_html(classes="table table-striped")

        return templates.TemplateResponse(
            request=request, name="table.html", context={"table": table_html}
        )

    except Exception as e:
        raise NetworkSecurityException(e, sys)


if __name__ == "__main__":
    app_run(app=app, host="0.0.0.0", port=8000)
