import time

import pandas as pd
import requests

# --- Config ---
CSV_PATH_OLD = "/Users/lelange/Uni/Projektarbeit/rag/testing/test_results.csv"
CSV_PATH_NEW = "/Users/lelange/Uni/Projektarbeit/rag/testing/test_results_scored.csv"
API_URL = "http://localhost:11434/api/generate"
EVAL_MODEL = "gemma3:27b"

# --- Lade Ergebnisse ---
df = pd.read_csv(CSV_PATH_OLD)

# --- Identifiziere alle Antwort-Spalten ---
answer_cols = [c for c in df.columns if c.startswith("answer_")]

# --- Initialisiere Score-Spalten ---
for c in answer_cols:
    model_id = c[len("answer_") :]  # z.B. "gemma7b"
    score_col = f"score_{model_id}"
    df[score_col] = pd.NA

# --- Für jede Zeile & jedes Modell eine Bewertung abfragen ---
for idx, row in df.iterrows():
    question = row["question"]
    correct_ans = row["correct_answer"]
    print(f"\n--- Bewerte Zeile {idx}: Frage „{question}“")

    for c in answer_cols:
        model_id = c[len("answer_") :]
        score_col = f"score_{model_id}"
        model_ans = row[c]

        prompt = f"""
Du bist ein sachkundiger Evaluator und kennst dich mit Bewertungsmetriken aus.
Gib einen numerischen Score zwischen 0 (gar nicht korrekt) und 1 (perfekt korrekt) zurück.
Nenne nur die Zahl im Format 0.XX, ohne weiteren Text.

Frage:
{question}

Korrekte Antwort:
{correct_ans}

Modell-Antwort:
{model_ans}

Score:
"""
        # Zeitmessung starten
        start = time.time()

        # Anfrage
        resp = requests.post(
            API_URL,
            json={"model": EVAL_MODEL, "prompt": prompt, "stream": False},
        )
        out = resp.json().get("response", "").strip()

        # Versuche, das Ergebnis als Float zu parsen
        try:
            score = float(out)
        except ValueError:
            print(f"⚠️ Konnte Score nicht parsen: „{out}“. Setze auf NaN.")
            score = pd.NA

        duration = time.time() - start
        print(f"[{model_id}] Score={score} (in {duration:.2f}s)")

        # Schreibe zurück ins DataFrame
        df.at[idx, score_col] = score

# --- Schreibe aktualisierte CSV ---
df.to_csv(CSV_PATH_NEW, index=False, encoding="utf-8-sig")
print("\n✅ Alle Scores berechnet und in", CSV_PATH_NEW, "gespeichert.")
