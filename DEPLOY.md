# Deploying to Streamlit Cloud

This guide will help you deploy the WhatsApp Order Processor to Streamlit Cloud.

## Prerequisites
- A GitHub account
- A Streamlit Cloud account (you can sign up with GitHub)

## Steps

1. **Push to GitHub**
   - Ensure all files are committed and pushed to your GitHub repository.
   - The repository should contain:
     - `app.py`: The main Streamlit application
     - `processor.py`: The logic for processing orders
     - `requirements.txt`: List of dependencies

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io/)
   - Click "New app"
   - Select "Use existing repo"
   - **Repository**: Select your GitHub repository
   - **Branch**: `main` (or your working branch)
   - **Main file path**: `app.py`
   - Click "Deploy!"

3. **Wait for Deployment**
   - Streamlit will install the dependencies from `requirements.txt`.
   - Once finished, your app will be live!

## Troubleshooting
- If the app fails to build, check the logs on the Streamlit dashboard.
- Ensure `requirements.txt` lists all libraries used: `streamlit`, `pandas`, `openpyxl`.
