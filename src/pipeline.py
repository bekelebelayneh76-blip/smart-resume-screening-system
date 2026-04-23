from pathlib import Path

import pandas as pd
from sentence_transformers import SentenceTransformer

from src.data_utils import load_dataset, preprocess_dataset
from src.evaluation import evaluate_similarity
from src.modeling import (build_tfidf_model, load_sentence_transformer_model,
                           score_similarity_tfidf, score_similarity_transformer)


def build_models_from_dataset(dataset_path: str):
    df = load_dataset(dataset_path)
    df = preprocess_dataset(df)
    models = build_tfidf_model(df)
    models["transformer_model"] = load_sentence_transformer_model()
    return models


def evaluate_models(dataset_path: str, threshold: float = 0.5):
    df = load_dataset(dataset_path)
    df = preprocess_dataset(df)
    vectorizer = build_tfidf_model(df)["tfidf_vectorizer"]
    transformer_model = load_sentence_transformer_model()

    tfidf_scores = [
        score_similarity_tfidf(row.resume_text_clean, row.job_description_clean, vectorizer)
        for row in df.itertuples()
    ]
    transformer_scores = [
        score_similarity_transformer(row.resume_text_clean, row.job_description_clean, transformer_model)
        for row in df.itertuples()
    ]

    results = {
        "tfidf": evaluate_similarity(df["label"].astype(int), tfidf_scores, threshold),
        "transformer": evaluate_similarity(df["label"].astype(int), transformer_scores, threshold),
    }
    return results


def save_evaluation_report(dataset_path: str, output_path: str = "evaluation_report.csv"):
    results = evaluate_models(dataset_path)
    df = pd.DataFrame(
        [
            {"model": "tfidf", **results["tfidf"]},
            {"model": "transformer", **results["transformer"]},
        ]
    )
    df.to_csv(output_path, index=False)
    return Path(output_path).absolute()
