#!/usr/bin/env python3
"""Publish the canonical POLOP script to one Google Doc and one PDF in Drive.

GitHub is the source of truth. OAuth credentials belong only in GitHub Actions secrets.
"""
import io
import os
import re
import sys
import time
from pathlib import Path

import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

FOLDER_ID = "1A5LpnJh_c7cPe0xprY_r9jDFowu48tLc"
DOC_ID = "1-3JmmVB0da-eE-ewTSjAVzANDJA6udn_lmNIEe995z4"
PDF_NAME = "Script_POLOP.pdf"
SOURCE = Path("Script_POLOP.md")


def credentials():
    names = ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN")
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise RuntimeError("Missing GitHub Actions secrets: " + ", ".join(missing))
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    creds.refresh(google.auth.transport.requests.Request())
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

    pdf = drive.files().export(fileId=DOC_ID, mimeType="application/pdf").execute()
    if not pdf.startswith(b"%PDF"):
        raise RuntimeError("Google Docs did not return a PDF; refusing to upload.")
    q = "name = '%s' and '%s' in parents and trashed = false" % (PDF_NAME, FOLDER_ID)
    matches = drive.files().list(q=q, fields="nextPageToken,files(id,name,mimeType)",pageSize=100).execute().get("files", [])
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
    print("Updated PDF:", result.get("webViewLink", "Drive file ID " + result["id"]))


if __name__ == "__main__":
    main()
