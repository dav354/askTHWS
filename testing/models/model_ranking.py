import matplotlib.pyplot as plt
import pandas as pd

# --- Config ---
CSV_SCORED = "/Users/lelange/Uni/Projektarbeit/rag/testing/test_results_scored.csv"
CSV_RANKING = "/Users/lelange/Uni/Projektarbeit/rag/testing/model_ranking.csv"

# --- Lade die bewerteten Ergebnisse ---
df = pd.read_csv(CSV_SCORED)

# --- Finde alle Score-Spalten ---
score_cols = [col for col in df.columns if col.startswith("score_")]

# --- Berechne Durchschnittsscore pro Modell ---
ranking = []
for col in score_cols:
    model_id = col[len("score_") :]  # entfernt das "score_"-Prefix
    # Mittelwert ignoriert NaN-Werte automatisch
    avg_score = df[col].mean()
    ranking.append({"model": model_id, "average_score": avg_score})

# --- Erstelle DataFrame und sortiere absteigend ---
rank_df = pd.DataFrame(ranking).sort_values("average_score", ascending=False).reset_index(drop=True)

# --- Ausgabe auf Konsole ---
print("Modell-Rangliste (nach Durchschnittsscore):")
for i, row in rank_df.iterrows():
    print(f"{i+1}. {row['model']}: {row['average_score']:.3f}")

# --- Visualisierung der Rangliste ---
plt.figure(figsize=(10, 6))
plt.bar(rank_df["model"], rank_df["average_score"])
plt.xticks(rotation=45, ha="right")
plt.ylabel("Durchschnittlicher Score")
plt.title("Modell-Rangliste nach Durchschnittsscore")
plt.tight_layout()
plt.show()
