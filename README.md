# NetworkSecurity

A machine learning project for classifying website phishing features, with a training pipeline and a browser-based prediction workspace.

The application accepts a CSV of encoded website attributes, validates the input, and returns a prediction for each row. BentoML serves the model API, while a mounted FastAPI application provides the interface.

## Preview

The workspace includes:

- CSV upload through a file picker or drag and drop
- Validation for column names and encoded feature values
- Prediction counts for each output class
- A paginated results table with class filtering
- CSV export of the complete prediction batch
- A responsive charcoal and teal interface

The model works with **extracted website features**. It does not accept a URL and scan the corresponding website.

## How it works

### Prediction

```text
CSV input
    │
    ▼
Column and value validation
    │
    ▼
Saved preprocessing pipeline
    │
    ▼
Saved classifier
    │
    ▼
Predictions → results table → CSV export
```

The preprocessor and classifier are loaded when the serving worker starts. Prediction does not require a MongoDB connection, DagsHub authentication, or a training run.

### Training

```text
MongoDB
    │
    ▼
Data ingestion and train/test split
    │
    ▼
Schema validation and distribution checks
    │
    ▼
KNN imputation
    │
    ▼
Model selection and hyperparameter search
    │
    ▼
MLflow tracking through DagsHub
    │
    ▼
Saved artifacts and S3 synchronization
```

The training code compares Random Forest, Decision Tree, Gradient Boosting, Logistic Regression, AdaBoost, and K-Nearest Neighbors classifiers using cross-validation accuracy.

## Built with

| Area | Tools |
| --- | --- |
| Model development | scikit-learn, pandas, NumPy |
| Prediction API | BentoML |
| Web application | FastAPI, Jinja2 |
| Frontend | HTML, CSS, JavaScript |
| Training data storage | MongoDB |
| Experiment tracking | MLflow, DagsHub |
| Artifact storage | Amazon S3 |
| Deployment configuration | Docker, GitHub Actions, Amazon ECR |

## Run locally

Run the following commands from the repository root using your Python environment.

### 1. Install serving dependencies

```bash
python -m pip install "bentoml>=1.2,<2" fastapi jinja2 pandas numpy "scikit-learn==1.7.2"
```

The included model artifacts were created with scikit-learn 1.7.2. Keep the serving environment compatible with the environment used to train and serialize them.

### 2. Check the model files

The application expects:

```text
final/
├── model.pkl
└── preprocessor.pkl
```

Use artifacts produced by a trusted training process.

### 3. Start the application

```bash
bentoml serve service:NetworkSecurityService --port 3000
```

Open:

- **Workspace:** http://localhost:3000/ui/
- **API reference:** http://localhost:3000/

The frontend and prediction API run on the same server.

## Input format

Each CSV row represents one observation with 30 encoded features.

Requirements:

- UTF-8 CSV with a header row
- Between 1 and 5,000 data rows
- CSV content no larger than 2 MiB
- All expected feature names, without duplicates
- Numeric values using the feature’s allowed encoding

Column order may vary. The service restores the order recorded by the fitted preprocessor.

The optional `Result` column is removed before prediction. Other unexpected columns are rejected.

### Feature names

```text
having_IP_Address
URL_Length
Shortining_Service
having_At_Symbol
double_slash_redirecting
Prefix_Suffix
having_Sub_Domain
SSLfinal_State
Domain_registeration_length
Favicon
port
HTTPS_token
Request_URL
URL_of_Anchor
Links_in_tags
SFH
Submitting_to_email
Abnormal_URL
Redirect
on_mouseover
RightClick
popUpWidnow
Iframe
age_of_domain
DNSRecord
web_traffic
Page_Rank
Google_Index
Links_pointing_to_page
Statistical_report
```

Names retain the spelling used in the training data. Download a header-only template from the workspace to avoid typing them manually.

### Output classes

The training pipeline applies this target mapping:

