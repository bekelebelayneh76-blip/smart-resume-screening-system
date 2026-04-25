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
            
    /* 1. ያንተ የነበረው ኮድ (GitHub እና Fork ለመደበቅ) */
    header[data-testid="stHeader"] a[href*="github.com"],
    header[data-testid="stHeader"] a[aria-label*="GitHub"],
    header[data-testid="stHeader"] [data-testid="stToolbarActions"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* 2. ያንተ የነበረው ኮድ (ሜኑውን ለመደበቅ) */
    #MainMenu {
        visibility: hidden;
    }

    /* 3. ያንተ የነበረው ኮድ (Sidebar ቀስት እንዲታይ) */
    header[data-testid="stHeader"] {
        background-color: rgba(0,0,0,0);
    }

    /* --- አዲስ የተጨመረ፡ የፕሮፋይል ፎቶን ብቻ ለመደበቅ --- */
    
    /* 4. የፕሮፋይል ፎቶውን (Avatar icon) መደበቂያ */
    [data-testid="stHeader"] img {
        display: none !important;
    }

    /* 5. አይጥ ሲጠጋ የሚመጣውን 'View Profile' በተን መከልከያ */
    button[aria-label="View profile"], 
    .st-emotion-cache-1vq4p4l {
        display: none !important;
    }

    /* 6. በስተቀኝ በኩል ያለውን የፕሮፋይል በተን ሙሉ በሙሉ ማጥፊያ */
    [data-testid="stHeaderActionButton"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
CUSTOM_CSS = """
<style>
    /* Header */
    .header {
        background-color: #006400;
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
    /* Main content padding to account for sticky header */
    .main-content {
        padding-top: 120px;
        padding-bottom: 60px; /* To prevent content from being hidden behind the footer */
    }
    /* Cards */
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
    /* Sidebar */
    .sidebar .stRadio > div {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 10px;
    }
    /* Buttons */
    .submit-btn-container button {
        background-color: #000080; /* Navy Blue */
        color: white;
        border: none;
        padding: 10px;
        border-radius: 5px;
        width: 100%;
        font-size: 16px;
        transition: background-color 0.3s;
    }
    .submit-btn-container button:hover {
        background-color: #4169E1; /* Royal Blue */
    }
    /* Footer */
    .footer {
        text-align: center;
        padding: 10px;
        background-color: #f8f9fa;
        color: blue;
        position: fixed;
        font-weight: bold;
        font-size: 24px;
        bottom: 0;
        width: 100%;
    }


 @media (max-width: 768px) {
        .footer {
            font-size: 12px;
            padding: 8px;
        }
    }


    /* Status Badges */
    .badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: bold;
    }
    .badge-accepted {
        background-color: #28a745;
        color: white;
    }
    .badge-processing {
        background-color: #007bff;
        color: white;
        
    }
    
    /* Progress Bar */
    
    .progress-bar {
        width: 100%;
        background-color: #e9ecef;
        border-radius: 10px;
        overflow: hidden;
    }
    .progress-fill {
        height: 20px;
        background-color: #28a745;
        width: 100%; /* Full for accepted */
    }
    /* Stepper */
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
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: #e9ecef;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: #6c757d;
        margin-bottom: 5px;
    }
    .step-circle.active {
        background-color: #28a745;
        color: white;
    }
    .step-circle.completed {
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
    /* Skill Badges */
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






# Load SMTP credentials: prioritize st.secrets for deployment, fall back to .env for local testing
try:
    SMTP_USERNAME = st.secrets["SMTP_USERNAME"]
    SMTP_PASSWORD = st.secrets["SMTP_PASSWORD"]
    SMTP_SERVER = st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(st.secrets.get("SMTP_PORT", 587))
except (KeyError, StreamlitSecretNotFoundError):
    # Fall back to environment variables with .env loading
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))


# --- SQLite Database Functions ---
def get_sqlite_connection():
    """Establish a connection to the SQLite database."""
    try:
        connection = sqlite3.connect('resume_system.db')
        return connection
    except Error as e:
        st.error(f"Error connecting to SQLite: {e}")
        return None

def init_db():
    """Initialize SQLite database and ensure tables exist."""
    connection = get_sqlite_connection()
    if connection:
        cursor = connection.cursor()
        try:
            # Create users table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    phone TEXT,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('candidate', 'recruiter'))
                )
            """)
            # Create all_submissions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS all_submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    resume_text TEXT,
                    tf_idf_score REAL,
                    transformer_score REAL,
                    final_score REAL,
                    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(email)
                )
            """)
            # Ensure the email column has a unique index for existing tables
            try:
                cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_all_submissions_email ON all_submissions(email)")
            except Error:
                pass
            # Create invitation_codes table for recruiter pre-verification
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invitation_codes (
                    email TEXT PRIMARY KEY,
                    code TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            connection.commit()
        except Error as e:
            st.error(f"Error creating tables: {e}")
        finally:
            cursor.close()
            connection.close()

def load_submissions() -> pd.DataFrame:
    """Load all submissions from the SQLite database as a Pandas DataFrame."""
    connection = get_sqlite_connection()
    if connection:
        try:
            df = pd.read_sql_query("SELECT full_name AS Name, email AS Email, resume_text AS Resume_Text, tf_idf_score, transformer_score, final_score, upload_time FROM all_submissions", connection)
            return df
        except Error as e:
            st.error(f"Error loading submissions: {e}")
            return pd.DataFrame()
        finally:
            connection.close()
    return pd.DataFrame()

def save_submission(name: str, email: str, resume_text: str, tf_idf_score: float = None, transformer_score: float = None, final_score: float = None):
    """Save a new submission to the SQLite database."""
    connection = get_sqlite_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO all_submissions (full_name, email, resume_text, tf_idf_score, transformer_score, final_score, upload_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, email, resume_text, tf_idf_score, transformer_score, final_score, datetime.now()))
            connection.commit()
        except Error as e:
            st.error(f"Error saving submission: {e}")
        finally:
            cursor.close()
            connection.close()

def find_submission_by_email(email: str):
    """Return submission data if exists, else None."""
    connection = get_sqlite_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM all_submissions WHERE email = ? LIMIT 1", (email,))
            result = cursor.fetchone()
            return result
        except Error as e:
            st.error(f"Error checking submission: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    return None


def clear_all_submissions() -> bool:
    """Delete all rows from the submissions table."""
    connection = get_sqlite_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM all_submissions")
            connection.commit()
            return True
        except Error as e:
            st.error(f"Error clearing submissions: {e}")
            return False
        finally:
            cursor.close()
            connection.close()


# --- Pre-Verification Functions for Recruiters ---
def generate_access_code():
    """Generate a random 6-character alphanumeric code."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(6))


