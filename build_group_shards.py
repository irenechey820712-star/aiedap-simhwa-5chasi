#!/usr/bin/env python3
"""
Split data/imdb50k.csv into six balanced group shards.

Input:
  data/imdb50k.csv
Required columns:
  review,label
Optional:
  split

Output:
  data/imdb_group_A.csv ... data/imdb_group_F.csv

Each group:
  2,000 reviews = 1,000 positive + 1,000 negative
Sampling is reproducible.
"""

from pathlib import Path
import pandas as pd
import numpy as np

SRC = Path("data/imdb50k.csv")
OUTDIR = Path("data")
GROUPS = list("ABCDEF")
PER_CLASS = 1000
SEED = 20260906

if not SRC.exists():
    raise SystemExit("data/imdb50k.csv가 없습니다. 먼저 IMDb 50K CSV를 준비하세요.")

df = pd.read_csv(SRC)

review_col = next((c for c in ["review","text","document"] if c in df.columns), None)
label_col = next((c for c in ["label","sentiment"] if c in df.columns), None)

if review_col is None or label_col is None:
    raise SystemExit("review/text/document 열과 label/sentiment 열이 필요합니다.")

def norm_label(v):
    s = str(v).strip().lower()
    if s in {"1","pos","positive","true"}:
        return 1
    if s in {"0","neg","negative","false"}:
        return 0
    return np.nan

df = df.copy()
df["_label"] = df[label_col].map(norm_label)
df = df[df["_label"].isin([0,1])].dropna(subset=[review_col])

pos = df[df["_label"] == 1].sample(frac=1, random_state=SEED).reset_index(drop=True)
neg = df[df["_label"] == 0].sample(frac=1, random_state=SEED+1).reset_index(drop=True)

need = len(GROUPS) * PER_CLASS
if len(pos) < need or len(neg) < need:
    raise SystemExit(f"각 클래스에 최소 {need}개가 필요합니다. pos={len(pos)}, neg={len(neg)}")

OUTDIR.mkdir(exist_ok=True)

manifest = []
for i, g in enumerate(GROUPS):
    p = pos.iloc[i*PER_CLASS:(i+1)*PER_CLASS].copy()
    n = neg.iloc[i*PER_CLASS:(i+1)*PER_CLASS].copy()
    shard = pd.concat([p, n], ignore_index=True)
    shard = shard.sample(frac=1, random_state=SEED+i).reset_index(drop=True)

    out = pd.DataFrame({
        "review": shard[review_col].astype(str),
        "label": shard["_label"].astype(int),
        "group": g
    })
    path = OUTDIR / f"imdb_group_{g}.csv"
    out.to_csv(path, index=False, encoding="utf-8")
    manifest.append({"group":g,"rows":len(out),"positive":int((out.label==1).sum()),"negative":int((out.label==0).sum()),"file":str(path)})
    print(f"{g}조: {path} · {len(out):,} rows")

pd.DataFrame(manifest).to_csv(OUTDIR/"group_manifest.csv", index=False, encoding="utf-8")
print("완료: A~F 각 2,000개, Positive/Negative 1,000개씩.")
