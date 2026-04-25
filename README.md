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
3. Configure email credentials:
   - **For deployment**: Set `EMAIL_SENDER` and `EMAIL_PASSWORD` in Streamlit secrets (via the Streamlit Cloud dashboard).
   - **For local testing**: Create a `.streamlit/secrets.toml` file in the project root with your email credentials.

   Example `.streamlit/secrets.toml` file:
   ```toml
   [general]
   EMAIL_SENDER = "your-email@gmail.com"
   EMAIL_PASSWORD = "your-app-password"
   ```
4. Generate a sample dataset:
   ```bash
   python data/generate_sample_data.py
   ```
4. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

## Database Management

### Preventing Duplicate Entries

The system now automatically prevents duplicate submissions by checking for existing email addresses before saving. If an email exists, it updates the existing record instead of creating a new one.

### Cleaning Up Existing Duplicates

If you have existing duplicate entries in your database, use one of the cleanup methods below:

#### Option 1: Python Script (Recommended)
```bash
python cleanup_duplicates.py
```
This interactive script will:
- Show you how many duplicates exist
- Ask for confirmation before deleting
- Remove all duplicates, keeping only the most recent entry per email
- Show before/after statistics

#### Option 2: SQL Script
Run the queries in `cleanup_duplicates.sql` in your SQLite database:
```sql
-- Check duplicates
SELECT email, COUNT(*) as duplicate_count
FROM all_submissions
GROUP BY email
HAVING COUNT(*) > 1;

-- Remove duplicates (keeping most recent)
DELETE FROM all_submissions
WHERE id NOT IN (
    SELECT MAX(id)
    FROM all_submissions
    GROUP BY email
);
```

### Database Schema

The `all_submissions` table includes a UNIQUE constraint on the email column to prevent future duplicates.

Then open `http://localhost:8501` in your browser.

## Notes

- The baseline model uses TF-IDF + cosine similarity.
- The advanced model uses a transformer-based embedding model from `sentence-transformers`.
- Evaluation is based on precision, recall, and F1-score.

from datetime import datetime, timedelta

def style_scores_table(df: pd.DataFrame) -> "pd.io.formats.style.Styler":
