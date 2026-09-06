#!/usr/bin/env python3
"""
Movie Review Corpus Lab - 조별 분산 데이터 빌더 (표준 라이브러리만, pandas 불필요)

  1) Stanford Large Movie Review Dataset v1 다운로드 (~84 MB)
  2) 각 리뷰의 IMDb 영화 ID(tconst)를 urls_*.txt 에서 추출
  3) IMDb 공식 title.basics.tsv.gz (~226 MB)로 tconst -> (제목, 연도, 유형) 매핑
  4) data/imdb_group_A.csv ~ imdb_group_F.csv 생성
       열: review,label,movie,group,famous
       조당 2,000개 = 긍정 1,000 + 부정 1,000, A~F 비중복, 시드 고정
       각 조에 대중적으로 유명한 영화(연도 대조로 동명이작 배제) 쿼터 보장
     + data/group_manifest.csv
사용
  python build_group_shards.py <레포경로>
"""
import csv, gzip, re, random, sys, tarfile, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
IMDB_URL = "https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz"
BASICS_URL = "https://datasets.imdbws.com/title.basics.tsv.gz"
TARP = HERE / "aclImdb_v1.tar.gz"
BASICS = HERE / "title.basics.tsv.gz"
OUTDIR = (Path(sys.argv[1]) / "data") if len(sys.argv) > 1 else Path("data")
GROUPS = list("ABCDEF")
PER_CLASS = 1000
FAMOUS_QUOTA_PER_CLASS = 90
SEED = 20260906
TT = re.compile(r"(tt\d+)")

# 학생들이 알 만한 대중적 영화 "제목|개봉연도" (Stanford 데이터는 ~2011년까지)
FAMOUS = """
The Shawshank Redemption|1994
The Godfather|1972
Pulp Fiction|1994
Forrest Gump|1994
Fight Club|1999
The Dark Knight|2008
Batman Begins|2005
Inception|2010
The Matrix|1999
The Matrix Reloaded|2003
Titanic|1997
Avatar|2009
Gladiator|2000
Braveheart|1995
The Lord of the Rings: The Fellowship of the Ring|2001
The Lord of the Rings: The Two Towers|2002
The Lord of the Rings: The Return of the King|2003
Raiders of the Lost Ark|1981
Indiana Jones and the Last Crusade|1989
The Silence of the Lambs|1991
Se7en|1995
Saving Private Ryan|1998
Schindler's List|1993
The Green Mile|1999
The Departed|2006
The Prestige|2006
Memento|2000
The Sixth Sense|1999
Jurassic Park|1993
Terminator 2: Judgment Day|1991
The Terminator|1984
Back to the Future|1985
Alien|1979
Aliens|1986
Blade Runner|1982
The Lion King|1994
Finding Nemo|2003
Toy Story|1995
Up|2009
WALL·E|2008
Ratatouille|2007
The Incredibles|2004
Monsters, Inc.|2001
Shrek|2001
Harry Potter and the Sorcerer's Stone|2001
Harry Potter and the Prisoner of Azkaban|2004
Pirates of the Caribbean: The Curse of the Black Pearl|2003
Spider-Man|2002
Spider-Man 2|2004
Iron Man|2008
The Bourne Identity|2002
The Bourne Supremacy|2004
The Bourne Ultimatum|2007
Casino Royale|2006
300|2007
Sin City|2005
Kill Bill: Vol. 1|2003
Inglourious Basterds|2009
No Country for Old Men|2007
There Will Be Blood|2007
Slumdog Millionaire|2008
American Beauty|1999
Requiem for a Dream|2000
The Truman Show|1998
Groundhog Day|1993
Eternal Sunshine of the Spotless Mind|2004
The Big Lebowski|1998
A Beautiful Mind|2001
Cast Away|2000
The Aviator|2004
Million Dollar Baby|2004
Crash|2004
Little Miss Sunshine|2006
The Social Network|2010
District 9|2009
Star Trek|2009
The Hangover|2009
Wall Street|1987
Jaws|1975
E.T. the Extra-Terrestrial|1982
The Shining|1980
Psycho|1960
2001: A Space Odyssey|1968
Apocalypse Now|1979
Taxi Driver|1976
Goodfellas|1990
Scarface|1983
The Usual Suspects|1995
L.A. Confidential|1997
Heat|1995
Reservoir Dogs|1992
Trainspotting|1996
Amélie|2001
Life Is Beautiful|1997
Cinema Paradiso|1988
Oldboy|2003
Spirited Away|2001
Princess Mononoke|1997
Howl's Moving Castle|2004
My Neighbor Totoro|1988
Grave of the Fireflies|1988
V for Vendetta|2005
Watchmen|2009
Children of Men|2006
Pan's Labyrinth|2006
The Curious Case of Benjamin Button|2008
Gran Torino|2008
Atonement|2007
King Kong|2005
Ocean's Eleven|2001
Catch Me If You Can|2002
Gangs of New York|2002
Minority Report|2002
War of the Worlds|2005
Signs|2002
Unbreakable|2000
The Village|2004
I Am Legend|2007
Mr. & Mrs. Smith|2005
The Italian Job|2003
National Treasure|2004
Twilight|2008
500 Days of Summer|2009
Zombieland|2009
Shaun of the Dead|2004
Hot Fuzz|2007
Superbad|2007
Knocked Up|2007
Mean Girls|2004
The Devil Wears Prada|2006
Love Actually|2003
Notting Hill|1999
Pretty Woman|1990
When Harry Met Sally...|1989
Ghost|1990
Dirty Dancing|1987
Grease|1978
Rocky|1976
Rain Man|1988
Dead Poets Society|1989
Good Will Hunting|1997
A Few Good Men|1992
One Flew Over the Cuckoo's Nest|1975
Chinatown|1974
The Deer Hunter|1978
Full Metal Jacket|1987
Platoon|1986
"""

