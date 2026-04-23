import csv
import random

RESUME_TEMPLATES = [
    "Experienced software engineer with expertise in Python, machine learning, data analysis, and NLP.",
    "Senior data scientist skilled in model evaluation, feature engineering, and statistical analysis.",
    "Full-stack developer with experience in JavaScript, cloud deployment, and REST API design.",
    "Marketing professional with experience in SEO, campaign management, and content creation.",
    "Cybersecurity specialist with knowledge in network security, encryption, and threat mitigation.",
    "DevOps engineer experienced in CI/CD pipelines, Docker, Kubernetes, and infrastructure automation.",
    "Product manager with skills in agile methodologies, user research, and product roadmap planning.",
    "UX/UI designer proficient in Figma, Sketch, user testing, and design systems.",
    "Database administrator with expertise in SQL, MongoDB, and database performance optimization.",
    "Business analyst skilled in requirements gathering, process modeling, and stakeholder management.",
    "Mobile app developer with experience in React Native, iOS/Android development, and app store deployment.",
    "QA engineer with expertise in automated testing, Selenium, bug tracking, and quality assurance.",
    "Technical writer experienced in creating documentation, user guides, and API references.",
    "Project manager with experience in Scrum, risk management, and cross-functional team coordination.",
    "Data engineer skilled in ETL processes, Apache Spark, big data technologies, and data warehousing.",
    "Systems administrator with knowledge in Linux, Windows Server, networking, and server management.",
    "Sales representative with strong communication skills, CRM software, and client relationship management.",
    "HR specialist experienced in recruitment, employee relations, and performance management.",
    "Financial analyst with expertise in budgeting, financial forecasting, and Excel modeling.",
    "Graphic designer skilled in Adobe Creative Suite, branding, and visual communication.",
]

JOB_DESCRIPTION_TEMPLATES = [
    "We are seeking a machine learning engineer with experience in Python, NLP, and model deployment.",
    "Looking for a data analyst who can perform data cleaning, visualization, and predictive analysis.",
    "Hiring a software engineer familiar with frontend frameworks, backend APIs, and cloud platforms.",
    "Seeking a marketing specialist with strong writing skills and digital campaign experience.",
    "We need a cybersecurity expert with knowledge in network security, encryption, and threat analysis.",
    "Looking for a DevOps engineer experienced in CI/CD pipelines, containerization, and infrastructure automation.",
    "Hiring a product manager with skills in agile methodologies, user research, and roadmap planning.",
    "Seeking a UX/UI designer proficient in prototyping tools, user testing, and design systems.",
    "We are looking for a database administrator with expertise in SQL, NoSQL, and performance optimization.",
    "Hiring a business analyst to conduct requirements gathering, process modeling, and stakeholder management.",
    "Seeking a mobile app developer with experience in iOS/Android development and cross-platform frameworks.",
    "Looking for a QA engineer skilled in automated testing, bug tracking, and quality assurance processes.",
    "We need a technical writer to create documentation, user guides, and API references.",
    "Hiring a project manager with experience in Scrum, risk management, and team coordination.",
    "Seeking a data engineer for ETL processes, big data technologies, and data warehousing.",
    "Looking for a systems administrator with knowledge in Linux, networking, and server management.",
    "We are hiring a sales representative with strong communication skills and CRM experience.",
    "Seeking a HR specialist for recruitment, employee relations, and performance management.",
    "Hiring a financial analyst with expertise in budgeting, forecasting, and financial modeling.",
    "Looking for a graphic designer skilled in Adobe Creative Suite and branding.",
]

KEYWORDS = {
    1: ["python", "machine learning", "nlp", "data analysis"],
    0: ["javascript", "cloud", "frontend", "marketing", "seo"],
}


def generate_sample_data(num_samples: int = 10000, output_path: str = "data/sample_resumes.csv"):
    rows = []
    for i in range(num_samples):
        label = random.choice([0, 1])
        resume = random.choice(RESUME_TEMPLATES)
        job_description = random.choice(JOB_DESCRIPTION_TEMPLATES)

        # Ensure some correlation but allow mismatches for variety
        if random.random() < 0.7:  # 70% chance of match
            if label == 1:
                job_description = random.choice(JOB_DESCRIPTION_TEMPLATES[:10])  # Tech jobs for positive
            else:
                job_description = random.choice(JOB_DESCRIPTION_TEMPLATES[10:])  # Non-tech for negative

        rows.append({
            "resume_text": resume,
            "job_description": job_description,
            "label": label,
        })

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["resume_text", "job_description", "label"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {num_samples} example records at {output_path}")


if __name__ == "__main__":
    generate_sample_data()
