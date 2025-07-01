#!/usr/bin/env python3

import json
import pandas as pd
import unicodedata

# === Config ===
JSON_PATH = "./acronym_transforms.json"   # your uploaded JSON
PARQUET_PATH = "./acronym_transforms.parquet"  # output Parquet

def normalize_ascii(text):
    if text is None:
        return None
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()

def json_to_parquet(json_file, parquet_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rows = []
    for entry in data:
        row = {
            "source": normalize_ascii(entry.get("source")),
            "target": normalize_ascii(entry.get("target")),
            "context": normalize_ascii(entry.get("context")),
            "method": normalize_ascii(entry.get("method")),
            "weight": entry.get("weight"),
            "logographic_ref": normalize_ascii(entry.get("logographic_ref"))
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_parquet(parquet_file, index=False)
    print(f"✅ Parquet saved: {parquet_file}")

if __name__ == "__main__":
    json_to_parquet(JSON_PATH, PARQUET_PATH)
