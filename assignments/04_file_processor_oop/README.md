# 04 – File Processor (OOP)

Goals
- Extract and display file metadata and the first 20 bytes of the header for files in a user-selected directory.

Approach
- Use a FileProcessor class to collect stats (size, times, mode, UID), read the header, and pretty-print.

Results
- For each accessible file, prints metadata and a hexlified header. Handles exceptions gracefully.

Run
```bash path=null start=null
python3 assignments/04_file_processor_oop/04_file_processor_oop.py
```
