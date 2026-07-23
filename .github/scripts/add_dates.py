name: Add Calendar Dates

on:
  workflow_dispatch:
    inputs:
      dates:
        description: |
          Paste one date per line using this format:
          YYYY-MM-DD | MON | DD | Title | type | Detail 1; Detail 2 | Range text

          type options: academic, event, clinical, deadline
          Last two columns (details and range) are optional.

          Examples:
          2026-09-08 | SEP | 8 | First Day of Class | academic
          2026-11-09 | NOV | 9 | 753A Sim Intensive | academic | Nov 9-13 2026 on campus; Harrogate TN | Nov 9–13, 2026
        required: true
        type: string
      semester_label:
        description: 'Optional: semester section label (e.g. "Spring 2027"). Leave blank to auto-detect.'
        required: false
        type: string

permissions:
  contents: write

jobs:
  add-dates:
    runs-on: ubuntu-latest

    steps:
      - name: Check out repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Add dates to index.html
        env:
          DATES_INPUT: ${{ github.event.inputs.dates }}
          SEMESTER_LABEL: ${{ github.event.inputs.semester_label }}
        run: |
          python .github/scripts/add_dates.py

      - name: Commit and push changes
        run: |
          git config user.name  "Class Hub Bot"
          git config user.email "lmunurseanesthesia2028@gmail.com"
          git add class-hub/index.html
          if git diff --staged --quiet; then
            echo "No changes to commit — dates may already exist."
          else
            git commit -m "📅 Add calendar dates via GitHub Actions"
            git push
          fi