| Original target | Model output |
| --- | --- |
| `-1` | `0` |
| `1` | `1` |

The interface displays these as **Class 0** and **Class 1**. Confirm the source dataset’s label definitions before interpreting them as security verdicts.

## API usage

### Get the input schema

```bash
curl -X POST http://localhost:3000/input_schema \
  -H "Content-Type: application/json" \
  -d '{}'
```

The response includes feature names, request limits, and the classifier type.

### Predict from a CSV

```python
from pathlib import Path

import requests

csv_text = Path("sample-input.csv").read_text(
    encoding="utf-8-sig"
)

response = requests.post(
    "http://localhost:3000/predict",
    json={"csv_text": csv_text},
    timeout=90,
)

response.raise_for_status()
result = response.json()

print("Observations:", result["total"])
print("Class 0:", result["class_0"])
print("Class 1:", result["class_1"])
```

Install `requests` if you use this example:

```bash
python -m pip install requests
```

The prediction response contains:

| Field | Description |
| --- | --- |
| `total` | Number of observations |
| `class_0` | Number of class 0 predictions |
| `class_1` | Number of class 1 predictions |
| `columns` | Ordered output column names |
| `rows` | Feature values, row numbers, and predictions |

## Train a model

Training is separate from serving.

Install the training dependencies:

```bash
python -m pip install -r requirements.txt "scikit-learn==1.7.2"
```

Configure these environment variables:

```dotenv
MONGO_CLIENT_URI=<your-mongodb-connection-string>
MONGODB_DATABASE=<your-database-name>
MONGODB_COLLECTION=<your-collection-name>
DAGSHUB_USER_TOKEN=<your-dagshub-token>
```

The current training implementation also uses:

- The DagsHub repository configured in `model_trainer.py`
- The S3 bucket configured in the training constants
- AWS CLI credentials with permission to synchronize artifacts

Update those settings for your own accounts before running training.

To insert the local dataset into MongoDB:

```bash
python push_data.py
```

This inserts records into the configured collection. Repeating it can create duplicate records.

Start training:

```bash
python main.py
```

The pipeline writes timestamped training artifacts, saves the serving files under `final/`, and synchronizes the configured directories to S3.

Keep credentials out of version control.

## Repository structure

```text
.
├── service.py                  # BentoML prediction service
├── frontend.py                 # Mounted FastAPI frontend
├── app.py                      # Earlier FastAPI serving implementation
├── main.py                     # Training entry point
├── push_data.py                # Local CSV ingestion into MongoDB
├── networksecurity/
│   ├── components/             # Ingestion, validation, transformation, training
│   ├── pipeline/               # Training orchestration
│   ├── entity/                 # Configuration and artifact definitions
│   ├── constants/              # Pipeline settings
│   ├── cloud/                  # S3 synchronization
│   ├── utils/                  # Serialization and model utilities
│   ├── logging/
│   └── exception/
├── data_schema/
│   └── schema.yaml
├── Network_Data/
│   └── phisingData.csv
├── final/
│   ├── model.pkl
│   └── preprocessor.pkl
├── templates/
│   └── index.html
├── static/
│   ├── style.css
│   └── app.js
├── .github/workflows/
├── Dockerfile
└── requirements.txt
```

## Evaluation notes

The local dataset contains 11,055 observations and 30 input features. It also contains repeated observations.

The current training pipeline uses a row-level random train/test split. Identical observations can therefore appear in both partitions, making holdout scores optimistic. A stronger evaluation should group repeated feature rows before splitting and measure performance on independent data.

Reported precision, recall, and F1 currently use class 1 as the positive class.

## Limitations

- Feature extraction from live websites is not implemented.
- Predictions depend on the quality and encoding of the supplied features.
- Model outputs are not guarantees that a website is safe or malicious.
- The serving application does not include authentication or persistent prediction history.
- The existing Docker and GitHub Actions configuration targets the earlier application entry point and needs updating before deploying the BentoML version.

## Author

Maaz Khan