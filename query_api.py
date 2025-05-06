import time

import requests

API_URL = "http://localhost:8000"


def ask_question(question):
    url = f"{API_URL}/ask"
    response = requests.post(url, json={"query": question})
    return response.json()


def is_server_alive():
    try:
        response = requests.get(f"{API_URL}/metadata", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False


if __name__ == "__main__":
    print("🧪 Prüfe, ob der Server läuft...")

    if not is_server_alive():
        print("❌ Der API-Server läuft nicht oder ist nicht erreichbar.")
        print("👉 Bitte stelle sicher, dass du `api_server.py` gestartet hast.")
        exit(1)

    print("✅ Server ist erreichbar.")
    print("🔄 THWS Assistent – API Modus (ENTER zum Beenden)")

    while True:
        try:
            question = input("\n❓ Frage: ").strip()
            if not question:
                print("👋 Tschüss!")
                break

            start = time.time()
            result = ask_question(question)

            print("\n📝 Frage:", result["question"])
            print("💬 Antwort:", result["answer"])
            print("🕒 Berechnungszeit (gesamt):", result["time_seconds"], "Sekunden")
            print("🔗 Quellen:")
            for src in result["sources"]:
                print(" -", src)

        except KeyboardInterrupt:
            print("\n👋 Manuell beendet. Tschüss!")
            break
        except Exception as e:
            print(f"\n⚠️ Fehler bei der Anfrage: {e}")
