# app.py
import streamlit as st
from inference import get_context, query_model

st.set_page_config(page_title="THWS Chatbot (Prototyp)", layout="centered")

st.title("🎓 THWS Chatbot (Prototyp)")
st.write("Gib deine Frage ein, und der Bot sucht im THWS-Kontext und antwortet.")

# Eingabe
question = st.text_input("Frage:", placeholder="z. B. Wie melde ich mich für Prüfungen an?")

# Auswahl Modell (optional)
model = st.selectbox("Modell:", ["gemma3:27b", "orca-mini:7b", "mistral:latest"])

if st.button("Absenden") and question.strip():
    with st.spinner("Suche Kontext…"):
        context = get_context(question)
    if not context:
        st.warning("Kein Kontext gefunden. Frage bitte anders formulieren.")
    else:
        st.markdown("**⌛ Kontext:**")
        st.text_area("", context, height=200)

        with st.spinner("Hole Antwort…"):
            answer = query_model(question, context, model_name=model)

        st.markdown("**💬 Antwort:**")
        st.success(answer)