def save_invitation_code(email: str, code: str):
    """Save or update invitation code in the database."""
    connection = get_sqlite_connection()
    if connection:
        cursor = connection.cursor()
        try:
            # Use INSERT OR REPLACE to handle existing emails
            cursor.execute("""
                INSERT OR REPLACE INTO invitation_codes (email, code, created_at)
                VALUES (?, ?, ?)
            """, (email, code, datetime.now()))
            connection.commit()
            return True
        except Error as e:
            st.error(f"Error saving invitation code: {e}")
            return False
        finally:
            cursor.close()
            connection.close()
    return False


def verify_invitation_code(email: str, code: str) -> bool:
    """Verify if the entered code matches the stored code for the email."""
    connection = get_sqlite_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT code FROM invitation_codes
                WHERE email = ? AND created_at >= datetime('now', '-24 hours')
            """, (email,))
            result = cursor.fetchone()
            if result and result[0] == code:
                return True
            return False
        except Error as e:
            st.error(f"Error verifying code: {e}")
            return False
        finally:
            cursor.close()
            connection.close()
    return False


def send_access_code_email(recipient_email: str, access_code: str):
    """Send the access code to the recruiter's email."""
    # This pulls the data you just saved in the Secrets tab
    sender_email = st.secrets["EMAIL_SENDER"]
    sender_password = st.secrets["EMAIL_PASSWORD"]

    try:
        msg = MIMEText(f"Hello! Your registration access code is: {access_code}")
        msg['Subject'] = 'Access Code - Resume Screening System'
        msg['From'] = sender_email
        msg['To'] = recipient_email

        # Gmail SMTP settings
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True, "Email sent successfully!"
    except Exception as e:
        return False, str(e)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def validate_email(email: str) -> bool:
    """Validate email format using regex."""
    if not email.strip():
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def register_user(name: str, email: str, phone: str, password: str, role: str):
    """Register a new user."""
    if not validate_email(email):
        return False, "Invalid email address."

    connection = get_sqlite_connection()
    if not connection:
        return False, "Database connection failed."

    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (full_name, email, phone, password, role) VALUES (?, ?, ?, ?, ?)",
            (name, email.lower().strip(), phone, hash_password(password.strip()), role),
        )
        connection.commit()
        return True, "Registration successful!"
    except sqlite3.IntegrityError:
        return False, "Email already registered."
    except Error as e:
        return False, f"Registration failed: {str(e)}"
    finally:
        cursor.close()
        connection.close()


