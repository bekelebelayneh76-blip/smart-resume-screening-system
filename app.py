import streamlit as st
import sqlite3
from sqlite3 import Error
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import hashlib
import re
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from src.data_utils import extract_text_from_file, preprocess_text
from src.modeling import compute_weighted_score, apply_min_max_scaling
from streamlit.runtime.secrets import StreamlitSecretNotFoundError

# --- Page Configuration ---
st.set_page_config(
    page_title="Resume Screening System",
    page_icon="📄",
    layout="wide",
)

# --- CSS STYLING ---
st.markdown("""
    <style>
    header img { display: none !important; }
    header[data-testid="stHeader"] a[href*="github.com"],
    header[data-testid="stHeader"] a[aria-label*="GitHub"],
    header[data-testid="stHeader"] [data-testid="stToolbarActions"] {
        display: none !important; visibility: hidden !important;
    }
    #MainMenu { visibility: hidden; }
    header[data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
    [data-testid="stHeader"] img { display: none !important; }
    button[aria-label="View profile"], .st-emotion-cache-1vq4p4l { display: none !important; }
    [data-testid="stHeaderActionButton"] { display: none !important; }

    .header { background-color: #1B5E20; color: white; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; width: 100%; position: sticky; top: 0; z-index: 2000; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); }
    .main-content { padding-top: 120px; padding-bottom: 60px; }
    .card { background-color: white; border: 1px solid #e6e9ef; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); padding: 20px; margin-bottom: 20px; }
    .green-text { color: #006400; font-weight: bold; }
    .footer { text-align: center; padding: 10px; background-color: #1E1E1E; color: white; position: fixed; bottom: 0; width: 100%; font-size: 16px; }
    
    /* Stepper UI */
    .stepper { display: flex; justify-content: space-between; align-items: center; margin: 20px 0; }
    .step { display: flex; flex-direction: column; align-items: center; flex: 1; }
    .step-circle { width: 40px; height: 40px; border-radius: 50%; background-color: #e9ecef; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #6c757d; margin-bottom: 5px; }
    .step-circle.active { background-color: #28a745; color: white; }
    .step-circle.completed { background-color: #28a745; color: white; }
    .step-line { height: 2px; background-color: #e9ecef; flex: 1; margin: 0 10px; }
    .step-line.completed { background-color: #28a745; }
    .step-label { font-size: 12px; text-align: center; }
    .skill-badge { display: inline-block; background-color: #006400; color: white; padding: 5px 10px; margin: 2px; border-radius: 15px; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- Email Credentials Setup ---
try:
    EMAIL_SENDER = st.secrets["EMAIL_SENDER"]
    EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
    SMTP_SERVER = st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(st.secrets.get("SMTP_PORT", 465))
except (KeyError, StreamlitSecretNotFoundError):
    EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "")
    EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
    SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 465))

def check_email_config():
    return bool(EMAIL_SENDER and EMAIL_PASSWORD)

# --- SQLite Database Logic ---
def get_sqlite_connection():
    try:
        return sqlite3.connect('resume_system.db')
    except Error as e:
        st.error(f"Database connection error: {e}")
        return None

def init_db():
    connection = get_sqlite_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT, email TEXT UNIQUE, phone TEXT, password TEXT, role TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS all_submissions (id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT, email TEXT UNIQUE, resume_text TEXT, tf_idf_score REAL, transformer_score REAL, final_score REAL, upload_time DATETIME, status TEXT DEFAULT 'Applied')""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS invitation_codes (email TEXT PRIMARY KEY, code TEXT, created_at DATETIME)""")
        
        # Add status column if it doesn't exist for existing databases
        cursor.execute("PRAGMA table_info(all_submissions)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'status' not in columns:
            cursor.execute("ALTER TABLE all_submissions ADD COLUMN status TEXT DEFAULT 'Applied'")
        
        connection.commit()
        connection.close()

def save_submission(name, email, resume_text, tf_idf=None, transformer=None, final=None, status=None):
    connection = get_sqlite_connection()
    if connection:
        cursor = connection.cursor()
        try:
            # CLEANING LOGIC (isprintable)
            clean_resume = "".join(c for c in resume_text if c.isprintable() or c.isspace())
            clean_resume = clean_resume.encode('utf-8', errors='replace').decode('utf-8')
            
            email = email.lower().strip()
            
            if status is None:
                existing = find_submission_by_email(email)
                status = existing[8] if (existing and len(existing) > 8) else 'Applied'

            cursor.execute("""
                INSERT INTO all_submissions (full_name, email, resume_text, tf_idf_score, transformer_score, final_score, upload_time, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET 
                resume_text=excluded.resume_text, tf_idf_score=excluded.tf_idf_score, 
                transformer_score=excluded.transformer_score, final_score=excluded.final_score, 
                upload_time=excluded.upload_time, status=COALESCE(excluded.status, all_submissions.status)
            """, (name, email, clean_resume, tf_idf, transformer, final, datetime.now(), status))
            connection.commit()
        except Exception:
            st.error("❌ ሲቪውን ማስቀመጥ አልተቻለም። ፋይሉ ውስጥ ያሉ አንዳንድ ምልክቶች (Symbols) አልተነበቡም። እባክዎ ፋይሉን አስተካክለው በድጋሚ ይሞክሩ።")
        finally:
            connection.close()

def update_candidate_status(email, status):
    connection = get_sqlite_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("UPDATE all_submissions SET status = ? WHERE lower(email) = lower(?)", (status, email.strip()))
        connection.commit()
        connection.close()

def find_submission_by_email(email):
    connection = get_sqlite_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM all_submissions WHERE lower(email) = lower(?) LIMIT 1", (email.strip(),))
        result = cursor.fetchone()
        connection.close()
        return result
    return None

def load_submissions():
    connection = get_sqlite_connection()
    if connection:
        df = pd.read_sql_query("SELECT full_name AS Name, email AS Email, resume_text AS Resume_Text, tf_idf_score, transformer_score, final_score, upload_time, status FROM all_submissions", connection)
        connection.close()
        return df
    return pd.DataFrame()

# --- Auth Helper ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(email, password):
    connection = get_sqlite_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT full_name, email, phone, role FROM users WHERE lower(email) = ? AND password = ?", (email.lower().strip(), hash_password(password)))
        result = cursor.fetchone()
        connection.close()
        if result:
            return {"name": result[0], "email": result[1], "phone": result[2], "role": result[3]}
    return None

def register_user(name, email, phone, password, role):
    connection = get_sqlite_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO users (full_name, email, phone, password, role) VALUES (?, ?, ?, ?, ?)", (name, email.lower().strip(), phone, hash_password(password), role))
            connection.commit()
            return True, "Registration successful!"
        except sqlite3.IntegrityError:
            return False, "Email already exists."
        finally:
            connection.close()
    return False, "DB Error"

# --- ML Models ---
@st.cache_resource
def build_models(resume_texts):
    vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
    vectorizer.fit(resume_texts)
    transformer = SentenceTransformer("all-MiniLM-L6-v2")
    return vectorizer, transformer

def score_candidates(df, job_desc, vectorizer, transformer):
    clean_job = preprocess_text(job_desc)
    job_vec = vectorizer.transform([clean_job])
    job_emb = transformer.encode([clean_job])[0]
    results = []
    for _, row in df.iterrows():
        clean_res = preprocess_text(row["Resume_Text"])
        tfidf = cosine_similarity(vectorizer.transform([clean_res]), job_vec)[0,0]
        trans = cosine_similarity([transformer.encode(clean_res)], [job_emb])[0,0]
        final = compute_weighted_score(tfidf, trans)
        results.append({"Name": row["Name"], "Email": row["Email"], "Resume_Text": row["Resume_Text"], "TF-IDF Score": tfidf, "Transformer Score": trans, "Final Score": final})
    return pd.DataFrame(results).sort_values("Final Score", ascending=False).reset_index(drop=True)

# --- Dashboard Components ---
def candidate_dashboard(user):
    st.header(f"Welcome, {user['name']} (Candidate)")
    sub = find_submission_by_email(user['email'])
    status = sub[8] if sub else "Applied"
    
    # Visual Stepper
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="green-text">Application Status: {status}</div>', unsafe_allow_html=True)
    steps = ["Applied", "Under Review", "Shortlisted"]
    status_map = {"Applied": 0, "Under Review": 1, "Shortlisted": 2}
    curr = status_map.get(status, 0)
    
    stepper = '<div class="stepper">'
    for i, s_name in enumerate(steps):
        cls = "active" if i == curr else ("completed" if i < curr else "")
        line_cls = "completed" if i < curr else ""
        stepper += f'<div class="step"><div class="step-circle {cls}">{i+1}</div><div class="step-label">{s_name}</div></div>'
        if i < 2: stepper += f'<div class="step-line {line_cls}"></div>'
    st.markdown(stepper + '</div></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload CV", type=["pdf", "txt"])
        if st.button("Submit CV"):
            if uploaded:
                text = extract_text_from_file(uploaded)
                save_submission(user['name'], user['email'], text)
                st.success("✅ Application Received!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="card">### Resume Analysis</div>', unsafe_allow_html=True)
        if sub:
            score = (sub[6] or 0) * 100
            st.metric("Match Strength", f"{score:.1f}%")

def recruiter_dashboard(user):
    st.header(f"Welcome, {user['name']} (Recruiter)")
    df = load_submissions()
    if df.empty: st.info("No submissions yet.")
    else:
        job_title = st.text_input("Job Title")
        job_desc = st.text_area("Job Description")
        if st.button("Compute Rankings"):
            vec, trans = build_models(df["Resume_Text"].tolist())
            scores = score_candidates(df, job_desc, vec, trans)
            for _, r in scores.iterrows():
                save_submission(r["Name"], r["Email"], r["Resume_Text"], r["TF-IDF Score"], r["Transformer Score"], r["Final Score"], status="Under Review")
            st.success("Rankings computed!")
            st.rerun()

        # Rankings Table...
        if not df[df["Final Score"] > 0].empty:
            st.dataframe(df.sort_values("Final Score", ascending=False))
            if st.button("Accept Top Candidates"):
                top_emails = df.sort_values("Final Score", ascending=False).head(2)["Email"].tolist()
                for email in top_emails:
                    update_candidate_status(email, "Shortlisted")
                st.success("Status Updated to Shortlisted!")
                st.rerun()

# --- Main App ---
def main():
    init_db()
    st.markdown(f'<div class="header"> Resume Screening System</div><div class="main-content">', unsafe_allow_html=True)
    
    if "user" not in st.session_state: st.session_state["user"] = None

    if st.session_state["user"] is None:
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            e = st.text_input("Email")
            p = st.text_input("Password", type="password")
            if st.button("Login"):
                u = login_user(e, p)
                if u: 
                    st.session_state["user"] = u
                    st.rerun()
        with tab2:
            n = st.text_input("Name")
            re_e = st.text_input("Email ")
            re_p = st.text_input("Password ", type="password")
            role = st.radio("Role", ["candidate", "recruiter"])
            if st.button("Register"):
                register_user(n, re_e, "000", re_p, role)
                st.success("Success!")
    else:
        if st.sidebar.button("Logout"):
            st.session_state["user"] = None
            st.rerun()
        u = st.session_state["user"]
        if u["role"] == "candidate": candidate_dashboard(u)
        else: recruiter_dashboard(u)
    
    st.markdown('</div><div class="footer">© 2026 Resume Screening System</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
