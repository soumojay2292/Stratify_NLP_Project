import streamlit as st
import requests

st.set_page_config(page_title="Stratify AI", layout="wide")

# ---------- HEADER ---------- #
st.markdown("""
# 🚀 STRATIFY AI
### Intelligent Startup–Investor Matchmaking
""")

# ---------- INPUT SECTION ---------- #
col1, col2 = st.columns(2)

with col1:
    description = st.text_area("🧠 Startup Description")

with col2:
    stage = st.selectbox("📊 Funding Stage", ["Pre-Seed", "Seed", "Series A"])


# ---------- HELPERS ---------- #
def get_score_color(score):
    if score > 0.6:
        return "🟢"
    elif score > 0.4:
        return "🟡"
    else:
        return "🔴"

def get_label(score):
    if score > 0.6:
        return "🔥 Strong Match"
    elif score > 0.4:
        return "👍 Good Match"
    else:
        return "⚠️ Weak Match"


# ---------- BUTTON ---------- #
if st.button("🔍 Find Investors"):
    with st.spinner("🔍 Analyzing and matching investors..."):

        data = {
            "description": description,
            "stage": stage
        }

        try:
            response = requests.post("http://127.0.0.1:8000/match", json=data)

            if response.status_code == 200:
                results = response.json()["matches"]

                st.success("🎯 Top Investor Matches Found!")

                # ---------- BEST MATCH ---------- #
                top = results[0]

                st.markdown("## 🏆 Best Match")

                with st.container():
                    st.markdown(f"### {top['name']}")
                    st.progress(float(top['score']))

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric("Score", top['score'])

                    with col2:
                        st.write(get_label(top['score']))

                    st.write(f"**Keywords:** {', '.join(top['keywords']) if top['keywords'] else 'None'}")
                    st.write(f"**Reason:** {top['reason']}")

                st.divider()

                # ---------- OTHER MATCHES ---------- #
                st.markdown("## 📊 Other Matches")

                for match in results[1:]:
                    color = get_score_color(match['score'])

                    with st.container():
                        st.markdown(f"### {color} {match['name']}")
                        st.progress(float(match['score']))

                        col1, col2 = st.columns(2)

                        with col1:
                            st.metric("Score", match['score'])

                        with col2:
                            st.write(get_label(match['score']))

                        st.write(f"**Keywords:** {', '.join(match['keywords']) if match['keywords'] else 'None'}")
                        st.write(f"**Reason:** {match['reason']}")

                        st.divider()

            else:
                st.error(f"Error: {response.status_code}")
                st.write(response.text)

        except Exception as e:
            st.error("⚠️ Backend connection failed")
            st.write(str(e))