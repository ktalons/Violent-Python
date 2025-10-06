# 07 – Memory Regex Extract

Goals
- Find unique e-mail addresses and URLs in a binary memory dump.
- Optionally show occurrence counts and write results to JSON.

Approach
- Read the file in chunks with an overlap window to catch matches that span chunk boundaries.
- Use compiled regular expressions for e-mails and URLs; maintain sets for uniqueness and dicts for counts.

Results
- Prints totals and lists of unique e-mails and URLs.
- With `--show-counts`, prints top occurrences by frequency.
- With `--json-out`, writes a JSON file containing both lists.

Dependencies
- None

Run
```bash
python3 assignments/07_memory_regex_extract/07_memory_regex_extract.py assets/test.bin --show-counts --json-out output/indicators.json
```
