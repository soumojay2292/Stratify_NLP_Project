import streamlit as st
import requests

st.title(" STRATIFY - Investor Matchmaking")

description = st.text_area("Enter Startup Description")
stage = st.selectbox("Select Stage", ["Pre-Seed", "Seed", "Series A"])

if st.button("Find Investors"):
    data = {
        "description": description,
        "stage": stage
    }

    response = requests.post("http://127.0.0.1:8000/match", json=data)

    if response.status_code == 200:
        results = response.json()["matches"]

        st.subheader("Top Matches")

        for i, match in enumerate(results, 1):
            st.write(f"### {i}. {match['name']}")
            st.write(f"Score: {match['score']}")
            st.write(f"Keywords: {match['keywords']}")
    else:
        st.error("Something went wrong")