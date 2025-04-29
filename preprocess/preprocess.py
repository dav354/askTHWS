import json
import os
import sys
import uuid

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langdetect import DetectorFactory, detect
from tqdm import tqdm

# Make langdetect deterministic
DetectorFactory.seed = 42


def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python preprocess_and_chunk.py <input_file.jsonl>")
        sys.exit(1)

    input_path = sys.argv[1]
    if not os.path.isfile(input_path):
        print(f"❌ File not found: {input_path}")
        sys.exit(1)

    output_path = input_path.replace(".jsonl", "_chunks.jsonl")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    total_docs = 0
    total_chunks = 0

    with (
        open(input_path, "r", encoding="utf-8") as fin,
        open(output_path, "w", encoding="utf-8") as fout,
    ):
        for line in tqdm(fin, desc="🔄 Chunking"):
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                continue

            text = doc.get("text", "").strip()
            if not text:
                continue

            try:
                lang = detect(text)
            except Exception:
                lang = "unknown"

            metadata = {
                "source": doc.get("url"),
                "title": doc.get("title"),
                "type": doc.get("type"),
                "date_updated": doc.get("date_updated"),
                "lang": lang,
            }

            for chunk_text in splitter.split_text(text):
                chunk = {
                    "chunk_id": str(uuid.uuid4()),
                    "text": chunk_text,
                    "metadata": metadata,
                }
                fout.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                total_chunks += 1

            total_docs += 1

    print(f"🔍 Processed {total_docs} documents")
    print(f"✅ Saved {total_chunks} chunks → {output_path}")


if __name__ == "__main__":
    main()