def login_user(email: str, password: str) -> dict | None:
    """Login user and return user info if successful."""
    connection = get_sqlite_connection()
    if not connection:
        return None

    cursor = connection.cursor()
    try:
        cursor.execute("SELECT full_name, email, phone, role FROM users WHERE email = ? AND password = ?",
                      (email.lower().strip(), hash_password(password.strip())))
        result = cursor.fetchone()
        if result:
            return {"name": result[0], "email": result[1], "phone": result[2], "role": result[3]}
        return None
    except Error as e:
        st.error(f"Login failed: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

@st.cache_resource
def build_models(resume_texts):
    """Build TF-IDF and Transformer models."""
    vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
    vectorizer.fit(resume_texts)
    transformer = SentenceTransformer("all-mpnet-base-v2")
    return vectorizer, transformer

def score_candidates(df, job_description, vectorizer, transformer):
    """Score all candidates against the job description."""
    clean_job = preprocess_text(job_description)
    job_vector = vectorizer.transform([clean_job])
    job_embedding = transformer.encode([clean_job], convert_to_numpy=True)[0]

    results = []
    for idx, row in df.iterrows():
        clean_resume = preprocess_text(row["Resume_Text"])
        tfidf_score = cosine_similarity(vectorizer.transform([clean_resume]), job_vector)[0, 0]
        transformer_score = cosine_similarity(transformer.encode([clean_resume], convert_to_numpy=True), [job_embedding])[0, 0]
        years_of_experience = float(
            row.get("Years of Experience", row.get("Years_of_Experience", row.get("experience_years", 0))) or 0
        )
        final_score = compute_weighted_score(
            tfidf_score,
            transformer_score,
            years_of_experience=years_of_experience,
        )
        results.append({
            "Name": row["Name"],
            "Email": row["Email"],
            "Resume_Text": row["Resume_Text"],
            "upload_time": row.get("upload_time", row.get("Timestamp", None)),
            "Years of Experience": years_of_experience,
            "TF-IDF Score": tfidf_score,
            "Transformer Score": transformer_score,
            "Final Score": final_score,
        })
    results_df = pd.DataFrame(results)
    return results_df.sort_values(["Final Score", "upload_time"], ascending=[False, False]).reset_index(drop=True)


def extract_skills(resume_text: str) -> list[str]:
    """Extract common skills from resume text."""
    common_skills = [
        "Python", "Java", "JavaScript", "C++", "SQL", "Machine Learning", "Data Analysis",
        "HTML", "CSS", "React", "Node.js", "Django", "Flask", "TensorFlow", "PyTorch",
        "AWS", "Docker", "Git", "Linux", "Agile", "Scrum"
    ]
    found_skills = []
    resume_lower = resume_text.lower()
    for skill in common_skills:
        if skill.lower() in resume_lower:
            found_skills.append(skill)
    return found_skills[:10]  # Limit to 10 skills


def compute_resume_strength(resume_text: str, job_description: str) -> float:
    """Compute a simple resume strength score based on keyword matching."""
    job_words = set(preprocess_text(job_description).split())
    resume_words = set(preprocess_text(resume_text).split())
    matching_words = job_words.intersection(resume_words)
    return len(matching_words) / len(job_words) if job_words else 0.0


def suggest_keywords(resume_text: str, job_description: str) -> list[str]:
    """Suggest 2-3 keywords from job description not in resume."""
    job_words = set(preprocess_text(job_description).split())
    resume_words = set(preprocess_text(resume_text).split())
    missing_words = job_words - resume_words
    # Filter to meaningful words (length > 3)
    meaningful = [word for word in missing_words if len(word) > 3]
    return meaningful[:3]


def send_acceptance_email(recipient_email: str, candidate_name: str, position: str, recruiter_name: str, custom_message: str = "") -> tuple[bool, str]:
    # This pulls the data you just saved in the Secrets tab
    sender_email = st.secrets["EMAIL_SENDER"]
    sender_password = st.secrets["EMAIL_PASSWORD"]

    message = MIMEMultipart("alternative")
    message["Subject"] = f"Application Update: You are accepted for {position}"
    message["From"] = sender_email
    message["To"] = recipient_email

    text = (
        f"Hello {candidate_name},\n\n"
        f"Congratulations! Based on the job requirements you are among the top matched candidates for the position: {position}.\n\n"
        "A recruiter has reviewed your profile and marked you as accepted.\n\n"
    )
    if custom_message:
        text += f"{custom_message}\n\n"
    text += (
        "Please stay tuned for the next steps.\n\n"
        "Best regards,\n"
        f"{recruiter_name}\n"
        "Resume Screening Team"
    )

    html = (
        f"<html><body><p>Hello {candidate_name},</p>"
        f"<p>Congratulations! Based on the job requirements you are among the top matched candidates for the position: <strong>{position}</strong>.</p>"
        "<p>A recruiter has reviewed your profile and marked you as <strong>accepted</strong>.</p>"
    )
    if custom_message:
        html += f"<p>{custom_message}</p>"
    html += (
        "<p>Please stay tuned for the next steps.</p>"
        "<p>Best regards,<br/>"
        f"{recruiter_name}<br/>Resume Screening Team</p>"
        "</body></html>"
    )

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)

    try:
        # Gmail SMTP settings
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)
        return True, ""
    except Exception as exc:
        return False, str(exc)


