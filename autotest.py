import re
import time
from datetime import datetime

import requests

MARKDOWN_FILE = "docs/tests/fragen.md"
API_URL = "http://localhost:8000/ask"
METADATA_URL = "http://localhost:8000/metadata"


# --- Extract Questions from Markdown ---
def extract_questions(md_file):
    with open(md_file, "r", encoding="utf-8") as file:
        content = file.read()
    questions = re.findall(r"-\s+(.*?)\?", content)
    return [q.strip() + "?" for q in questions]


# --- Query the API ---
def query_api(question):
    response = requests.post(API_URL, json={"query": question})
    return response.json()


# --- Get metadata from API ---
def get_metadata():
    response = requests.get(METADATA_URL)
    return response.json()


# --- Write Header to Result File ---
def write_header(f, metadata):
    commit_link = f"[Version](/commit/{metadata['commit_hash']})"
    f.write(f"{commit_link}\n\n")
    f.write("# Automatischer Testlauf\n\n")
    f.write(f"Modell: {metadata['model']}\n")
    f.write(f"GPU/Device: {metadata['device']}\n")
    f.write("Kein Cherry Picking, Antworten aus erstem Lauf\n\n")
    f.write("---\n")


# --- Save Single Result Incrementally ---
def save_result(f, question, duration, res):
    f.write(f"\n#### {question}\n\n")
    f.write(f"{duration}s\n\n")
    f.write("```\n")
    f.write(res["answer"] + "\n")
    f.write("\n🔗 Quellen:\n")
    for src in res["sources"]:
        f.write(f"- {src}\n")
    f.write("```\n")
    f.write("\n---\n")
    f.flush()


# --- Main Testing Routine ---
def run_tests():
    metadata = get_metadata()
    questions = extract_questions(MARKDOWN_FILE)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    result_file = f"test_results_{timestamp}.md"

    with open(result_file, "w", encoding="utf-8") as f:
        write_header(f, metadata)

        for q in questions:
            print(f"🔍 Frage: {q}")
            start = time.time()
            res = query_api(q)
            duration = round(time.time() - start, 2)

            save_result(f, q, duration, res)

    print(f"\n✅ Test abgeschlossen. Ergebnisse gespeichert in: {result_file}")


# --- Run the script ---
if __name__ == "__main__":
    run_tests()
