#!/usr/bin/env python3
"""Publish the canonical POLOP script to one Google Doc and one PDF in Drive.

GitHub is the source of truth. The Google service account key belongs only
in GitHub Actions secrets (GDRIVE_SA_KEY).
"""
import io
import json
import os
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

FOLDER_ID = "1A5LpnJh_c7cPe0xprY_r9jDFowu48tLc"
DOC_ID = "1-3JmmVB0da-eE-ewTSjAVzANDJA6udn_lmNIEe995z4"
PDF_NAME = "Script_POLOP.pdf"
SCRIPT_NAME = "Script_POLOP.md"
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


def main():
    text = SOURCE.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError("Canonical script is empty; refusing to overwrite Drive.")
    creds = credentials()
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)
    docs = build("docs", "v1", credentials=creds, cache_discovery=False)

    metadata = drive.files().get(fileId=DOC_ID, fields="id,name,mimeType,parents", supportsAllDrives=True).execute()
    if metadata.get("mimeType") != "application/vnd.google-apps.document" or FOLDER_ID not in metadata.get("parents", []):
        raise RuntimeError("Target Google Doc is not in the intended Drive folder; refusing to write.")

    old = docs.documents().get(documentId=DOC_ID).execute()
    content = old.get("body", {}).get("content", [])
    end_index = content[-1]["endIndex"] if content else 2
    rendered, style_requests = render_markdown(text)
    # Deleting through endIndex-1 preserves the mandatory final newline in Google Docs.
    requests = []
    if end_index > 2:
        requests.append({"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end_index - 1}}})
    requests.append({"insertText": {"location": {"index": 1}, "text": rendered}})
    requests.extend(style_requests)
    # Single batch ensures styles are anchored to the new, never old, content.
    docs.documents().batchUpdate(documentId=DOC_ID, body={"requests": requests}).execute()

    # Publish the exact Markdown source as a separate, directly downloadable Drive file.
    source_query = "name = '%s' and '%s' in parents and trashed = false" % (SCRIPT_NAME, FOLDER_ID)
    source_matches = drive.files().list(
        q=source_query, fields="nextPageToken,files(id,name,mimeType)", pageSize=100
    ).execute().get("files", [])
    if len(source_matches) > 1:
        raise RuntimeError("Several source files have the expected name: refusing to choose one arbitrarily.")
    if source_matches and source_matches[0]["mimeType"] != "text/markdown":
        raise RuntimeError("Existing source file is not Markdown; refusing to overwrite.")
    source_upload = MediaIoBaseUpload(
        io.BytesIO(text.encode("utf-8")), mimetype="text/markdown", resumable=False
    )
    if source_matches:
        source_result = drive.files().update(
            fileId=source_matches[0]["id"], media_body=source_upload,
            fields="id,name,webViewLink", supportsAllDrives=True
        ).execute()
    else:
        source_result = drive.files().create(
            body={"name": SCRIPT_NAME, "parents": [FOLDER_ID], "mimeType": "text/markdown"},
            media_body=source_upload, fields="id,name,webViewLink", supportsAllDrives=True
        ).execute()

    pdf = drive.files().export(fileId=DOC_ID, mimeType="application/pdf").execute()
    if not pdf.startswith(b"%PDF"):
        raise RuntimeError("Google Docs did not return a PDF; refusing to upload.")
    q = "name = '%s' and '%s' in parents and trashed = false" % (PDF_NAME, FOLDER_ID)
    matches = drive.files().list(q=q, fields="nextPageToken,files(id,name,mimeType)", pageSize=100).execute().get("files", [])
    if len(matches) > 1:
        raise RuntimeError("Several PDFs have the expected name: refusing to choose one arbitrarily.")
    if matches and matches[0]["mimeType"] != "application/pdf":
        raise RuntimeError("Existing target name is not a PDF; refusing to overwrite.")
    upload = MediaIoBaseUpload(io.BytesIO(pdf), mimetype="application/pdf", resumable=False)
    if matches:
        result = drive.files().update(fileId=matches[0]["id"], media_body=upload, fields="id,name,webViewLink", supportsAllDrives=True).execute()
    else:
        result = drive.files().create(body={"name": PDF_NAME, "parents": [FOLDER_ID], "mimeType": "application/pdf"}, media_body=upload, fields="id,name,webViewLink", supportsAllDrives=True).execute()
    print("Updated Google Doc:", "https://docs.google.com/document/d/" + DOC_ID + "/edit")
    print("Updated Markdown source:", source_result.get("webViewLink", "Drive file ID " + source_result["id"]))
    print("Updated PDF:", result.get("webViewLink", "Drive file ID " + result["id"]))


if __name__ == "__main__":
    main()
