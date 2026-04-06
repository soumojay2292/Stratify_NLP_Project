from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI()

# ---------------- LOAD MODEL & DATA ---------------- #

model = SentenceTransformer('all-MiniLM-L6-v2')

try:
    investors = pd.read_csv("data/investors.csv")

    required_cols = ["name", "thesis", "stage_preference"]
    for col in required_cols:
        if col not in investors.columns:
            raise ValueError(f"Missing column: {col}")

    investor_embeddings = model.encode(investors['thesis'].tolist())

except Exception as e:
    print("Error loading data:", str(e))


# ---------------- INPUT SCHEMA ---------------- #

class StartupInput(BaseModel):
    description: str
    stage: str


# ---------------- HELPERS ---------------- #

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
    return 1 if s1.lower() == s2.lower() else 0


def generate_reason(semantic, keywords, stage_score):
    reasons = []

    if semantic > 0.5:
        reasons.append("Strong semantic alignment")

    if keywords:
        reasons.append(f"Domain match ({', '.join(keywords)})")

    if stage_score:
        reasons.append("Stage compatible")

    return " + ".join(reasons) if reasons else "Low relevance"


# ---------------- MAIN API ---------------- #

@app.post("/match")
def match_startup(data: StartupInput):

    try:
        if not data.description.strip():
            raise HTTPException(status_code=400, detail="Description is empty")

        if data.stage not in ["Pre-Seed", "Seed", "Series A"]:
            raise HTTPException(status_code=400, detail="Invalid stage")

        startup_desc = data.description
        startup_stage = data.stage

        startup_embedding = model.encode(startup_desc)
        startup_keywords = extract_keywords(startup_desc)

        results = []

        for j, inv in investors.iterrows():

            investor_name = inv['name']
            investor_thesis = inv['thesis']
            investor_stage = inv['stage_preference']

            investor_embedding = investor_embeddings[j]

            # Semantic similarity
            semantic_score = float(
                cosine_similarity([startup_embedding], [investor_embedding])[0][0]
            )

            # Keyword matching
            investor_keywords = extract_keywords(investor_thesis)
            common_keywords = startup_keywords & investor_keywords

            keyword_score = float(
                len(common_keywords) / len(startup_keywords)
            ) if startup_keywords else 0.0

            # Stage match
            stage_score = float(stage_match(startup_stage, investor_stage))

            # Final score
            final_score = 0.6 * semantic_score + 0.2 * keyword_score + 0.2 * stage_score

            results.append({
                "name": investor_name,
                "score": float(round(final_score, 3)),
                "keywords": list(common_keywords),
                "reason": generate_reason(semantic_score, common_keywords, stage_score)
            })

        top_matches = sorted(results, key=lambda x: x['score'], reverse=True)[:3]

        return {"matches": top_matches}

    except Exception as e:
        print("ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))