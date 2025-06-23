# server.py
from __future__ import annotations

import base64
from pathlib import Path
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from mcp.server.fastmcp import FastMCP

# ──────────────────────────────────────────────────────────────────────────────
# MCP server
# ──────────────────────────────────────────────────────────────────────────────
mcp = FastMCP("gmail-mcp")

# Gmail OAuth / API helpers
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

BASE_DIR = Path(__file__).resolve().parent        # folder that contains server.py
CREDS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

_service = None  # module‑level cache


def get_service():
    """Return an authenticated gmail v1 service, refreshing / re‑authing if needed."""
    global _service
    if _service:
        return _service

    creds: Credentials | None = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            # Use run_console() if you're on a headless box
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())

    _service = build("gmail", "v1", credentials=creds)
    return _service


def list_message_ids(service, *, max_results: int = 10, query: str | None = None):
    resp = (
        service.users()
        .messages()
        .list(userId="me", maxResults=max_results, q=query)
        .execute()
    )
    return [m["id"] for m in resp.get("messages", [])]


def fetch_message(service, msg_id: str) -> str:
    msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    payload = msg["payload"]
    parts = payload.get("parts", [payload])  # handle both simple & multipart
    for part in parts:
        if part["mimeType"] == "text/plain":
            data = part["body"]["data"]
            return base64.urlsafe_b64decode(data).decode("utf-8")
    return "(no plain‑text body found)"


# ──────────────────────────────────────────────────────────────────────────────
# MCP tools & resources
# ──────────────────────────────────────────────────────────────────────────────
@mcp.tool(
    name="get_gmail_messages",
    description="Return the plain‑text bodies of unread Gmail messages.",
)
def get_gmail_messages(max_results: int = 5, query: str = "is:unread") -> List[str]:
    """Fetch unread Gmail messages that match *query*."""
    service = get_service()
    ids = list_message_ids(service, max_results=max_results, query=query)

    bodies: List[str] = []
    for i, mid in enumerate(ids, 1):
        body = fetch_message(service, mid)
        # Comment this out if you don't want log spam
        print(f"\n--- Message {i} ---\n{body}")
        bodies.append(body)

    return bodies


@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Return a personalised greeting."""
    return f"Hello, {name}!"


# ──────────────────────────────────────────────────────────────────────────────
# Entry point (only needed if you *directly* run python server.py)
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(mcp.app, host="0.0.0.0", port=8000)
  

    # return bodies
