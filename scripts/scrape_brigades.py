#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to scrape brigade PDFs from znaci.org and organize them systematically.
"""

import os
import sys
import re
import time
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Base configuration
BASE_URL = "https://znaci.org"
BRIGADES_DIR = Path(r"E:\Projects\113-nasi-heroji\01-data\brigades")
DELAY_BETWEEN_REQUESTS = 1  # Be polite to the server

# Brigade entries from znaci.org
BRIGADE_ENTRIES = [
    {"title": "PRVA PROLETERSKA BRIGADA - ZBORNIK SEĆANJA (knjiga 1)", "url": "/00001/99.htm"},
    {"title": "PRVA PROLETERSKA BRIGADA - ZBORNIK SEĆANJA (knjiga 2)", "url": "/00001/27.htm"},
    {"title": "PRVA PROLETERSKA BRIGADA - ZBORNIK SEĆANJA (knjiga 3)", "url": "/00001/98.htm"},
    {"title": "PRVA PROLETERSKA BRIGADA - ZBORNIK SEĆANJA (knjiga 4)", "url": "/00001/97.htm"},
    {"title": "PRVA PROLETERSKA BRIGADA - ILUSTROVANA MONOGRAFIJA", "url": "/00001/54.htm"},
    {"title": "Miloš Vuksanović: PRVA PROLETERSKA BRIGADA", "url": "/00003/382.htm"},
    {"title": "DALMATINCI U PRVOJ PROLETERSKOJ", "url": "/00001/207.htm"},
    {"title": "PRVI CRNOGORSKI BATALJON PRVE PROLETERSKE", "url": "/00003/493.htm"},
    {"title": "Mitar Mitrović: RATNIM STAZAMA PROLETERA", "url": "/00003/509.htm"},
    {"title": "Branislav Božović: RUDARSKA ČETA", "url": "/00003/748.php"},
    {"title": "BEOGRADSKI BATALJON PRVE PROLETERSKE", "url": "/00003/499.htm"},
    {"title": "50 GODINA DRUGE PROLETERSKE BRIGADE", "url": "/00001/55.htm"},
    {"title": "Sredoje Urošević: DRUGA PROLETERSKA BRIGADA", "url": "/00003/387.htm"},
    {"title": "DRUGA PROLETERSKA BRIGADA - SEĆANJA (KNJIGA 2)", "url": "/00001/202.htm"},
    {"title": "DRUGA PROLETERSKA BRIGADA - SEĆANJA (KNJIGA 4)", "url": "/00001/203.htm"},
    {"title": "Slobodan Špegar Špego: PRVA KRAJIŠKA BRIGADA", "url": "/00001/56.htm"},
    {"title": "Milorad Gončin, Stevo Rauš: PRVA KRAJIŠKA BRIGADA", "url": "/00001/226.htm"},
    {"title": "PRVA KRAJIŠKA BRIGADA - ZBORNIK SJEĆANJA", "url": "/00001/2.htm"},
    {"title": "Žarko Vidović: TREĆA PROLETERSKA BRIGADA", "url": "/00001/164.htm"},
    {"title": "TREĆA PROLETERSKA BRIGADA - SEĆANJA (KNJIGA 2)", "url": "/00001/205.htm"},
    {"title": "TREĆA PROLETERSKA BRIGADA - SEĆANJA (KNJIGA 3)", "url": "/00001/206.htm"},
    {"title": "Blažo Janković: ČETVRTA PROLETERSKA", "url": "/00001/148.htm"},
    {"title": "ČETVRTA PROLETERSKA - SJEĆANJA (KNJIGA 1)", "url": "/00001/282.htm"},
    {"title": "ČETVRTA PROLETERSKA - SJEĆANJA (KNJIGA 2)", "url": "/00001/287.htm"},
    {"title": "PETA PROLETERSKA SJEĆANJA (KNJIGA 2)", "url": "/00003/707.htm"},
    {"title": "PETA PROLETERSKA CRNOGORSKA BRIGADA", "url": "/00001/204.htm"},
    {"title": "Jovo Popović: PRVA LIČKA PROLETERSKA BRIGADA", "url": "/00001/137.htm"},
    {"title": "Rudi Petovar - Savo Trikić: ŠESTA PROLETERSKA", "url": "/00001/140.htm"},
    {"title": "Ahmed Đonlagić: PROLETERI ISTOČNE BOSNE", "url": "/00003/710.htm"},
    {"title": "Milorad Gončin: DRUGA KRAJIŠKA BRIGADA", "url": "/00001/133.htm"},
    {"title": "DRUGA KRAJIŠKA BRIGADA - RATNA SJEĆANJA", "url": "/00001/288.htm"},
    {"title": "Dušan Uzelac: GRMEČKE BIJELE NOĆI", "url": "/00003/520.htm"},
    {"title": "Mensur Seferović: ISTOČNO I ZAPADNO OD NERETVE", "url": "/00003/533.htm"},
    {"title": "Đorđe Orlović: DRUGA LIČKA PROLETERSKA BRIGADA", "url": "/00001/160.htm"},
    {"title": "DRUGA LIČKA PROLETERSKA BRIGADA - SJEĆANJA", "url": "/00001/110.htm"},
    {"title": "Savo Trikić: TREĆA KRAJIŠKA PROLETERSKA BRIGADA", "url": "/00001/224.htm"},
    {"title": "TREĆA KRAJIŠKA BRIGADA - SJEĆANJA (KNJIGE 1-2)", "url": "/00001/31.htm"},
    {"title": "TREĆA KRAJIŠKA BRIGADA - SJEĆANJA (KNJIGA 3)", "url": "/00003/394.htm"},
    {"title": "Mirko Novović, Stevan Petković: PRVA DALMATINSKA", "url": "/00001/108.htm"},
    {"title": "NAŠA PRVA DALMATINSKA - SJEĆANJA", "url": "/00001/125.htm"},
    {"title": "TREĆA LIČKA BRIGADA - SJEĆANJA", "url": "/00001/227.htm"},
    {"title": "Ignjatije Perić: PETA KORDUNAŠKA BRIGADA", "url": "/00003/539.htm"},
    {"title": "Lado Ambrožič-Novljan: CANKARJEVA BRIGADA", "url": "/00003/767.php"},
    {"title": "Branko B. Obradović: DRUGA DALMATINSKA", "url": "/00001/33.htm"},
    {"title": "DRUGA DALMATINSKA - SJEĆANJA BORACA", "url": "/00003/577.htm"},
    {"title": "Ljubo Vučković: DALMATINSKI PROLETERI", "url": "/00001/161.htm"},
    {"title": "Rade Zorić: ČETVRTA KRAJIŠKA NOU BRIGADA", "url": "/00001/94.htm"},
    {"title": "Advan Hozić: KORACI I RIJEKE", "url": "/00003/586.htm"},
    {"title": "ČETVRTA KRAJIŠKA BRIGADA - SEĆANJA (KNJIGA 1)", "url": "/00003/597.htm"},
    {"title": "ČETVRTA KRAJIŠKA BRIGADA - SEĆANJA (KNJIGA 2)", "url": "/00003/598.htm"},
    {"title": "Lj. Borojević, D Samardžija, R. Bašić: PETA KOZARAČKA", "url": "/00001/163.htm"},
    {"title": "KOZARA - ZBORNIK SJEĆANJA", "url": "/00001/241.htm"},
    {"title": "Ljuban Đurić: SEDMA BANIJSKA BRIGADA", "url": "/00001/63.htm"},
    {"title": "Ljuban Đurić: OSMA BANIJSKA NOU BRIGADA", "url": "/00003/383.htm"},
    {"title": "Jovan Kokot: DVANAESTA PROLETERSKA SLAVONSKA", "url": "/00001/46.htm"},
    {"title": "Milan Kavgić: VERNA BRDA", "url": "/00001/166.htm"},
    {"title": "Todor Radošević: TRINAESTA PROLETERSKA BRIGADA", "url": "/00001/69.htm"},
    {"title": "Mato Horvatić: PO DRUGI PUT ROĐENI", "url": "/00003/656.htm"},
    {"title": "Mamula, Bašić, Vurdelja, Pekić: PRVI PROLETERSKI BATALJON", "url": "/00003/590.htm"},
    {"title": "Vladimir-Dušan Matetić: 14. PRIMORSKO GORANSKA", "url": "/00003/544.htm"},
    {"title": "Branko Damjanović, Savo Popović: ŠESTA KRAJIŠKA", "url": "/00003/711.htm"},
    {"title": "ŠESTA KRAJIŠKA NOU BRIGADA - RATNA SJEĆANJA", "url": "/00001/147.htm"},
    {"title": "Jovan Kljajić: SEDMA KRAJIŠKA BRIGADA", "url": "/00003/396.htm"},
    {"title": "SEDMA KRAJIŠKA BRIGADA - SJEĆANJA (KNJIGA 2)", "url": "/00001/186.htm"},
    {"title": "Ignjatije Perić: PETNAESTA KORDUNAŠKA BRIGADA", "url": "/00001/159.htm"},
    {"title": "Dragutin Grgurević: U ZLOPOLJU", "url": "/00003/588.htm"},
    {"title": "Stevo Pravdić i Nail Redžić: 16. SLAVONSKA OMLADINSKA", "url": "/00002/407.htm"},
    {"title": "Izudin Čaušević: OSMA KRAJIŠKA NOU BRIGADA", "url": "/00001/146.htm"},
    {"title": "OSMA KRAJIŠKA BRIGADA - SJEĆANJA", "url": "/00001/68.htm"},
    {"title": "Zdravko B. Cvetković: SEDAMNAESTA SLAVONSKA BRIGADA", "url": "/00001/131.htm"},
    {"title": "Rade Roksandić, Zdravko B. Cvetković: 18. SLAVONSKA", "url": "/00001/101.htm"},
    {"title": "Milan Kavgić: PAPUK PLANINOM", "url": "/00003/605.htm"},
    {"title": "Milorad Gončin: DESETA KRAJIŠKA NOU BRIGADA", "url": "/00001/264.htm"},
    {"title": "Đuro Milinović, Drago Karasijević: JEDANAESTA KRAJIŠKA", "url": "/00001/167.htm"},
    {"title": "Milutin Vujović: MEĆAVINA BRIGADA", "url": "/00003/690.htm"},
]


def standardize_brigade_name(title):
    """
    Extract and standardize the brigade name from the title.
    Returns a clean folder name.
    """
    # Extract brigade number/name patterns
    patterns = [
        r'PRVA PROLETERSKA',
        r'DRUGA PROLETERSKA',
        r'TREĆA PROLETERSKA',
        r'ČETVRTA PROLETERSKA',
        r'PETA PROLETERSKA',
        r'ŠESTA PROLETERSKA',
        r'PRVA KRAJIŠKA',
        r'DRUGA KRAJIŠKA',
        r'TREĆA KRAJIŠKA',
        r'ČETVRTA KRAJIŠKA',
        r'PETA KOZARAČKA',
        r'ŠESTA KRAJIŠKA',
        r'SEDMA KRAJIŠKA',
        r'OSMA KRAJIŠKA',
        r'DESETA KRAJIŠKA',
        r'JEDANAESTA KRAJIŠKA',
        r'PRVA LIČKA',
        r'DRUGA LIČKA',
        r'TREĆA LIČKA',
        r'PRVA DALMATINSKA',
        r'DRUGA DALMATINSKA',
        r'SEDMA BANIJSKA',
        r'OSMA BANIJSKA',
        r'DVANAESTA PROLETERSKA SLAVONSKA',
        r'TRINAESTA PROLETERSKA',
        r'14\. PRIMORSKO GORANSKA',
        r'PETA KORDUNAŠKA',
        r'PETNAESTA KORDUNAŠKA',
        r'16\. SLAVONSKA OMLADINSKA',
        r'SEDAMNAESTA SLAVONSKA',
        r'18\. SLAVONSKA',
        r'CANKARJEVA BRIGADA',
    ]

    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            brigade_name = match.group(0)
            # Standardize capitalization
            brigade_name = brigade_name.title()
            # Clean up for folder name
            brigade_name = re.sub(r'[<>:"/\\|?*]', '', brigade_name)
            return brigade_name

    # If no pattern matches, use a cleaned version of the title
    clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
    clean_title = re.sub(r'\s+', ' ', clean_title).strip()
    return clean_title[:50]  # Limit length


def get_descriptive_filename(title, page_content, index=1):
    """
    Generate a descriptive filename based on title and content.
    """
    # Extract author if present
    author_match = re.search(r'^([A-ZŠĐČĆŽ][a-zšđčćž]+(?:\s+[A-ZŠĐČĆŽ][a-zšđčćž]+)*?):', title)
    author = author_match.group(1).replace(' ', '_') if author_match else None

    # Extract book title or description
    book_title = title.split(':', 1)[-1].strip()
    book_title = re.sub(r'\s*\(knjiga\s+\d+\)', '', book_title, flags=re.IGNORECASE)
    book_title = re.sub(r'\s*\(KNJIGA\s+\d+\)', '', book_title, flags=re.IGNORECASE)
    book_title = re.sub(r'[<>:"/\\|?*]', '', book_title)
    book_title = re.sub(r'\s+', '_', book_title).strip('_')

    # Extract book number if present
    book_num_match = re.search(r'knjiga\s+(\d+)', title, re.IGNORECASE)
    book_num = f"_knjiga{book_num_match.group(1)}" if book_num_match else ""

    # Construct filename
    parts = []
    if author:
        parts.append(author)
    if book_title:
        parts.append(book_title)
    if book_num:
        parts.append(book_num)

    if not parts:
        parts.append(f"document_{index}")

    filename = '_'.join(parts)
    filename = filename[:100]  # Limit length

    return f"{filename}.pdf"


def find_pdf_links(url):
    """
    Find all PDF links on a given page.
    Returns list of (pdf_url, context) tuples.
    """
    try:
        time.sleep(DELAY_BETWEEN_REQUESTS)
        page_url = urljoin(BASE_URL, url)
        response = requests.get(page_url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        pdf_links = []

        # Find all links to PDFs
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.lower().endswith('.pdf') or '/pdf/' in href.lower():
                # Resolve relative URLs based on the current page URL
                full_url = urljoin(page_url, href)
                context = link.get_text(strip=True) or link.get('title', '')
                pdf_links.append((full_url, context))

        return pdf_links
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []


def download_pdf(pdf_url, save_path):
    """
    Download a PDF file to the specified path.
    """
    try:
        time.sleep(DELAY_BETWEEN_REQUESTS)
        response = requests.get(pdf_url, timeout=60, stream=True)
        response.raise_for_status()

        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return True
    except Exception as e:
        print(f"Error downloading {pdf_url}: {e}")
        return False


def process_brigades():
    """
    Main function to process all brigades.
    """
    BRIGADES_DIR.mkdir(parents=True, exist_ok=True)

    results = {
        "processed": [],
        "errors": [],
        "summary": {}
    }

    # Group entries by brigade
    brigade_groups = {}
    for entry in BRIGADE_ENTRIES:
        brigade_name = standardize_brigade_name(entry['title'])
        if brigade_name not in brigade_groups:
            brigade_groups[brigade_name] = []
        brigade_groups[brigade_name].append(entry)

    print(f"Found {len(brigade_groups)} unique brigades to process")
    print("=" * 80)

    for brigade_name, entries in sorted(brigade_groups.items()):
        print(f"\nProcessing: {brigade_name}")
        print(f"  Found {len(entries)} entries")

        brigade_dir = BRIGADES_DIR / brigade_name
        brigade_dir.mkdir(parents=True, exist_ok=True)

        pdf_count = 0

        for entry in entries:
            title = entry['title']
            url = entry['url']

            print(f"    Checking: {title}")

            # Find PDFs on this page
            pdf_links = find_pdf_links(url)

            if not pdf_links:
                print(f"      No PDFs found")
                results["errors"].append({
                    "brigade": brigade_name,
                    "title": title,
                    "url": url,
                    "error": "No PDFs found"
                })
                continue

            print(f"      Found {len(pdf_links)} PDF(s)")

            for idx, (pdf_url, context) in enumerate(pdf_links, 1):
                filename = get_descriptive_filename(title, context, idx)
                save_path = brigade_dir / filename

                # Skip if already downloaded
                if save_path.exists():
                    print(f"        Already exists: {filename}")
                    pdf_count += 1
                    continue

                print(f"        Downloading: {filename}")
                success = download_pdf(pdf_url, save_path)

                if success:
                    pdf_count += 1
                    results["processed"].append({
                        "brigade": brigade_name,
                        "title": title,
                        "filename": filename,
                        "pdf_url": pdf_url
                    })
                    print(f"        ✓ Success")
                else:
                    results["errors"].append({
                        "brigade": brigade_name,
                        "title": title,
                        "pdf_url": pdf_url,
                        "error": "Download failed"
                    })
                    print(f"        ✗ Failed")

        results["summary"][brigade_name] = pdf_count
        print(f"  Total PDFs for {brigade_name}: {pdf_count}")

    return results


def generate_report(results):
    """
    Generate a summary report.
    """
    print("\n" + "=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)

    total_pdfs = sum(results["summary"].values())
    total_brigades = len(results["summary"])

    print(f"\nTotal Brigades: {total_brigades}")
    print(f"Total PDFs Downloaded: {total_pdfs}")

    print("\nPDFs per Brigade:")
    for brigade, count in sorted(results["summary"].items()):
        print(f"  {brigade}: {count} PDF(s)")

    if results["errors"]:
        print(f"\nErrors Encountered: {len(results['errors'])}")
        for error in results["errors"]:
            print(f"  - {error['brigade']}: {error.get('error', 'Unknown error')}")

    # Save detailed results to JSON
    report_path = BRIGADES_DIR / "download_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nDetailed report saved to: {report_path}")


if __name__ == "__main__":
    print("Starting brigade PDF download...")
    print(f"Target directory: {BRIGADES_DIR}")

    results = process_brigades()
    generate_report(results)

    print("\nDownload complete!")
