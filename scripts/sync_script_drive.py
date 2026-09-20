#!/usr/bin/env python3
"""Publish the canonical POLOP script to one Google Doc and one PDF in Drive.

GitHub is the source of truth. The Google service account key belongs only
in GitHub Actions secrets (GDRIVE_SA_KEY).
"""
import io
import json
import os
import sys
from xml.sax.saxutils import escape
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

FOLDER_ID = "1A5LpnJh_c7cPe0xprY_r9jDFowu48tLc"
DOC_ID = "1gzZ5zgLaNcuPdH4M4pfohNSP_WisfYYy6_2E0_db_fs"
PDF_NAME = "Script_POLOP.pdf"
SOURCE = Path("Script_POLOP.md")

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]


def credentials():
    """Build credentials from the service account key stored in GitHub secrets."""
    raw = os.environ.get("GDRIVE_SA_KEY", "").strip()
    if not raw:
        raise RuntimeError(
            "Secret GDRIVE_SA_KEY absent ou vide. "
            "Ouvrir Settings > Secrets and variables > Actions > Repository secrets "
            "et coller le contenu exact du fichier de clé JSON du compte de service."
        )
    try:
        info = json.loads(raw)
    except json.JSONDecodeError:
        raise RuntimeError(
            "GDRIVE_SA_KEY ne contient pas un JSON valide. "
            "Coller le contenu exact du fichier de clé téléchargé depuis "
            "Google Cloud (IAM et administration > Comptes de service > Clés)."
        ) from None

    missing = [k for k in ("client_email", "private_key", "token_uri") if not info.get(k)]
    if missing:
        raise RuntimeError(
            "GDRIVE_SA_KEY est un JSON incomplet, champ(s) manquant(s) : "
            + ", ".join(missing)
            + ". Retélécharger la clé JSON depuis Google Cloud."
        )

    print("Compte de service :", info["client_email"], flush=True)
    try:
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    except ValueError as exc:
        raise RuntimeError(
            "Impossible de construire les identifiants à partir de GDRIVE_SA_KEY : "
            + str(exc)
        ) from None
    return creds


def render_markdown(source):
    """Keep every source line, stripping Markdown display syntax only where safe."""
    paragraphs = []
    for line in source.splitlines():
        if line.startswith("### "):
            paragraphs.append(("HEADING_3", line[4:]))
        elif line.startswith("## "):
            paragraphs.append(("HEADING_2", line[3:]))
        elif line.startswith("# "):
            paragraphs.append(("HEADING_1", line[2:]))
        else:
            paragraphs.append(("NORMAL_TEXT", line))
    # Source may not end in a newline; Docs requires a final paragraph break.
    output = "\n".join(text for _, text in paragraphs).rstrip("\n") + "\n"
    styles = []
    offset = 1
    for kind, line in paragraphs:
        if kind != "NORMAL_TEXT":
            styles.append({"updateParagraphStyle": {
                "range": {"startIndex": offset, "endIndex": offset + len(line) + 1},
                "paragraphStyle": {"namedStyleType": kind},
                "fields": "namedStyleType",
            }})
        offset += len(line) + 1
    return output, styles


