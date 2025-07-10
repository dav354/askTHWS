

This project builds **vector databases** from **scraped content** in MongoDB. It supports **text extraction**, **preprocessing**, and **language filtering**.

---

## ✅ Installation

1. **Install Poetry**

2. **Install dependencies**:

```bash
poetry install --no-root
```

---

## 🔧 Configuration

The system is configured entirely via **environment variables**. You can either export them or use a `.env` file.

### Core Options


| `LANGUAGE`                    | `all`, `de`, or `en` – filters documents by language metadata                          | `all`           |


---

## 🛠 Usage

### Build vector DBs

```bash
poetry run python build_dbs.py
```



### Build for a specific subdomain

You need to replace all `dots` with an `underscore` for the subdomains.

```bash
poetry run python build_dbs.py --subdomain fiw_thws_de --subdomain www_thws_de
```




---

## 🧹 What the pipeline does

### 1. **Load documents from MongoDB**

* Connects to two MongoDB collections: `pages` (HTML) and `files` (PDF).
* Filters by `LANGUAGE` setting (if not `all`).
* Extracts content:

  * `HTML` → converted to clean **Markdown**
  * `PDF` → converted to plain **text** via `PyMuPDF`

### 2. **Clean & sanitize**

* Filters out empty or broken documents
* Removes null characters and unwanted whitespace
* Organizes docs by **subdomain** (from URL)

### 3. **Vectorization**

All documents are indexed into a unified vector DB.

---



---

## 📁 Output

All output is stored in the `RAG_STORAGE` directory:

```
RAG_STORAGE/
├── vectors/             ← unified vector DB
```

---

Let me know if you'd like this rendered into a real `README.md` file, or if you want a `make` or bash script for easier running.