def candidate_dashboard(user):
    st.header(f"Welcome, {user['name']} (Candidate)")
    
    # Determine status
    accepted_emails = st.session_state.get("accepted_emails", [])
    submission = find_submission_by_email(user['email'])
    has_submission = submission is not None
    is_accepted = user['email'] in accepted_emails
    
    # Visual Status Tracker: Stepper
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="green-text"><strong>Application Status</strong></div>', unsafe_allow_html=True)
    steps = ["Applied", "Under Review", "Shortlisted"]
    current_step = 0
    if has_submission:
        current_step = 1
    if is_accepted:
        current_step = 2
    
    stepper_html = '<div class="stepper">'
    for i, step in enumerate(steps):
        active_class = "active" if i == current_step else ("completed" if i < current_step else "")
        line_class = "completed" if i < current_step else ""
        stepper_html += f'<div class="step"><div class="step-circle {active_class}">{i+1}</div><div class="step-label">{step}</div></div>'
        if i < len(steps) - 1:
            stepper_html += f'<div class="step-line {line_class}"></div>'
    stepper_html += '</div>'
    st.markdown(stepper_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="green-text"><strong>Candidate Submission</strong></div>', unsafe_allow_html=True)
        st.write("Submit your resume to be reviewed by recruiters.")

        uploaded_file = st.file_uploader("Upload your CV (PDF or TXT)", type=["pdf", "txt"])

        st.markdown('<div class="submit-btn-container">', unsafe_allow_html=True)
        if st.button("Submit CV", key="submit_cv"):
            if not uploaded_file:
                st.error("Please upload your CV.")
            else:
                with st.spinner("Processing your CV..."):
                    resume_text = extract_text_from_file(uploaded_file)
                    save_submission(user['name'], user['email'], resume_text)
                st.success("Application Received! Your CV has been submitted successfully.")
                submission = find_submission_by_email(user['email'])
        st.markdown('</div>', unsafe_allow_html=True)

        if submission:
            st.markdown('---')
            st.markdown('### Your Submitted CV Review')
            if submission[3]:
                st.text_area("Submitted resume text", submission[3], height=250)
            else:
                st.info("Your uploaded resume is stored and awaiting reviewer analysis.")

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="green-text"><strong>Resume Analysis</strong></div>', unsafe_allow_html=True)
        
        # Skill Extraction
        submission = find_submission_by_email(user['email'])
        if submission:
            resume_text = submission[3]  # resume_text is at index 3
            skills = extract_skills(resume_text)
            if skills:
                st.markdown("**Detected Skills:**")
                skill_badges = "".join([f'<span class="skill-badge">{skill}</span>' for skill in skills])
                st.markdown(skill_badges, unsafe_allow_html=True)
            else:
                st.info("No skills detected. Consider adding technical skills to your resume.")
        
        # Match Feedback
        if "job_description" in st.session_state and submission:
            job_desc = st.session_state["job_description"]
            resume_text = submission[3]  # resume_text is at index 3
            strength_score = compute_resume_strength(resume_text, job_desc)
            st.markdown(f"**Resume Strength:** {strength_score:.1%}")
            tips = suggest_keywords(resume_text, job_desc)
            if tips:
                st.markdown("**💡 Tips:** Add these keywords to improve matching:")
                st.write(", ".join(tips))
        else:
            st.info("Submit your resume and wait for recruiter to set job description for analysis.")
        
        st.markdown('</div>', unsafe_allow_html=True)


def recruiter_dashboard(user):
    st.header(f"Welcome, {user['name']} (Recruiter)")

    submissions_df = load_submissions()
    if submissions_df.empty:
        st.info("No submissions yet.")
    else:
        st.write(f"Total Submissions: {len(submissions_df)}")

        job_title = st.text_input("Position / Job Title", value="Best matched role")
        job_description = st.text_area("Enter Job Description")
        num_candidates = st.number_input(
            "Number of candidates to accept",
            min_value=1,
            max_value=max(1, len(submissions_df)),
            value=1,
            step=1,
        )

        if st.button("Compute Rankings"):
            if not job_description.strip():
                st.error("Please enter a job description.")
            elif not job_title.strip():
                st.error("Please enter a job title.")
            else:
                # Remove stale ranking rows before writing new results
                clear_all_submissions()

                resume_texts = [preprocess_text(text) for text in submissions_df["Resume_Text"]]
                vectorizer, transformer = build_models(resume_texts)
                scores_df = score_candidates(submissions_df, job_description, vectorizer, transformer)

                # Save scores to database
                for _, row in scores_df.iterrows():
                    save_submission(
                        name=row["Name"],
                        email=row["Email"],
                        resume_text=row["Resume_Text"],
                        tf_idf_score=row["TF-IDF Score"],
                        transformer_score=row["Transformer Score"],
                        final_score=row["Final Score"]
                    )

                st.session_state["scores_df"] = scores_df
                st.session_state["job_title"] = job_title
                st.session_state["job_description"] = job_description
                st.session_state["num_candidates"] = int(num_candidates)

        if "scores_df" in st.session_state:
            scores_df = st.session_state["scores_df"]
            job_title = st.session_state.get("job_title", "Best matched role")
            top_n = min(int(st.session_state.get("num_candidates", 1)), len(scores_df))
            selected_df = scores_df.head(top_n)
            st.session_state["accepted_emails"] = selected_df["Email"].tolist()

            tab1, tab2 = st.tabs(["📊 Table View", "📈 Visual Analysis"])

            with tab1:
                st.subheader("Ranked Candidates")
                st.write(f"Top {top_n} candidate(s) for '{job_title}'")
                
                # Smart Filtering
                min_score = st.slider("Filter by minimum Final Score", 0.0, 1.0, 0.0, 0.01, format="%.2f")
                filtered_df = scores_df[scores_df["Final Score"] >= min_score]
                
                st.dataframe(style_scores_table(filtered_df))

                st.markdown("---")
                st.subheader("Accepted Candidate Emails")
                st.dataframe(
                    selected_df[["Name", "Email", "Final Score"]]
                    .style.format({"Final Score": "{:.2%}"})
                )
                
                # Export to CSV
                csv_data = selected_df[["Name", "Email", "Final Score"]].to_csv(index=False)
                st.download_button(
                    label="Download Accepted Candidates as CSV",
                    data=csv_data,
                    file_name="accepted_candidates.csv",
                    mime="text/csv"
                )

                job_position = st.text_input("Position", value=job_title, key="accepted_job_position")
                custom_message = st.text_area("Custom Message to Accepted Candidates", placeholder="e.g., Please attend the interview on [date] at [time].", height=100)

                if st.button("Send acceptance to top candidates"):
                    try:
                        sender_email = st.secrets["EMAIL_SENDER"]
                        sender_password = st.secrets["EMAIL_PASSWORD"]
                    except KeyError:
                        st.error(
                            "Email credentials not configured in Streamlit secrets. Please set EMAIL_SENDER and EMAIL_PASSWORD in your secrets."
                        )
                    else:
                        sent = []
                        failed = []
                        for _, row in selected_df.iterrows():
                            success, error_message = send_acceptance_email(
                                recipient_email=row["Email"],
                                candidate_name=row["Name"],
                                position=job_position,
                                recruiter_name=user["name"],
                                custom_message=custom_message,
                            )
                            if success:
                                sent.append(row["Email"])
                            else:
                                failed.append(f"{row['Email']} ({error_message})")

                        if sent:
                            st.success(f"Acceptance  sent to: {', '.join(sent)}")
                        if failed:
                            st.error(f"Failed to send email to: {', '.join(failed)}")

            with tab2:
                st.subheader("Top 5 Candidates")
                top_5_df = scores_df.head(5)
                fig = px.bar(
                    top_5_df,
                    x="Name",
                    y="Final Score",
                    title="Top 5 Candidates by Final Score",
                    text="Final Score",
                    color="Final Score",
                    color_continuous_scale="greens"
                )
                fig.update_layout(
                    xaxis_tickangle=-45,
                    yaxis_title="Final Score",
                    yaxis_tickformat=".1%"
                )
                fig.update_traces(texttemplate="%{text:.1%}", textposition="outside")
                st.plotly_chart(fig)


def get_score_color(score: float) -> str:
    if score >= 0.70:
        return "background-color: #c6efce; color: #006100"
    if score >= 0.40:
        return "background-color: #fff2cc; color: #9c6500"
    return "background-color: #f8cbad; color: #9c0006"


def highlight_row_based_on_final(row: pd.Series) -> list[str]:
    style = get_score_color(row["Final Score"])
    return [style] * len(row)


def style_scores_table(df: pd.DataFrame) -> "pd.io.formats.style.Styler":
    return (
        df.style
          .apply(highlight_row_based_on_final, axis=1)
          .format({
              "TF-IDF Score": "{:.2%}",
              "Transformer Score": "{:.2%}",
              "Final Score": "{:.2%}"
          })
          .set_table_styles([
              {
                  "selector": "th",
                  "props": [
                      ("background-color", "#1f2937"),
                      ("color", "white"),
                      ("font-weight", "bold"),
                      ("text-align", "center")
                  ]
              }
          ])
    )


def main():
    # Initialize database
    init_db()

    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Header
    st.markdown('<div class="header"> Resume Screening System</div>', unsafe_allow_html=True)
    # Main content
    st.markdown('<div class="main-content">', unsafe_allow_html=True)

    # Check for logout via URL parameter
    query_params = st.query_params
    if query_params.get("logout") == "true":
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.query_params.clear()
        st.success("You have been logged out successfully!")
        st.rerun()

    # Check for session timeout (30 minutes)
    if "user" in st.session_state and "login_time" in st.session_state:
        if datetime.now() - st.session_state["login_time"] > timedelta(minutes=30):
            st.warning("Your session has expired due to inactivity. Please log in again.")
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Check if user is logged in
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if "needs_redirect" not in st.session_state:
        st.session_state["needs_redirect"] = False
    if "skip_redirect_once" not in st.session_state:
        st.session_state["skip_redirect_once"] = False
    if "login_success_message" not in st.session_state:
        st.session_state["login_success_message"] = ""
    if "login_success_visible" not in st.session_state:
        st.session_state["login_success_visible"] = False

    if st.session_state["user"] is None:
        # Login/Register Page
        st.markdown("<h1 style='text-align: center;'>Welcome to Resume Screening System</h1>", unsafe_allow_html=True)

        outer_col1, outer_col2, outer_col3 = st.columns([1, 2, 1])
        with outer_col2:
            login_default = "🔐 Login" if st.session_state.get("needs_redirect") and not st.session_state.get("skip_redirect_once") else None
            tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"], default=login_default)

            with tab1:
                st.subheader("Login")
                st.session_state.pop("reg_success_internal", None)
                st.session_state.pop("registration_message", None)
                email = st.text_input("Email", key="login_email", autocomplete="email")
                password = st.text_input("Password", type="password", key="login_password", autocomplete="current-password")
                if st.session_state.get("login_success_visible"):
                    st.success(st.session_state.get("login_success_message", "Registration successful! Please login."))
                    st.session_state["login_success_visible"] = False
                    st.session_state["login_success_message"] = ""
                    st.session_state["needs_redirect"] = False
                if st.button("Login"):
                    user = login_user(email, password)
                    if user:
                        st.session_state["user"] = user
                        st.session_state["login_time"] = datetime.now()
                        st.success("Logged in successfully!")
                        st.session_state.pop("registration_message", None)
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

            with tab2:
                st.subheader("Register")

                # Initialize session state for pre-verification
                if "verification_step" not in st.session_state:
                    st.session_state["verification_step"] = "select_role"
                if "verification_email" not in st.session_state:
                    st.session_state["verification_email"] = ""
                if "admin_authorized" not in st.session_state:
                    st.session_state["admin_authorized"] = False
                if "recruiter_step" not in st.session_state:
                    st.session_state["recruiter_step"] = "start"

                role = st.radio("Register as:", ["👤 Candidate", "🔑 Recruiter"], key="reg_role")

                if role == "👤 Candidate":
                    # Simple registration for candidates
                    st.markdown("### Candidate Registration")

                    name = st.text_input("Full Name", key="reg_name", autocomplete="name")
                    email = st.text_input("Email", key="reg_email", autocomplete="email")
                    phone = st.text_input("Phone", key="reg_phone", autocomplete="tel")
                    password = st.text_input("Password", type="password", key="reg_password", autocomplete="new-password")
                    confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm", autocomplete="new-password")

                    if st.button("Register as Candidate"):
                        if password != confirm_password:
                            st.error("Passwords do not match.")
                        elif not all([name, email, phone, password]):
                            st.error("Please fill all fields.")
                        elif not validate_email(email):
                            st.error("Please enter a valid email address.")
                        else:
                            success, message = register_user(name, email, phone, password, "candidate")
                            if success:
                                st.success("Registration successful! Please login.")
                                st.session_state["needs_redirect"] = True
                                st.session_state["skip_redirect_once"] = True
                                st.session_state["login_success_message"] = "Registration successful! Please login."
                                st.session_state["login_success_visible"] = True
                                st.session_state["verification_step"] = "select_role"
                            else:
                                st.error(message)

                else:  # Recruiter
                    if not st.session_state["admin_authorized"]:
                        st.markdown("### Step 1: Admin Authorization")
                        st.info("🔐 Admin authorization required for recruiter registration.")
                        admin_key = st.text_input("Enter Admin Master Key", type="password", key="admin_key")

                        if st.button("Authorize"):
                            if admin_key == "MAU_ADMIN_2026":
                                st.session_state["admin_authorized"] = True
                                st.success("✅ Admin authorization successful!")
                                st.rerun()
                            else:
                                st.error("❌ Invalid admin key.")
                    else:
                        # Pre-verification workflow for recruiters
                        if st.session_state["verification_step"] == "select_role":
                            st.markdown("### Step 2: Request Access Code")
                            st.info("🔐 Recruiters must verify their email before registration.")
                            recruiter_email = st.text_input("Enter your email address", key="recruiter_email", autocomplete="email")

                            if st.button("Send Access Code"):
                                if not recruiter_email or not validate_email(recruiter_email):
                                    st.error("Please enter a valid email address.")
                                else:
                                    try:
                                        sender_email = st.secrets["EMAIL_SENDER"]
                                        sender_password = st.secrets["EMAIL_PASSWORD"]
                                    except KeyError:
                                        st.error("Email service is not configured. Please contact administrator.")
                                    else:
                                        # Generate and save code
                                        access_code = generate_access_code()
                                        if save_invitation_code(recruiter_email, access_code):
                                            # Send email
                                            success, message = send_access_code_email(recruiter_email, access_code)
                                            if success:
                                                st.success("Access code sent to your email!")
                                                st.session_state["verification_email"] = recruiter_email
                                                st.session_state["verification_step"] = "verify_code"
                                                st.rerun()
                                            else:
                                                st.error(message)
                                        else:
                                            st.error("Failed to generate access code. Please try again.")

                        elif st.session_state["verification_step"] == "verify_code":
                            st.markdown("### Step 3: Verify Access Code")
                            st.info(f"📧 Code sent to: {st.session_state['verification_email']}")
                            entered_code = st.text_input("Enter the 6-character access code", key="entered_code", max_chars=6)

                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Verify Code"):
                                    if not entered_code or len(entered_code) != 6:
                                        st.error("Please enter a valid 6-character code.")
                                    elif verify_invitation_code(st.session_state["verification_email"], entered_code.upper()):
                                        st.success("✅ Code verified successfully!")
                                        st.session_state["verification_step"] = "complete_registration"
                                        st.rerun()
                                    else:
                                        st.error("❌ Invalid or expired code. Please try again.")

                            with col2:
                                if st.button("Resend Code"):
                                    # Generate new code and resend
                                    access_code = generate_access_code()
                                    if save_invitation_code(st.session_state["verification_email"], access_code):
                                        success, message = send_access_code_email(st.session_state["verification_email"], access_code)
                                        if success:
                                            st.success("New access code sent!")
                                        else:
                                            st.error(message)
                                    else:
                                        st.error("Failed to generate new code.")

                            if st.button("← Back to Email Input"):
                                st.session_state["verification_step"] = "select_role"
                                st.session_state["verification_email"] = ""
                                st.rerun()

                        elif st.session_state["verification_step"] == "complete_registration":
                            st.markdown("### Step 4: Complete Registration")
                            st.success(f"✅ Email verified: {st.session_state['verification_email']}")

                            name = st.text_input("Full Name", key="reg_name", autocomplete="name")
                            phone = st.text_input("Phone", key="reg_phone", autocomplete="tel")
                            password = st.text_input("Password", type="password", key="reg_password", autocomplete="new-password")
                            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm", autocomplete="new-password")

                            if st.button("Complete Registration"):
                                if password != confirm_password:
                                    st.error("Passwords do not match.")
                                elif not all([name, phone, password]):
                                    st.error("Please fill all fields.")
                                else:
                                    success, message = register_user(name, st.session_state["verification_email"], phone, password, "recruiter")
                                    if success:
                                        st.success("Registration successful! Please login.")
                                        st.session_state["needs_redirect"] = True
                                        st.session_state["skip_redirect_once"] = True
                                        st.session_state["login_success_message"] = "Registration successful! Please login."
                                        st.session_state["login_success_visible"] = True
                                        st.session_state["recruiter_step"] = "start"
                                        st.session_state["verification_step"] = "complete_registration"
                                        st.session_state["admin_authorized"] = True
                                    else:
                                        st.error(message)

                                if st.button("← Start Over"):
                                    st.session_state["verification_step"] = "select_role"
                                    st.session_state["verification_email"] = ""
                                    st.session_state["admin_authorized"] = False
                                    st.session_state["recruiter_step"] = "start"
                                    st.rerun()

                if st.session_state.get("skip_redirect_once"):
                    st.session_state["skip_redirect_once"] = False

    else:
        # Dashboard based on role
        user = st.session_state["user"]
        if user["role"] == "candidate":
            candidate_dashboard(user)
        elif user["role"] == "recruiter":
            recruiter_dashboard(user)
            # Temporary reset button for clearing all submissions is only visible to recruiters
            if st.sidebar.button("Reset all submissions"):
                if clear_all_submissions():
                    st.success("All submissions have been cleared.")
                    st.session_state.pop("scores_df", None)
                    st.session_state.pop("accepted_emails", None)
                    return

        # Logout button
        if st.sidebar.button("Logout"):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            # Redirect with logout parameter to ensure clean logout
            st.query_params["logout"] = "true"
            st.rerun()

        # About text below logout button
        st.sidebar.markdown("---")
        if user["role"] == "recruiter":
            st.sidebar.markdown(
                "**About**\n\n"
                "Recruiter dashboard: Create job descriptions, compute resume rankings, and shortlist top candidates efficiently. "
                "Use the system to compare applicant profiles, track matching scores, and speed up hiring decisions."
            )
        else:
            st.sidebar.markdown(
                "**About**\n\n"
                "Candidate dashboard: View your resume submission status and see how your profile aligns with the selected role. "
                "This system helps candidates understand hiring criteria and keep track of application progress."
            )


    st.markdown('</div>', unsafe_allow_html=True)
    # Footer
    st.markdown('<div class="footer">© 2026 Resume Screening System | Mekdela Amba University</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()