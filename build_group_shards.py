#!/usr/bin/env python3
"""
Movie Review Corpus Lab - 조별 분산 데이터 빌더 (표준 라이브러리만 사용, pandas 불필요)

하는 일
  1) Stanford Large Movie Review Dataset v1 다운로드 (~84 MB)
  2) 각 리뷰의 IMDb 영화 ID(tconst)를 urls_*.txt 에서 추출
  3) IMDb 공식 데이터셋(title.basics.tsv.gz, ~226 MB)으로 tconst -> "제목 (연도)" 매핑
  4) data/imdb_group_A.csv ~ imdb_group_F.csv 생성
       열: review,label,movie,group
       조당 2,000개 = 긍정 1,000 + 부정 1,000, A~F 서로 겹치지 않음, 시드 고정
     + data/group_manifest.csv

사용
  python build_group_shards.py            # data/ 아래에 생성
  python build_group_shards.py <레포경로>  # <레포경로>/data/ 아래에 생성

다운로드 파일(aclImdb_v1.tar.gz, title.basics.tsv.gz)은 스크립트 폴더에 캐시되어
재실행 시 다시 받지 않습니다.
"""
import csv, gzip, io, re, random, sys, tarfile, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
IMDB_URL = "https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz"
BASICS_URL = "https://datasets.imdbws.com/title.basics.tsv.gz"
TARP = HERE / "aclImdb_v1.tar.gz"
BASICS = HERE / "title.basics.tsv.gz"
OUTDIR = (Path(sys.argv[1]) / "data") if len(sys.argv) > 1 else Path("data")
GROUPS = list("ABCDEF")
PER_CLASS = 1000
SEED = 20260906
TT = re.compile(r"(tt\d+)")

OUTDIR.mkdir(parents=True, exist_ok=True)


def fetch(url, dest, min_size):
    if dest.exists() and dest.stat().st_size >= min_size:
        return
    print(f"다운로드: {url}", flush=True)
    urllib.request.urlretrieve(url, dest)
    print(f"  저장 {dest.stat().st_size:,} bytes", flush=True)


# 1) Stanford IMDb
fetch(IMDB_URL, TARP, 80_000_000)

# 2) 리뷰 + tconst 추출 (tar 1회 스트리밍)
urls, texts = {}, {}
with tarfile.open(TARP, "r:gz") as tf:
    for m in tf:
        if not m.isfile():
            continue
        parts = m.name.split("/")
        if len(parts) == 3 and parts[2] in ("urls_pos.txt", "urls_neg.txt"):
            folder = "pos" if parts[2].endswith("pos.txt") else "neg"
            urls[(parts[1], folder)] = tf.extractfile(m).read().decode("utf-8", "replace").splitlines()
        elif len(parts) == 4 and parts[1] in ("train", "test") and parts[2] in ("pos", "neg") and parts[3].endswith(".txt"):
            rid = int(parts[3].split("_")[0])
            t = tf.extractfile(m).read().decode("utf-8", "replace").strip()
            t = t.replace("<br />", " ").replace("<br/>", " ").replace("<br>", " ")
            t = re.sub(r"\s+", " ", t).strip()
            texts[(parts[1], parts[2], rid)] = t

reviews, needed = [], set()
for (split, folder, rid), t in texts.items():
    ul = urls.get((split, folder), [])
    tc = ""
    if rid < len(ul):
        mm = TT.search(ul[rid])
        if mm:
            tc = mm.group(1)
    reviews.append((folder, tc, t))
    if tc:
        needed.add(tc)
print(f"리뷰 {len(reviews):,}개, 영화 {len(needed):,}편", flush=True)

# 3) IMDb 제목 매핑
fetch(BASICS_URL, BASICS, 50_000_000)
title = {}
with gzip.open(BASICS, "rt", encoding="utf-8", newline="") as fh:
    fh.readline()
    for line in fh:
        c = line.rstrip("\n").split("\t")
        if len(c) < 6 or c[0] not in needed:
            continue
        year = c[5].strip()
        title[c[0]] = f"{c[2].strip()} ({year})" if year and year != r"\N" else c[2].strip()
        if len(title) == len(needed):
            break
print(f"제목 매핑 {len(title):,}/{len(needed):,} (나머지는 'IMDb <id>'로 표기)", flush=True)


def movie_of(tc):
    return title.get(tc) or (f"IMDb {tc}" if tc else "IMDb")


# 4) 균형·비중복 분할
pos = [(tc, t) for f, tc, t in reviews if f == "pos"]
neg = [(tc, t) for f, tc, t in reviews if f == "neg"]
random.Random(SEED).shuffle(pos)
random.Random(SEED + 1).shuffle(neg)
need = len(GROUPS) * PER_CLASS
assert len(pos) >= need and len(neg) >= need, (len(pos), len(neg))

manifest = []
for i, g in enumerate(GROUPS):
    p = pos[i * PER_CLASS:(i + 1) * PER_CLASS]
    n = neg[i * PER_CLASS:(i + 1) * PER_CLASS]
    rows = [(t, 1, movie_of(tc), g) for tc, t in p] + [(t, 0, movie_of(tc), g) for tc, t in n]
    random.Random(SEED + 10 + i).shuffle(rows)
    path = OUTDIR / f"imdb_group_{g}.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["review", "label", "movie", "group"])
        w.writerows(rows)
    manifest.append({"group": g, "rows": len(rows), "positive": len(p), "negative": len(n),
                     "distinct_movies": len({r[2] for r in rows}), "file": path.name})
    print(f"  {g}조 -> {path}  ({len(rows):,} rows, 영화 {manifest[-1]['distinct_movies']}편)", flush=True)

with (OUTDIR / "group_manifest.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["group", "rows", "positive", "negative", "distinct_movies", "file"])
    w.writeheader()
    w.writerows(manifest)
print("완료: A~F 각 2,000개 (긍정 1,000 + 부정 1,000), 영화 제목 포함.", flush=True)
