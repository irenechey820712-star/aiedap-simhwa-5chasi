#!/usr/bin/env python3
"""
Build data/imdb50k.csv for Movie Review Corpus Lab.

Usage:
  python build_imdb50k.py

It downloads Stanford Large Movie Review Dataset v1.0,
extracts only train/test pos/neg reviews, and writes:
  data/imdb50k.csv
"""
from pathlib import Path
import csv, io, tarfile, urllib.request

URL = "https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz"
OUT = Path("data/imdb50k.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

print("Downloading Stanford IMDb dataset...")
with urllib.request.urlopen(URL) as r:
    raw = r.read()

print("Extracting labeled train/test reviews...")
records = []
with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tf:
    for split in ("train", "test"):
        for folder, label in (("neg", 0), ("pos", 1)):
            prefix = f"aclImdb/{split}/{folder}/"
            members = [
                m for m in tf.getmembers()
                if m.isfile() and m.name.startswith(prefix) and m.name.endswith(".txt")
            ]
            members.sort(key=lambda m: m.name)
            for m in members:
                f = tf.extractfile(m)
                text = f.read().decode("utf-8", errors="replace") if f else ""
                records.append((text, label, split))

print(f"Writing {len(records):,} reviews to {OUT} ...")
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["review", "label", "split"])
    w.writerows(records)

print("Done.")
print("Expected rows: 50,000 labeled reviews.")
print("Upload the 'data' folder together with your HTML to GitHub.")
