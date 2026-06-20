def create_pdf(article):
    # Small dependency-free PDF writer for portable deployments.
    text = [article["title"], f"{article['source']} | {article['date']}", "", article["summary"], "", "Keywords: " + ", ".join(article["keywords"])]
    escaped = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in text]
    stream = "BT /F1 16 Tf 60 760 Td " + " Tj 0 -24 Td ".join(f"({line[:105]})" for line in escaped) + " Tj ET"
    objects = ["1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj", "2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj", "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Resources<</Font<</F1 5 0 R>>>>/Contents 4 0 R>>endobj", f"4 0 obj<</Length {len(stream)}>>stream\n{stream}\nendstream endobj", "5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj"]
    pdf = "%PDF-1.4\n"; offsets = [0]
    for obj in objects: offsets.append(len(pdf.encode())); pdf += obj + "\n"
    xref = len(pdf.encode()); pdf += f"xref\n0 6\n0000000000 65535 f \n" + "".join(f"{o:010d} 00000 n \n" for o in offsets[1:])
    pdf += f"trailer<</Size 6/Root 1 0 R>>\nstartxref\n{xref}\n%%EOF"
    return pdf.encode("latin-1", errors="replace")

