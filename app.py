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

# የቀረው የፕሮግራምህ ክፍል እዚህ ይቀጥላል...

st.set_page_config(
    page_title="Resume Screening System",
    page_icon="📄",
    layout="wide",
)

# --- 2. ከዚያ የ CSS ማስተካከያው ይቀጥላል ---
st.markdown("""
    <style>
            header img {
        display: none !important;
    }
            
    header[data-testid="stHeader"] a[href*="github.com"],
    header[data-testid="stHeader"] a[aria-label*="GitHub"],
    header[data-testid="stHeader"] [data-testid="stToolbarActions"] {
        display: none !important;
        visibility: hidden !important;
    }

    #MainMenu {
        visibility: hidden;
    }

    header[data-testid="stHeader"] {
        background-color: rgba(0,0,0,0);
    }

    [data-testid="stHeader"] img {
        display: none !important;
    }

    button[aria-label="View profile"], 
    .st-emotion-cache-1vq4p4l {
        display: none !important;
    }

    [data-testid="stHeaderActionButton"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

CUSTOM_CSS = """
<style>
    .header {
        background-color: #1B5E20;
        color: white;
        padding: 20px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        width: 100%;
        position: sticky;
        top: 0;
        left: 0;
        z-index: 2000;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    .main-content {
        padding-top: 120px;
        padding-bottom: 60px;
    }
    .card {
        background-color: white;
        border: 1px solid #e6e9ef;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        padding: 20px;
        margin-bottom: 20px;
    }
    .green-text {
        color: #006400;
        font-weight: bold;
    }
    .footer {
        text-align: center;
        padding: 10px;
        background-color: #1E1E1E;
        color: white;
        position: fixed;
        font-size: 16px;
        bottom: 0;
        width: 100%;
    }
    .stepper {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 20px 0;
    }
    .step {
        display: flex;
        flex-direction: column;
        align-items: center;
        flex: 1;
    }
    .step-circle {
        width: 40px; height: 40px;
        border-radius: 50%;
        background-color: #e9ecef;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: #6c757d;
        margin-bottom: 5px;
    }
    .step-circle.active, .step-circle.completed {
        background-color: #28a745;
        color: white;
    }
    .step-line {
        height: 2px;
        background-color: #e9ecef;
        flex: 1;
        margin: 0 10px;
    }
    .step-line.completed {
        background-color: #28a745;
    }
    .step-label {
        font-size: 12px;
        text-align: center;
    }
    .skill-badge {
        display: inline-block;
        background-color: #006400;
        color: white;
        padding: 5px 10px;
        margin: 2px;
        border-radius: 15px;
        font-size: 12px;
    }
</style>
"""

# --- Email Credentials ---
try:
    SMTP_USERNAME = st.secrets["SMTP_USERNAME"]
    SMTP_PASSWORD = st.secrets["SMTP_PASSWORD"]
except:
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

# --- SQLite Database Functions ---
def get_sqlite_connection():
    try:
        return sqlite3.connect('resume_system.db')
    except Error as e:
        st.error(f"Error: {e}")
        return None

def init_db():
    connection = get_sqlite_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT, email TEXT UNIQUE, phone TEXT, password TEXT, role TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS all_submissions (id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT, email TEXT UNIQUE, resume_text TEXT, tf_idf_score REAL, transformer_score REAL, final_score REAL, upload_time DATETIME, status TEXT DEFAULT 'Applied')")
        connection.commit()
        connection.close()

def save_submission(name, email, resume_text):
    connection = get_sqlite_connection()
    if connection:
        cursor = connection.cursor()
        # Unicode cleaning to prevent crashes
        clean_text = "".join(c for c in resume_text if c.isprintable() or c.isspace())
        cursor.execute("INSERT OR REPLACE INTO all_submissions (full_name, email, resume_text, upload_time) VALUES (?, ?, ?, ?)", 
                       (name, email.lower().strip(), clean_text, datetime.now()))
        connection.commit()
        connection.close()

def find_submission_by_email(email):
    connection = get_sqlite_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM all_submissions WHERE lower(email) = lower(?)", (email,))
        res = cursor.fetchone()
        connection.close()
        return res
    return None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(email, password):
    connection = get_sqlite_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT full_name, email, phone, role FROM users WHERE lower(email) = ? AND password = ?", (email.lower().strip(), hash_password(password)))
        res = cursor.fetchone()
        connection.close()
        if res: return {"name": res[0], "email": res[1], "phone": res[2], "role": res[3]}
    return None

# --- Candidate Dashboard ---
def candidate_dashboard(user):
    st.header(f"Welcome, {user['name']} (Candidate)")
    
    submission = find_submission_by_email(user['email'])
    status = submission[8] if (submission and len(submission) > 8) else "Applied"
    
    # Visual Status Tracker
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="green-text"><strong>Application Status</strong></div>', unsafe_allow_html=True)
    steps = ["Applied", "Under Review", "Shortlisted"]
    curr = {"Applied": 0, "Under Review": 1, "Shortlisted": 2}.get(status, 0)
    
    stepper_html = '<div class="stepper">'
    for i, s_name in enumerate(steps):
        cls = "active" if i == curr else ("completed" if i < curr else "")
        line_cls = "completed" if i < curr else ""
        stepper_html += f'<div class="step"><div class="step-circle {cls}">{i+1}</div><div class="step-label">{s_name}</div></div>'
        if i < 2: stepper_html += f'<div class="step-line {line_cls}"></div>'
    st.markdown(stepper_html + '</div></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="green-text"><strong>Candidate Submission</strong></div>', unsafe_allow_html=True)
        st.write("Submit your resume to be reviewed by recruiters.")

        uploaded_file = st.file_uploader("Upload your CV (PDF or TXT)", type=["pdf", "txt"])

        # --- እዚህ ጋር የተጠየቀው ማሳሰቢያ ተጨምሯል ---
        st.info("💡 **ማሳሰቢያ፦** ሲስተሙ መረጃዎችን በትክክል እንዲያነብ እባክዎ በሪዙሜዎ ውስጥ 'Emoji' ወይም በጣም ልዩ የሆኑ የዲዛይን ምልክቶችን አይጠቀሙ።")

        if st.button("Submit CV"):
            if uploaded_file:
                text = extract_text_from_file(uploaded_file)
                save_submission(user['name'], user['email'], text)
                st.success("Application Received!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="green-text"><strong>Resume Analysis</strong></div>', unsafe_allow_html=True)
        if submission:
            st.write(f"Current Status: **{status}**")
        else:
            st.info("Submit your resume for analysis.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- Main App ---
def main():
    init_db()
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown('<div class="header"> Resume Screening System</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-content">', unsafe_allow_html=True)

    if "user" not in st.session_state:
        st.session_state["user"] = None

    if st.session_state["user"] is None:
        # Simplified Login
        e = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            u = login_user(e, p)
            if u: 
                st.session_state["user"] = u
                st.rerun()
    else:
        if st.sidebar.button("Logout"):
            st.session_state["user"] = None
            st.rerun()
        
        u = st.session_state["user"]
        if u["role"] == "candidate":
            candidate_dashboard(u)
        else:
            st.write("Recruiter Dashboard")

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="footer">© 2026 Resume Screening System </div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
