from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI()

# Load model and data
model = SentenceTransformer('all-MiniLM-L6-v2')
investors = pd.read_csv("data/investors.csv")
investor_embeddings = model.encode(investors['thesis'].tolist())

class StartupInput(BaseModel):
    description: str
    stage: str

def extract_keywords(text):
    text = text.lower()

    keyword_groups = {
        "ai": ["ai", "artificial intelligence"],
        "healthcare": ["health", "hospital", "medical"],
        "fintech": ["fintech", "payment", "finance"],
        "energy": ["energy", "renewable"],
        "education": ["education", "learning", "student"],
        "agriculture": ["agriculture", "farming", "crop"]
    }

    found = set()
    for key, variations in keyword_groups.items():
        for word in variations:
            if word in text:
                found.add(key)

    return found

def stage_match(s1, s2):
    return 1 if s1 == s2 else 0

@app.post("/match")
def match_startup(data: StartupInput):
    startup_desc = data.description
    startup_stage = data.stage

    startup_embedding = model.encode(startup_desc)
    results = []

    for j, inv in investors.iterrows():
        investor_name = inv['name']
        investor_thesis = inv['thesis']
        investor_stage = inv['stage_preference']

        investor_embedding = investor_embeddings[j]

        semantic_score = cosine_similarity(
            [startup_embedding], [investor_embedding])[0][0]

        startup_keywords = extract_keywords(startup_desc)
        investor_keywords = extract_keywords(investor_thesis)
        common_keywords = startup_keywords & investor_keywords

        keyword_score = len(common_keywords) / len(startup_keywords) if startup_keywords else 0
        stage_score = stage_match(startup_stage, investor_stage)

        final_score = 0.6*semantic_score + 0.2*keyword_score + 0.2*stage_score

        results.append({
            "name": investor_name,
            "score": round(final_score, 3),
            "keywords": list(common_keywords)
        })

    top_matches = sorted(results, key=lambda x: x['score'], reverse=True)[:3]

    return {"matches": top_matches}            