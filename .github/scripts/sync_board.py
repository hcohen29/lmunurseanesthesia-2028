#!/usr/bin/env python3
"""
Notion -> board-data.json sync
================================
Queries the Class Feedback Log for items where "OK to Share on Hub" = Yes,
then writes class-hub/board-data.json so the site can render them dynamically.

Runs nightly via GitHub Actions (sync-board.yml).
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime

NOTION_TOKEN   = os.environ.get("NOTION_TOKEN", "")
DATABASE_ID    = "ae53a511f3dc496ab5bc23938d7d6494"
OUTPUT_PATH    = "class-hub/board-data.json"

STATUS_MAP = {
    "Not started": "Not Started",
    "In progress": "In Progress",
    "Done":        "Resolved",
}

MONTH_ABBR = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


def notion_request(path, payload):
    url  = f"https://api.notion.com/v1{path}"
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization",   f"Bearer {NOTION_TOKEN}")
    req.add_header("Notion-Version",  "2022-06-28")
    req.add_header("Content-Type",    "application/json")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def format_date(iso_str):
    """Convert '2026-07-01' -> 'Jul 2026'"""
    if not iso_str:
        return "—"
    try:
        dt = datetime.strptime(iso_str[:10], "%Y-%m-%d")
        return f"{MONTH_ABBR[dt.month - 1]} {dt.year}"
    except Exception:
        return iso_str[:7]


def get_prop(props, name, kind="select"):
    p = props.get(name)
    if not p:
        return ""
    if kind == "select":
        return (p.get("select") or {}).get("name", "")
    if kind == "status":
        return (p.get("status") or {}).get("name", "")
    if kind == "title":
        parts = p.get("title", [])
        return "".join(t.get("plain_text", "") for t in parts)
    if kind == "text":
        parts = p.get("rich_text", [])
        return "".join(t.get("plain_text", "") for t in parts)
    if kind == "date":
        d = p.get("date") or {}
        return d.get("start", "")
    return ""


def main():
    if not NOTION_TOKEN:
        print("ERROR: NOTION_TOKEN not set.", file=sys.stderr)
        sys.exit(1)

    payload = {
        "filter": {
            "property": "OK to Share on Hub",
            "select": {"equals": "Yes"}
        },
        "sorts": [{"property": "Date Received", "direction": "ascending"}]
    }

    try:
        result = notion_request(f"/databases/{DATABASE_ID}/query", payload)
    except urllib.error.HTTPError as e:
        print(f"Notion API error {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)

    items = []
    for page in result.get("results", []):
        props = page.get("properties", {})

        sub_type  = get_prop(props, "Submission Type", "select").lower()
        summary   = get_prop(props, "Issue",           "title")
        date_raw  = get_prop(props, "Date Received",   "date")
        status_raw= get_prop(props, "Status",          "status")
        update    = get_prop(props, "Action Taken",    "text")

        if not summary:
            continue

        items.append({
            "type":      sub_type or "idea",
            "summary":   summary,
            "submitted": format_date(date_raw),
            "status":    STATUS_MAP.get(status_raw, status_raw or "Not Started"),
            "update":    update or "—",
        })

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(items)} item(s) to {OUTPUT_PATH}.")


if __name__ == "__main__":
    main()
