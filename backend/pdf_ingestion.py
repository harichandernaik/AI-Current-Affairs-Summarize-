import re
from datetime import date
from io import BytesIO
from uuid import uuid4

try:
    from .nlp_service import analyze, category_scores
except ImportError:
    from nlp_service import analyze, category_scores


def _extract_with_pypdf(data):
    from pypdf import PdfReader
    reader = PdfReader(BytesIO(data))
    pages = [(page.extract_text(extraction_mode="layout") or "") for page in reader.pages]
    return "\n\n".join(pages), len(reader.pages), "pypdf"


def _extract_with_pdfplumber(data):
    import pdfplumber
    with pdfplumber.open(BytesIO(data)) as pdf:
        pages = [(page.extract_text() or "") for page in pdf.pages]
        return "\n\n".join(pages), len(pdf.pages), "pdfplumber"


def _extract_with_pymupdf(data):
    import fitz
    doc = fitz.open(stream=data, filetype="pdf")
    pages = [page.get_text("text") or "" for page in doc]
    return "\n\n".join(pages), doc.page_count, "PyMuPDF"


def extract_pdf_text(data):
    errors = []
    for extractor in (_extract_with_pypdf, _extract_with_pdfplumber, _extract_with_pymupdf):
        try:
            text, pages, engine = extractor(data)
            if len(text.strip()) >= 200:
                return text, pages, engine
            errors.append(f"{engine}: no searchable text")
        except Exception as exc:
            errors.append(f"{extractor.__name__.replace('_extract_with_', '')}: {exc}")
    raise ValueError("No readable text could be extracted. Upload a searchable PDF under 25 MB; scanned image PDFs need OCR before upload.")


def _looks_like_heading(line):
    words = line.split()
    if not 4 <= len(words) <= 18 or len(line) > 145 or line.endswith((".", ",", ";", ":")):
        return False
    letters = [c for c in line if c.isalpha()]
    if not letters:
        return False
    upper_ratio = sum(c.isupper() for c in letters) / len(letters)
    title_ratio = sum(w[:1].isupper() for w in words) / len(words)
    return upper_ratio > 0.65 or title_ratio > 0.72


def split_articles_from_text(text, min_chars=350):
    text = re.sub(r"[ \t]+", " ", text.replace("\r", "\n"))
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    sections, current = [], []
    for line in lines:
        if _looks_like_heading(line) and len(" ".join(current)) >= min_chars:
            sections.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append(current)

    merged, carry = [], []
    for section in sections:
        carry += section
        if len(" ".join(carry)) >= min_chars:
            merged.append(carry)
            carry = []
    if carry and merged:
        merged[-1] += carry
    elif carry:
        merged.append(carry)

    results = []
    for lineset in merged:
        block = " ".join(lineset)
        if len(block) < min_chars:
            continue
        title = lineset[0][:140] if _looks_like_heading(lineset[0]) else " ".join(block.split()[:12]).rstrip(".,")
        body = block[len(lineset[0]):].strip() if title == lineset[0][:140] else block
        if len(body) >= min_chars:
            results.append({"title": title, "content": body})
    return results


def normalize_title(value):
    cleaned = re.sub(r"[^a-z0-9 ]+", " ", value.lower())
    cleaned = re.sub(r"\b(the|a|an|and|or|to|of|in|on|for|with|by|from|new|india|indian)\b", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def content_fingerprint(value, words=80):
    tokens = re.findall(r"[a-z0-9]+", value.lower())
    return " ".join(tokens[:words])


def subject_summaries(created):
    result = {}
    for article in created:
        category = article.get("category", "Polity")
        bucket = result.setdefault(category, {"count": 0, "summaries": []})
        bucket["count"] += 1
        bucket["summaries"].append(article.get("shortSummary") or article.get("summary", ""))
    return result


def ingest_newspaper_pdf(data, filename, source, publication_date, repo):
    text, pages, engine = extract_pdf_text(data)
    candidates = split_articles_from_text(text)
    batch = uuid4().hex[:10]
    created, ignored = [], 0
    seen_titles, seen_content = set(), set()
    for candidate in candidates:
        title_key = normalize_title(candidate["title"])
        content_key = content_fingerprint(candidate["content"])
        if title_key in seen_titles or content_key in seen_content:
            ignored += 1
            continue
        seen_titles.add(title_key)
        seen_content.add(content_key)
        scores = category_scores(f"{candidate['title']} {candidate['content']}")
        if max(scores.values()) == 0 or repo.exists(candidate["title"], publication_date):
            ignored += 1
            continue
        created.append(repo.create({
            "title": candidate["title"],
            "content": candidate["content"],
            "source": source,
            "date": publication_date or date.today().isoformat(),
            "sourceType": "newspaper-pdf",
            "sourceFile": filename,
            "importBatch": batch,
            **analyze(candidate["title"], candidate["content"]),
        }))
    repo.record_pdf_upload({
        "filename": filename,
        "source": source,
        "date": publication_date,
        "pages": pages,
        "engine": engine,
        "createdCount": len(created),
        "ignoredCount": ignored,
        "batch": batch,
    })
    return {
        "created": created,
        "createdCount": len(created),
        "ignoredCount": ignored,
        "detectedCount": len(candidates),
        "pages": pages,
        "engine": engine,
        "batch": batch,
        "subjectSummaries": subject_summaries(created),
    }
