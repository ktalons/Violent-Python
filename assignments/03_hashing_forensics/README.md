# 03 – Hashing Forensics

Goals
- Compute MD5 hashes for files under a target directory and report hash→path pairs.

Approach
- Walk the directory tree, read each file’s bytes, compute md5, and store hash→path in a dictionary.

Results
- Prints each MD5 hash with its corresponding file path.

Defaults and options
- By default, the script scans the `testImages/` folder next to the script.
- To scan another directory, pass `-d /path/to/dir`.

Run
```bash
# Default (scans the testImages folder next to this script)
python3 assignments/03_hashing_forensics/03_hashing_forensics.py

# Specify a target directory explicitly
python3 assignments/03_hashing_forensics/03_hashing_forensics.py -d /path/to/dir
```
