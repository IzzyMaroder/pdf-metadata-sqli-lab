# PDF Metadata SQL Injection — Lab

An educational lab that reproduces a **SQL injection carried through the
metadata of a PDF file**. It simulates a document management system
("DocIndeX") that, on PDF upload, extracts the author from the file metadata
and stores it in a database.

The lab faithfully reproduces **two** flaws that, in the real world, often
appear together:

1. **Naive metadata parsing** — the app does not use a PDF library; it hand-scans
   the raw bytes for the first `/Author` occurrence. On a PDF edited with
   incremental-update tools (e.g. `exiftool`) this makes the payload "vanish",
   because the app reads the **old** value of the metadata.
2. **SQL concatenation** — the extracted value is placed into the query text
   with no parameterization → SQL injection.

The backend is **Microsoft SQL Server**.

> ⚠️ Intentionally vulnerable app. Use it only in an isolated environment.

---

## Running the lab

```bash
docker compose up --build
```

Then open **http://localhost:5000**.

Two containers start: the Flask app and a SQL Server instance. On first boot
SQL Server takes ~20–40 seconds to become ready; the app waits for it
automatically.

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

## The vulnerable query

In vulnerable mode the app builds the insert like this:

```sql
INSERT INTO dbo.documents (name, author) VALUES ('<file_name>', '<author_from_pdf>')
```

`<author_from_pdf>` comes from the PDF metadata: whoever uploads the file
controls every byte of that value.

---

## Attack chain

Ready-made PDFs live in `samples/`. You can also build new ones with `gen_pdf.py`.

### 1. Baseline — clean PDF

Upload `samples/00_clean.pdf` (`/Author = izzy`). The author shows up in
the archive with no errors.

### 2. Break-out — confirm the injection

Upload `samples/01_breakout.pdf` (`/Author = x'`). A single quote breaks the
query's string literal and the app returns a SQL error
(*unclosed quotation mark*). The error shown on screen confirms the metadata
lands inside the query with no sanitization.


### 3. Error-based — leak the DBMS version

Upload `samples/exploit-sql-error-based.pdf`. Its `/Author` value is:

```
x'); SELECT CAST(@@version AS INT);--
```

The forced `CAST(@@version AS INT)` fails and SQL Server puts the version string
into the error message:

```
Conversion failed when converting the nvarchar value 'Microsoft SQL Server ...' to data type int.
```

This proves arbitrary data can be read out of the database through the error
channel.

### 4. Blind — time-based confirmation

Upload `samples/exploit-sql-blind.pdf` (`x'); WAITFOR DELAY '0:0:12'--`). If the
response hangs for ~12 seconds, code execution in the query context is confirmed
even with no readable output.

### 5. Stacked insert — write attacker data

Upload `samples/exploit-stacked-insert.pdf`
(`x'); INSERT INTO dbo.documents (name,author) VALUES ('pwned','INJECTED');--`).
A new row `pwned / INJECTED` appears in the archive: arbitrary data written to
the database through a PDF metadata field.

### 6. Proof of the fix

Set `VULNERABLE=false`, restart, and re-upload any of the payload PDFs. Now the
payload is stored as a **literal value** in the author column: no error, no
version leak. The parameterized query treats the metadata as data, never as code.

---

## Purpose & license

This project exists for education and defensive research: it shows how a common
coding mistake becomes exploitable, and how to fix it. It is intentionally
vulnerable and must only be run in a local, isolated environment. Do not deploy
it on a public or shared host, and do not use these techniques against systems
you are not authorized to test.

Released under the MIT License (see `LICENSE`).
