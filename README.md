# Resume Screening System

A Python-based resume screening project that uses NLP similarity techniques to match resumes with job descriptions.

## Structure

- `data/` - dataset generator and storage
- `src/` - reusable data, modeling, and evaluation modules
- `app.py` - Streamlit interface for resume and job description matching

## Setup

1. Create and activate a Python environment
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure SMTP credentials for email sending:
   - **For deployment**: Set `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_SERVER`, and `SMTP_PORT` in Streamlit secrets (via the Streamlit Cloud dashboard or `secrets.toml`).
   - **For local testing**: Set the environment variables `SMTP_USERNAME` and `SMTP_PASSWORD`, or create a `.env` file in the project root with these values.

   Example `.env` file:
   ```env
   SMTP_USERNAME=your-email@example.com
   SMTP_PASSWORD=your-smtp-password
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   ```
4. Generate a sample dataset:
   ```bash
   python data/generate_sample_data.py
   ```
4. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

## Deployment

This project can be deployed using Docker.

Build the container:
```bash
docker build -t resume-screening-system .
```

Run the app in a container:
```bash
docker run -p 8501:8501 resume-screening-system
```

Then open `http://localhost:8501` in your browser.

## Notes

- The baseline model uses TF-IDF + cosine similarity.
- The advanced model uses a transformer-based embedding model from `sentence-transformers`.
- Evaluation is based on precision, recall, and F1-score.
