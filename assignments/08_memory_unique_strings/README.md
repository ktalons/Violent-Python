# 08 – Memory Unique Strings

Goals
- Identify unique alphabetical strings (5–15 letters) in a binary memory dump and count their occurrences.

Approach
- Stream the file in chunks with a 14-byte overlap to capture boundary-spanning matches.
- Use a regex pattern `[A-Za-z]{5,15}` and aggregate counts, then present results in a PrettyTable.

Results
- Prints a table with columns: String, Occurrences, sorted by highest count then alphabetically.

Dependencies
```bash
python3 -m pip install prettytable
```

Run
```bash
python3 assignments/08_memory_unique_strings/08_memory_unique_strings.py assets/test.bin
```
