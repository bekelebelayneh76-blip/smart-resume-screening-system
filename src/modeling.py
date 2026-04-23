from typing import Any, Dict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import pandas as pd


def build_tfidf_model(df) -> Dict[str, Any]:
    """Fit a TF-IDF model over resumes and job descriptions."""
    corpus = df["resume_text_clean"].astype(str).tolist() + df["job_description_clean"].astype(str).tolist()
    vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
    vectorizer.fit(corpus)
    return {"tfidf_vectorizer": vectorizer}


def score_similarity_tfidf(resume_text: str, job_description: str, vectorizer: TfidfVectorizer) -> float:
    """Compute cosine similarity between resume and job description using TF-IDF."""
    vectors = vectorizer.transform([resume_text, job_description])
    similarity = cosine_similarity(vectors[0], vectors[1])[0, 0]
    return float(similarity)


def load_sentence_transformer_model(model_name: str = "all-mpnet-base-v2") -> SentenceTransformer:
    """Load a transformer model for semantic embeddings."""
    return SentenceTransformer(model_name)


def score_similarity_transformer(resume_text: str, job_description: str, model: SentenceTransformer) -> float:
    """Compute cosine similarity between resume and job description embeddings."""
    embeddings = model.encode([resume_text, job_description], convert_to_numpy=True)
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0, 0]
    return float(similarity)


def compute_weighted_score(
    tfidf_score: float,
    transformer_score: float,
    years_of_experience: float = 0.0,
    tfidf_weight: float = 0.3,
    transformer_weight: float = 0.7,
    experience_bonus: float = 0.02,
) -> float:
    """Compute weighted final score from TF-IDF and Transformer scores.

    Transformer score is given a higher weight by default, and candidates with
    more than 5 years of experience receive a small bonus as a tie-breaker.
    """
    score = tfidf_weight * tfidf_score + transformer_weight * transformer_score
    if years_of_experience > 5:
        score += experience_bonus
    return min(score, 1.0)


def apply_min_max_scaling(scores: list[float]) -> list[float]:
    """Apply Min-Max scaling to a list of scores, making the highest 1.0 and lowest 0.0."""
    if not scores:
        return []
    min_score = min(scores)
    max_score = max(scores)
    if max_score == min_score:
        return [1.0] * len(scores)  # If all scores are the same, set to 1.0
    return [(s - min_score) / (max_score - min_score) for s in scores]


def evaluate_candidates(
    resumes: list[str],
    job_descriptions: list[str],
    tfidf_model: Dict[str, Any],
    transformer_model: SentenceTransformer,
) -> list[Dict[str, Any]]:
    """Evaluate candidates based on resume and job description similarity."""
    results = []
    for resume, job_description in zip(resumes, job_descriptions):
        resume_text = resume
        job_description = job_description
        tfidf_score = score_similarity_tfidf(resume_text, job_description, tfidf_model["tfidf_vectorizer"])
        transformer_score = score_similarity_transformer(resume_text, job_description, transformer_model)
        weighted_score = compute_weighted_score(tfidf_score, transformer_score)
        results.append(
            {
                "resume": resume,
                "job_description": job_description,
                "TF-IDF Score": tfidf_score,
                "Transformer Score": transformer_score,
                "Weighted Score": weighted_score,
            }
        )
    return results


def results_df(results) -> pd.DataFrame:
    """Convert results to a DataFrame and sort by Final Score and upload_time."""
    results_df = pd.DataFrame(results)
    return results_df.sort_values(
        ["Final Score", "upload_time"],
        ascending=[False, False]
    ).reset_index(drop=True)
