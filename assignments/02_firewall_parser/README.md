# 02 – Firewall Parser

Goals
- Parse a log file and extract a sorted list of unique tokens containing the substring "worm" (case-insensitive).

Approach
- Read a text log line by line, split into columns, search each token for the substring.
- Store unique matches in a set, then output the sorted results.

Results
- Prints a sorted list of unique tokens that contain "worm".

Data
- Expects a file named `redhat.txt` in the current working directory.
- Sample files are included at `assets/week1/redhat.txt` and at the repository root (`./redhat.txt`).

Run
Option A (copy sample to the working directory):
```bash
cp assets/week1/redhat.txt .
python3 assignments/02_firewall_parser/02_firewall_parser.py
```
Option B (run from the sample directory):
```bash
(cd assets/week1 && python3 ../../assignments/02_firewall_parser/02_firewall_parser.py)
```
