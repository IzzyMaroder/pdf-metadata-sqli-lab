#!/usr/bin/env python3
"""
PDF Metadata SQL Injection - Test Lab
=====================================

Intentionally vulnerable app for educational purposes. It simulates a document
management system that, on PDF upload, extracts the author from the file's
metadata and "indexes" it into a database - concatenating the value straight
into the SQL query.

VULNERABLE toggle (environment variable):
  VULNERABLE=true  (default) -> concatenated query, injection present
  VULNERABLE=false           -> parameterized query, injection closed

Do NOT run outside an isolated test environment.
"""

import os
import re
import time

import pymssql
from flask import Flask, render_template, request, flash, redirect, url_for

# ---- Database configuration (MSSQL) -------------------------------------
DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = int(os.environ.get("DB_PORT", "1433"))
DB_USER = os.environ.get("DB_USER", "sa")
DB_PASS = os.environ.get("DB_PASS", "Str0ng!Passw0rd")
DB_NAME = os.environ.get("DB_NAME", "docindex")

#Toggle: vulnerable by default. Set VULNERABLE=false for the fixed version.
VULNERABLE = os.environ.get("VULNERABLE", "true").lower() != "false"

app = Flask(__name__)
app.secret_key = "lab-secret-not-for-production"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


def get_conn(database=DB_NAME):
    """Open a connection to SQL Server."""
    return pymssql.connect(
        server=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASS, database=database, autocommit=True,
    )


def init_db(retries=30, delay=2):
    last_err = None
    for _ in range(retries):
        try:
            conn = get_conn(database="master")
            cur = conn.cursor()
            cur.execute(
                "IF DB_ID('%s') IS NULL CREATE DATABASE [%s]" % (DB_NAME, DB_NAME)
            )
            conn.close()

            conn = get_conn()
            cur = conn.cursor()
            cur.execute(
                """
                IF OBJECT_ID('dbo.documents', 'U') IS NULL
                CREATE TABLE dbo.documents (
                    id     INT IDENTITY(1,1) PRIMARY KEY,
                    name   NVARCHAR(400),
                    author NVARCHAR(400)
                )
                """
            )
            conn.close()
            print("[init_db] database ready")
            return
        except pymssql.Error as e:
            last_err = e
            time.sleep(delay)
    raise RuntimeError("Database not reachable: %s" % last_err)


def extract_author_naive(pdf_bytes: bytes) -> str:
    
    m = re.search(rb"/Author\s*\(", pdf_bytes)
    if not m:
        return ""

    i = m.end()
    out = bytearray()
    depth = 0
    n = len(pdf_bytes)
    while i < n:
        c = pdf_bytes[i]
        if c == 0x5C and i + 1 < n: 
            out.append(pdf_bytes[i + 1])
            i += 2
            continue
        if c == 0x28:                        
            depth += 1
            out.append(c)
        elif c == 0x29:                     
            if depth == 0:
                break                        
            depth -= 1
            out.append(c)
        else:
            out.append(c)
        i += 1

    return bytes(out).decode("latin-1", errors="replace")


def index_document(name: str, author: str):

    conn = get_conn()
    cur = conn.cursor()

    if VULNERABLE:
        # ---- VULNERABLE VERSION ------------------------------------------
        #The /Author metadata value goes straight into the SQL text.
        query = (
            "INSERT INTO dbo.documents (name, author) "
            "VALUES ('%s', '%s')" % (name, author)
        )
        cur.execute(query)
    else:
        # ---- FIXED VERSION -----------------------------------------------
        #Parameterized query: the value is always treated as data, never as
        #SQL code.
        cur.execute(
            "INSERT INTO dbo.documents (name, author) VALUES (%s, %s)",
            (name, author),
        )

    conn.close()


@app.route("/", methods=["GET"])
def home():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT TOP 20 id, name, author FROM dbo.documents ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return render_template("index.html", documents=rows, vulnerable=VULNERABLE)


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("pdf")

    if not file or file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("home"))

    if not file.filename.lower().endswith(".pdf"):
        flash("Only PDF files are allowed.", "error")
        return redirect(url_for("home"))

    pdf_bytes = file.read()
    if not pdf_bytes.startswith(b"%PDF"):
        flash("The file does not look like a valid PDF.", "error")
        return redirect(url_for("home"))

    author = extract_author_naive(pdf_bytes)

    try:
        index_document(file.filename, author)
    except pymssql.Error as e:
        flash("Error while indexing the document: %s" % (e,), "error")
        return redirect(url_for("home"))

    flash("Document indexed. Extracted author: %r" % author, "success")
    return redirect(url_for("home"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
