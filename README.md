# 🐍 Violent Python: Script Portfolio

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](#)
[![Course](https://img.shields.io/badge/Course-CYBV%20473-%23CC0033)](#)
[![Status](https://img.shields.io/badge/Status-Active-green)](#)

> A curated collection of my scripting assignments, showcasing practical Python for offensive & defensive cybersecurity tasks which include networking, forensics, web scraping, packet analysis, steganography, API work, and more.

---

## 📂 Overview of Contents

> This portfolio maps to the course’s weekly focus areas:
>   - **Core Python & file I/O:** string searching, parsing firewall logs, hashing for forensics.
>   - **OOP & utilities:** building reusable file processing helpers.
>   - **Images & EXIF:** search photos, extract metadata & geolocation.
>   - **Binary & memory:** regex extractions, unique strings from dumps.
>   - **Web content:** crawling & BeautifulSoup-powered scraping.
>   - **Sockets & scanning:** TCP client/server, sniffer, passive mapping.
>   - **PCAP & Scapy:** asset extraction & analysis pipelines.
>   - **Steganography:** LSB techniques in true-color images.
>   - **Social data:** hashtag and timeline collection via API.
>   - **NLP:** text parsing and analysis with NLTK.
>   - **Media carving:** MP3 ID3 frame extraction.
>   - **Malware intel:** VirusTotal client for file checks.
>   - **Intro to ML:** pandas + scikit-learn for basic classifiers.
> 
> This repo focuses on the core scripting assignments and placeholders for the rest.

#### 🔗 Repo Structure

```
.
├─ main.py                      # clickable-logo overview GUI<br>
├─ requirements.txt             # (optional) shared libs
├─ assets/
│  └─ python-logo.png           # 512px transparent logo (add your own)
└─ assignments/
   ├─ 01_string_search/
   ├─ 02_firewall_parser/
   ├─ 03_hashing_forensics/
   ├─ 04_file_processor_oop/
   ├─ 05_pil_search_images/
   ├─ 06_exif_geotag_extractor/
   ├─ 07_memory_regex_extract/
   ├─ 08_memory_unique_strings/
   ├─ 09_web_crawler_scraper/
   ├─ 10_tcp_server/
   ├─ 11_tcp_client/
   ├─ 12_packet_sniffer/
   ├─ 13_pcap_asset_mapping/
   ├─ 14_lsb_steganography/
   ├─ 15_hashtag_collector/
   ├─ 16_social_graph_harvest/
   ├─ 17_nltk_transcript_analysis/
   ├─ 18_mp3_id3_carver/
   ├─ 19_virustotal_client/
   ├─ 20_tbd/
   ├─ 21_tbd/
   └─ 22_tbd/
```
> Each assignment folder includes:
> - README.md with goals, approach, and results
> - A *.py script (or small package) and sample data if allowed
---
## 👀 Quick Setup & demo
> Clone this repository
```
git clone https://github.com/ktalons/Violent-Python-Script-Portfolio.git
```
> *optional: virtualenv
```
python3 -m venv .venv && source .venv/bin/activate
```
> *optional: shared deps used across demos
```
pip install -r requirements.txt
```
> Run the interactive overview:  
```
python3 main.py
```
---
