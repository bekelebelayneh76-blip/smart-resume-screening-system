import csv
import random
import os
import re
import string
from io import StringIO

import pandas as pd
from PyPDF2 import PdfReader
import nltk
from nltk.corpus import stopwords

# Download stopwords if not present
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

STOP_WORDS = set(stopwords.words('english'))


def generate_sample_data(num_samples=100, output_path="data/sample_resumes.csv"):
    os.makedirs("data", exist_ok=True)
    resumes = ["Python developer with ML experience", "Marketing manager SEO", "JS React Developer"]
    jobs = ["Seeking Python ML engineer", "Marketing specialist", "Frontend dev"]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["resume_text", "job_description", "label"])
        writer.writeheader()
        for _ in range(num_samples):
            writer.writerow({
                "resume_text": random.choice(resumes),
                "job_description": random.choice(jobs),
                "label": random.choice([0, 1])
            })
    print(f"Success: Created {output_path}")


def extract_text_from_file(uploaded_file):
    """Extract text from uploaded PDF or TXT file."""
    if uploaded_file.type == "application/pdf":
        pdf_reader = PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    elif uploaded_file.type == "text/plain":
        return StringIO(uploaded_file.getvalue().decode("utf-8")).read()
    else:
        raise ValueError("Unsupported file type")


def clean_text(text):
    """Clean text by removing extra whitespace."""
    return re.sub(r'\s+', ' ', text).strip()


def preprocess_text(text):
    """Preprocess text: lowercase, remove punctuation, remove stopwords."""
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    words = text.split()
    words = [word for word in words if word not in STOP_WORDS]
    text = ' '.join(words)
    return clean_text(text)


def load_dataset(path):
    """Load dataset from CSV."""
    return pd.read_csv(path)


def preprocess_dataset(df):
    """Preprocess dataset by cleaning and preprocessing text columns."""
    df = df.copy()
    # Use 'Resume_Text' if available, else 'resume_text'
    resume_col = 'Resume_Text' if 'Resume_Text' in df.columns else 'resume_text'
    df['resume_text_clean'] = df[resume_col].apply(preprocess_text)
    # For job_description, if not present, skip or use empty
    if 'job_description' in df.columns:
        df['job_description_clean'] = df['job_description'].apply(preprocess_text)
    else:
        df['job_description_clean'] = ''
    return df


if __name__ == "__main__":
    generate_sample_data()