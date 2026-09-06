# Movie Review Corpus Lab — 조별 분산 버전

## 폴더 구조

```text
repo/
├─ Movie_Review_Corpus_Lab.html
├─ build_group_shards.py        # 표준 라이브러리만 사용 (pandas 불필요)
└─ data/
   ├─ imdb_group_A.csv          # 열: review,label,movie,group
   ├─ imdb_group_B.csv
   ├─ imdb_group_C.csv
   ├─ imdb_group_D.csv
   ├─ imdb_group_E.csv
   ├─ imdb_group_F.csv
   └─ group_manifest.csv
```

## 데이터 재생성

```bash
python build_group_shards.py .        # ./data/ 아래에 생성
```

스크립트가 자동으로:
1. Stanford Large Movie Review Dataset v1 다운로드 (~84 MB)
2. 각 리뷰의 IMDb 영화 ID를 추출
3. IMDb 공식 데이터셋(`title.basics.tsv.gz`, ~226 MB)으로 **영화 제목 매핑**
4. `data/imdb_group_A~F.csv` + `group_manifest.csv` 생성

다운로드 파일은 스크립트 폴더에 캐시되어 재실행 시 다시 받지 않습니다.
이미 `data/` CSV가 커밋되어 있으므로 **보통은 다시 돌릴 필요가 없습니다.**

## 조별 링크

| 조 | 링크 |
|---|---|
| A | `https://USERNAME.github.io/REPO/Movie_Review_Corpus_Lab.html?group=A` |
| B~F | 위에서 `?group=B` … `?group=F` |

각 링크는 해당 조 CSV만 자동으로 내려받습니다.
「🧑‍🏫 강사용 6개 조 비교」 버튼은 A~F 6개 조를 한 번에 로드합니다.

## 구성

- 조당 2,000개 = Positive 1,000 + Negative 1,000
- A~F 서로 겹치지 않는 표본, 난수 시드 고정 → 재생성해도 동일 분할
- CSV 열: `review,label,movie,group,famous`
- 각 리뷰에 **영화 제목(연도)** 포함 — 데이터 표·KWIC 뷰어에 표시됨
- 조당 약 1,500편의 서로 다른 영화 (영화당 최대 30개 리뷰, Stanford 데이터셋 규칙)
- IMDb에서 병합·삭제된 옛 ID(약 5%)는 `IMDb tt0000000` 형태로 표기

### 대중적인 영화 태그 (`famous=1`)

- 학생들이 알 만한 대중적 영화(개봉연도까지 대조해 동명이작 배제)의 리뷰에 `famous=1`
- 조당 약 60행 / 14~16편 (Titanic, Scarface, Apocalypse Now, The Bourne Ultimatum,
  The Italian Job, Dirty Dancing, Inglourious Basterds, 2001: A Space Odyssey,
  The Shining, Crash, Oldboy, National Treasure, The Matrix Reloaded 등)
- 앱에서 쓰이는 곳:
  - **데이터 표** — 유명 영화 칩으로 좁혀 보기
  - **MOVIE QUIZ** — 제목이 가려진 리뷰를 읽고 4지선다로 영화 맞히기 (10문항)
