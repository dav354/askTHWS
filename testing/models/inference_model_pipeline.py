import time

import pandas as pd
import requests
import torch
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# --- Config ---
CSV_INPUT = "/Users/lelange/Uni/Projektarbeit/rag/testing/fragenkatalog_2904.csv"
CSV_OUTPUT = "/Users/lelange/Uni/Projektarbeit/rag/testing/test_results_scored.csv"
API_URL = "http://localhost:11434/api/generate"
EVAL_MODEL = "gemma3:27b"
COLLECTION = "thws_data2_chunks"
QDRANT_URL = "http://localhost:6333"
EMBED_MODEL = "BAAI/bge-m3"
MODELS = {
    "gemma:7b": "answer_gemma7b",
    "orca-mini:7b": "answer_orca-mini7b",
    "mistral:latest": "answer_mistral_latest",
    "phi4:latest": "answer_phi4_latest",
    "qwen2.5:14b": "answer_qwen2_5_14b",
    "orca-mini:13b": "answer_orca-mini_13b",
    "gemma3:27b": "answer_gemma3_27b",
    "deepseek-r1:32b": "answer_deepseek_r1_32b",
    "qwq:latest": "answer_qwq_latest",
}
TOP_K = 3

# --- Device für Embeddings ---
if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available() and torch.backends.mps.is_built():
    device = "mps"
else:
    device = "cpu"
print(f"🔥 Using device: {device}")

# --- Init Embedder & Qdrant-Client ---
embedder = SentenceTransformer(EMBED_MODEL, device=device)
client = QdrantClient(url=QDRANT_URL)

df = pd.read_csv(CSV_INPUT)
# --- Filtere nur gültige Fragen mit existierender Frage und Antwort ---
df = df.dropna(subset=["Question", "Answer"])
df = df[df["Question"].astype(str).str.strip() != ""]
df = df[df["Answer"].astype(str).str.strip() != ""]

results = []

for _, row in df.iterrows():
    question = row["Question"]
    correct_ans = row.get("Answer", "")
    print(f"\n--- Verarbeite Frage ID {row['Id']}")

    # 1) Embed Query
    q_vec = embedder.encode(question, device=device)
    # 2) Suche in Qdrant
    hits = client.search(
        collection_name=COLLECTION,
        query_vector=q_vec.tolist(),
        limit=TOP_K,
        with_payload=True,
    )

    # Dedupliziere nach Quelle
    unique = {}
    for hit in hits:
        src = hit.payload["source"]
        if src not in unique:
            unique[src] = hit
    context = "\n\n".join(h.payload["text"] for h in unique.values())
    row_source = row.get("URL / Dokument", "")

    # Bereite Ergebnis-Dict vor
    record = {
        "question": question,
        "correct_answer": correct_ans,
        "source": row_source,
    }

    # 3) Für jedes Modell einmal antworten
    for model_name, col_name in MODELS.items():
        print(f"Rufe Modell {model_name} auf...")
        prompt = f"""
Du bist ein hochintelligenter und präziser Assistent der Hochschule THWS.
Nutze ausschließlich die unten stehenden Kontextinformationen, um die Frage zu beantworten.
Wenn der Kontext nicht ausreicht oder irgendwas komisch ist (kein Frage, kein Kontext etc.), antworte mit "Diese Frage kann ich leider nicht beantworten."

1. Fasse in 1–2 Sätzen zusammen, wie du die Antwort aus dem Kontext abgeleitet hast.
2. Gib die Antwort klar und präzise in vollständigen Sätzen auf Deutsch.
3. Am Ende unter "Quelle(n):" liste alle verwendeten Kontextquellen mit kurzer Angabe (z. B. Titel oder Dokumentabschnitt).

Kontext:
{context}

Frage:
{question}

Antwort:
"""
        start_time = time.time()
        resp = requests.post(
            API_URL,
            json={"model": model_name, "prompt": prompt, "stream": False},
        )
        answer = resp.json().get("response", "").strip()
        duration = time.time() - start_time
        record[f"{col_name}_time"] = duration
        record[col_name] = answer
        print(f"[{model_name}] Dauer: {duration:.2f} Sekunden")

    # Bewertung der Modellantworten
    for model_name, col_name in MODELS.items():
        model_id = col_name[len("answer_") :]
        score_col = f"score_{model_id}"
        model_ans = record[col_name]

        prompt = f"""
Du evaluierst die Modellantwort im direkten Vergleich zur korrekten Antwort anhand folgender Kriterien:
1. Korrektheit: Sind die Fakten und Informationen in der Modellantwort korrekt im Vergleich zur richtigen Antwort?
2. Vollständigkeit: Deckt die Modellantwort alle wesentlichen Aspekte der richtigen Antwort ab?
3. Präzision: Ist die Antwort klar, genau und frei von irrelevanten Details?
4. Konsistenz: Ergibt die Antwort einen sinnvollen, logisch widerspruchsfreien Gesamtzusammenhang?

Gib einen numerischen Score zwischen 0.00 (keine Übereinstimmung) und 1.00 (vollständige Übereinstimmung) zurück. 
Nenne ausschließlich die Zahl im Format 0.XX, ohne weiteren Text.

Frage:
{question}

Korrekte Antwort:
{correct_ans}

Modell-Antwort:
{model_ans}
"""
        resp = requests.post(API_URL, json={"model": EVAL_MODEL, "prompt": prompt, "stream": False})
        out = resp.json().get("response", "").strip()
        try:
            score = float(out)
        except ValueError:
            print(f"⚠️ Konnte Score nicht parsen: „{out}“. Setze auf NaN.")
            score = pd.NA
        record[score_col] = score
        print(f"[{model_id}] Score={score}")

    results.append(record)

# 4) Schreibe Ergebnis-CSV
print("Schreibe Ergebnisse in:", CSV_OUTPUT)
pd.DataFrame(results).to_csv(CSV_OUTPUT, index=False, encoding="utf-8-sig")
print(f"✅ Fertig! Ergebnisse in »{CSV_OUTPUT}«.")
