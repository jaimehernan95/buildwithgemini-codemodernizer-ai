# RUNBOOK

## 1. Local Environment Setup

Clone the repository and set up a Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Automated Testing

Verify the multi-agent pipeline and codebase integrity by running the test suite:
```bash
PYTHONPATH=. pytest tests/
```

## 3. Local Preview

Start the application locally on port 8080:
```bash
uvicorn app.main:app --port 8080
```
Then navigate to `http://127.0.0.1:8080` (or your configured port proxy) to view the dashboard and run scans.

## 4. Cloud Run Deployment

Deploy the application to Google Cloud Run natively using the gcloud CLI. This builds the Docker image remotely and deploys the service.
```bash
gcloud run deploy codemodernizer-ai --source . --region us-east1 --allow-unauthenticated
```
