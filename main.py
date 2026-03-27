import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

def extract_keywords(text):
    text = text.lower()

    keyword_groups = {
        "ai": ["ai", "artificial intelligence"],
        "healthcare": ["health", "healthcare", "hospital", "medical"],
        "fintech": ["fintech", "finance", "payment", "banking"],
        "energy": ["energy", "renewable", "climate"],
        "education": ["education", "learning", "student", "edtech"],
        "agriculture": ["agriculture", "farming", "crop"]
    }

    found = set()

    for key, variations in keyword_groups.items():
        for word in variations:
            if word in text:
                found.add(key)

    return found

def stage_match(startup_stage, investor_stage):
    return 1 if startup_stage == investor_stage else 0

# Load data
startups = pd.read_csv("data/startups.csv")
investors = pd.read_csv("data/investors.csv")

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Convert investor text to embeddings
investor_embeddings = model.encode(investors['thesis'].tolist())

# Matching function
def match_startups():
    for i, row in startups.iterrows():
        startup_name = row['name']
        startup_desc = row['description']
        startup_stage = row['stage']

        startup_embedding = model.encode(startup_desc)

        results = []

        for j, inv in investors.iterrows():
            investor_name = inv['name']
            investor_thesis = inv['thesis']
            investor_stage = inv['stage_preference']

            investor_embedding = investor_embeddings[j]

            # Semantic score
            semantic_score = cosine_similarity(
                [startup_embedding], [investor_embedding])[0][0]

            # Keywords
            startup_keywords = extract_keywords(startup_desc)
            investor_keywords = extract_keywords(investor_thesis)
            common_keywords = startup_keywords & investor_keywords

            if len(startup_keywords) == 0:
                keyword_score = 0
            else:
                keyword_score = len(common_keywords) / len(startup_keywords)

            # Stage
            stage_score = stage_match(startup_stage, investor_stage)

            # Final score
            final_score = (
                0.6 * semantic_score +
                0.2 * keyword_score +
                0.2 * stage_score
            )

            results.append({
                "name": investor_name,
                "score": final_score,
                "keywords": common_keywords
            })

        # Sort top 3
        top_matches = sorted(results, key=lambda x: x['score'], reverse=True)[:3]

        # PRINT OUTPUT
        print("\n=============================")
        print("Startup:", startup_name)
        print("Stage:", startup_stage)
        print("Description:", startup_desc)

        print("\nTop Matches:")

        for idx, match in enumerate(top_matches, 1):
            print(f"\n{idx}. Investor:", match['name'])
            print("   Score:", round(match['score'], 3))
            print("   Matching Keywords:", match['keywords'])
            if match['score'] > 0.6:
                base = "High semantic alignment"
            elif match['score'] > 0.4:
                base = "Moderate semantic alignment"
            else:
                base = "Weak semantic alignment"

            if len(match['keywords']) > 0:
                base += " + domain match (" + ", ".join(match['keywords']) + ")"
            print("   Reason:", base)
# Run
if __name__ == "__main__":
    match_startups()