OUTDIR.mkdir(parents=True, exist_ok=True)


def norm_title(t):
    t = re.sub(r"\s*\(\d{4}\)\s*$", "", t or "")
    t = t.lower().strip()
    t = re.sub(r"^(the|a|an)\s+", "", t)
    t = re.sub(r"[^a-z0-9]+", "", t)
    return t


FAMOUS_YEAR = {}
for ln in FAMOUS.strip().splitlines():
    nm, _, yr = ln.rpartition("|")
    FAMOUS_YEAR[norm_title(nm)] = int(yr)


def fetch(url, dest, min_size):
    if dest.exists() and dest.stat().st_size >= min_size:
        return
    print(f"다운로드: {url}", flush=True)
    urllib.request.urlretrieve(url, dest)
    print(f"  저장 {dest.stat().st_size:,} bytes", flush=True)


fetch(IMDB_URL, TARP, 80_000_000)

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

fetch(BASICS_URL, BASICS, 50_000_000)
meta = {}   # tconst -> (display, year_int_or_None, titleType)
with gzip.open(BASICS, "rt", encoding="utf-8", newline="") as fh:
    fh.readline()
    for line in fh:
        c = line.rstrip("\n").split("\t")
        if len(c) < 6 or c[0] not in needed:
            continue
        yr = c[5].strip()
        yri = int(yr) if yr.isdigit() else None
        disp = f"{c[2].strip()} ({yr})" if yri else c[2].strip()
        meta[c[0]] = (disp, yri, c[1])
        if len(meta) == len(needed):
            break
print(f"메타 매핑 {len(meta):,}/{len(needed):,}", flush=True)


def movie_of(tc):
    m = meta.get(tc)
    return m[0] if m else (f"IMDb {tc}" if tc else "IMDb")


def is_famous(tc):
    m = meta.get(tc)
    if not m:
        return False
    disp, yri, ttype = m
    if ttype != "movie" or yri is None:
        return False
    canon = FAMOUS_YEAR.get(norm_title(disp))
    return canon is not None and abs(yri - canon) <= 1


def build_pool(folder):
    out = []
    for f, tc, t in reviews:
        if f != folder:
            continue
        out.append({"movie": movie_of(tc), "text": t, "famous": is_famous(tc)})
    return out


def assign(folder, rng):
    pool = build_pool(folder)
    rng.shuffle(pool)
    famous = [x for x in pool if x["famous"]]
    plain = [x for x in pool if not x["famous"]]
    fm = len({x["movie"] for x in famous})
    print(f"  {folder}: 유명 리뷰 {len(famous):,} ({fm}편) / 전체 {len(pool):,}", flush=True)

    by_movie = {}
    for x in famous:
        by_movie.setdefault(x["movie"], []).append(x)
    lists = [by_movie[m] for m in sorted(by_movie, key=lambda k: (-len(by_movie[k]), k))]
    ordered = []
    while any(lists):
        for lst in lists:
            if lst:
                ordered.append(lst.pop(0))

    group_rows = {g: [] for g in GROUPS}
    used = set()
    gi = 0
    for x in ordered:
        for _ in range(len(GROUPS)):
            g = GROUPS[gi % len(GROUPS)]
            gi += 1
            if len(group_rows[g]) < FAMOUS_QUOTA_PER_CLASS:
                group_rows[g].append(x)
                used.add(id(x))
                break
        else:
            break

    rest = plain + [x for x in famous if id(x) not in used]
    rng.shuffle(rest)
    ri = 0
    for g in GROUPS:
        while len(group_rows[g]) < PER_CLASS:
            group_rows[g].append(rest[ri])
            ri += 1
        rng.shuffle(group_rows[g])
    return group_rows


pos_groups = assign("pos", random.Random(SEED))
neg_groups = assign("neg", random.Random(SEED + 1))

manifest = []
for i, g in enumerate(GROUPS):
    rows_g = ([(x["text"], 1, x["movie"], g, 1 if x["famous"] else 0) for x in pos_groups[g]] +
              [(x["text"], 0, x["movie"], g, 1 if x["famous"] else 0) for x in neg_groups[g]])
    random.Random(SEED + 10 + i).shuffle(rows_g)
    path = OUTDIR / f"imdb_group_{g}.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["review", "label", "movie", "group", "famous"])
        w.writerows(rows_g)
    fam_rows = sum(1 for r in rows_g if r[4] == 1)
    fam_movies = len({r[2] for r in rows_g if r[4] == 1})
    manifest.append({"group": g, "rows": len(rows_g), "positive": PER_CLASS, "negative": PER_CLASS,
                     "distinct_movies": len({r[2] for r in rows_g}),
                     "famous_rows": fam_rows, "famous_movies": fam_movies, "file": path.name})
    print(f"  {g}조 -> {path.name}  ({len(rows_g):,} rows, 유명 {fam_rows}행 / {fam_movies}편)", flush=True)

with (OUTDIR / "group_manifest.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["group", "rows", "positive", "negative",
                                       "distinct_movies", "famous_rows", "famous_movies", "file"])
    w.writeheader()
    w.writerows(manifest)
print("완료.", flush=True)