def publish_doc(text, drive, docs):
    """Update the existing native Google Doc; never create a Markdown file."""
    metadata = drive.files().get(
        fileId=DOC_ID, fields="id,name,mimeType,parents", supportsAllDrives=True
    ).execute()
    if (metadata.get("mimeType") != "application/vnd.google-apps.document"
            or FOLDER_ID not in metadata.get("parents", [])):
        raise RuntimeError("Google Doc cible absent du dossier prévu ou de mauvais format.")

    old = docs.documents().get(documentId=DOC_ID).execute()
    content = old.get("body", {}).get("content", [])
    end_index = content[-1]["endIndex"] if content else 2
    rendered, style_requests = render_markdown(text)
    requests = []
    if end_index > 2:
        requests.append({"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end_index - 1}}})
    requests.append({"insertText": {"location": {"index": 1}, "text": rendered}})
    requests.extend(style_requests)
    docs.documents().batchUpdate(documentId=DOC_ID, body={"requests": requests}).execute()
    print("Google Docs publié : https://docs.google.com/document/d/" + DOC_ID + "/edit", flush=True)


def build_pdf(text):
    """Render a fresh PDF from GitHub source, independently of the Google Doc."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    pdfmetrics.registerFont(TTFont("PolopSans", font_path))
    pdfmetrics.registerFont(TTFont("PolopSansBold", bold_path))
    pdfmetrics.registerFontFamily("PolopSans", normal="PolopSans", bold="PolopSansBold")
    normal = ParagraphStyle("Body", fontName="PolopSans", fontSize=10.5, leading=15, spaceAfter=4)
    title = ParagraphStyle("Title", parent=normal, fontName="PolopSansBold",
                           fontSize=22, leading=28, spaceAfter=18, alignment=TA_CENTER)
    heading = ParagraphStyle("Heading", parent=normal, fontName="PolopSansBold",
                             fontSize=13, leading=18, spaceBefore=15, spaceAfter=8,
                             textColor=colors.black, keepWithNext=True)
    buffer = io.BytesIO()
    story = []
    for index, raw in enumerate(text.splitlines()):
        if not raw.strip():
            story.append(Spacer(1, 6))
            continue
        line = raw.strip()
        if line.startswith(("### ", "## ", "# ")):
            line = line.lstrip("#").strip()
            style = heading
        elif index == 0:
            style = title
        elif line.startswith(("A — ", "B — ", "A0 — ", "B0 — ")):
            style = heading
        else:
            style = normal
        # Escape source markup: Markdown is input text, not ReportLab XML.
        line = escape(line)
        if line.startswith("**") and line.endswith("**"):
            line = "<b>" + line[2:-2] + "</b>"
        story.append(Paragraph(line, style))
    SimpleDocTemplate(buffer, pagesize=A4, leftMargin=48, rightMargin=48,
                      topMargin=50, bottomMargin=50, title="Polop").build(story)
    pdf = buffer.getvalue()
    if not pdf.startswith(b"%PDF"):
        raise RuntimeError("Échec de génération du PDF depuis la source GitHub.")
    return pdf


def publish_pdf(text, drive):
    pdf = build_pdf(text)
    q = "name = '%s' and '%s' in parents and trashed = false" % (PDF_NAME, FOLDER_ID)
    matches = drive.files().list(
        q=q, fields="nextPageToken,files(id,name,mimeType)", pageSize=100
    ).execute().get("files", [])
    if len(matches) > 1 or (matches and matches[0]["mimeType"] != "application/pdf"):
        raise RuntimeError("Cible PDF ambiguë ou de mauvais format ; aucun écrasement.")
    upload = MediaIoBaseUpload(io.BytesIO(pdf), mimetype="application/pdf", resumable=False)
    if matches:
        result = drive.files().update(
            fileId=matches[0]["id"], media_body=upload,
            fields="id,name,webViewLink", supportsAllDrives=True
        ).execute()
    else:
        result = drive.files().create(
            body={"name": PDF_NAME, "parents": [FOLDER_ID], "mimeType": "application/pdf"},
            media_body=upload, fields="id,name,webViewLink", supportsAllDrives=True
        ).execute()
    print("PDF publié :", result.get("webViewLink", "Drive file ID " + result["id"]), flush=True)


def main():
    text = SOURCE.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError("Script source vide : publication refusée.")
    creds = credentials()
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)

    successes = 0
    try:
        docs = build("docs", "v1", credentials=creds, cache_discovery=False)
        publish_doc(text, drive, docs)
        successes += 1
    except Exception as exc:
        print("::error title=Échec Google Docs::" + str(exc).replace("\\n", " "), file=sys.stderr, flush=True)

    try:
        publish_pdf(text, drive)
        successes += 1
    except Exception as exc:
        print("::error title=Échec PDF::" + str(exc).replace("\\n", " "), file=sys.stderr, flush=True)

    print(f"Publication : {successes}/2 format(s) réussi(s).", flush=True)
    if not successes:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
