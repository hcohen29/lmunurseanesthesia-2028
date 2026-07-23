#!/usr/bin/env python3

import os
import re
import sys
from datetime import datetime

MARKER = "    // <<DATES-END>> — DO NOT REMOVE: auto-update marker"
INDEX_PATH = "class-hub/index.html"

MONTH_NAMES = {
    "JAN": "January", "FEB": "February", "MAR": "March",    "APR": "April",
    "MAY": "May",     "JUN": "June",     "JUL": "July",     "AUG": "August",
    "SEP": "September","OCT": "October", "NOV": "November", "DEC": "December",
}


def parse_line(raw_line):
    line = raw_line.strip()
    if not line or line.startswith("#"):
        return None

    parts = [p.strip() for p in line.split("|")]
    if len(parts) < 5:
        return None

    iso_date    = parts[0]
    mo          = parts[1].upper()[:3]
    dy          = parts[2]
    title       = parts[3]
    entry_type  = parts[4].lower()
    details_raw = parts[5] if len(parts) > 5 else ""
    range_text  = parts[6].strip() if len(parts) > 6 else ""

    try:
        dt = datetime.strptime(iso_date, "%Y-%m-%d")
    except ValueError:
        return None

    details = []
    if details_raw.strip():
        details = [d.strip() for d in details_raw.split(";") if d.strip()]

    readable_date = "{} {}, {}".format(MONTH_NAMES.get(mo, mo), dy, dt.year)
    if details and not any(readable_date[:6] in d for d in details):
        details.insert(0, readable_date)
    elif not details:
        details = [readable_date]

    return {
        "iso": iso_date, "mo": mo, "dy": dy,
        "title": title, "type": entry_type,
        "details": details, "range": range_text,
    }


def js_string(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def render_entry(d):
    mo    = js_string(d["mo"])
    dy    = js_string(d["dy"])
    typ   = js_string(d["type"])
    title = js_string(d["title"])
    iso   = js_string(d["iso"])

  
        plan_flag = ""

    lines = ['    {{ mo:"{}", dy:"{}", type:"{}", title:"{}",'.format(mo, dy, typ, title)]

    if d["range"]:
        lines.append('      range:"{}",'.format(js_string(d["range"])))

    if d["details"]:
        detail_items = ", ".join('"{}"'.format(js_string(det)) for det in d["details"])
        lines.append("      details:[{}],".format(detail_items))

    lines.append('      iso:"{}"{} }},'.format(iso, plan_flag))
    return "\n".join(lines)


def main():
    dates_input    = os.environ.get("DATES_INPUT", "").strip()
    semester_label = os.environ.get("SEMESTER_LABEL", "").strip()

    if not dates_input:
        print("No DATES_INPUT provided.")
        sys.exit(0)

    entries = [parse_line(r) for r in dates_input.splitlines()]
    entries = [e for e in entries if e]

    if not entries:
        print("No valid date lines found.")
        sys.exit(1)

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if MARKER not in content:
        print("ERROR: Marker not found in index.html.")
        sys.exit(1)

    entries.sort(key=lambda d: d["iso"])
    existing_isos = set(re.findall(r'iso:"(\d{4}-\d{2}-\d{2})"', content))

    new_entries = [e for e in entries if e["iso"] not in existing_isos]

    if not new_entries:
        print("All dates already exist.")
        sys.exit(0)

    insert_lines = []
    if semester_label:
        insert_lines.append("\n    // -- {} --".format(semester_label))

    for entry in new_entries:
        insert_lines.append(render_entry(entry))

    insert_block = "\n".join(insert_lines) + "\n\n"
    updated = content.replace(MARKER, insert_block + MARKER)

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(updated)

    print("Done! {} date(s) added.".format(len(new_entries)))


if __name__ == "__main__":
    main()
