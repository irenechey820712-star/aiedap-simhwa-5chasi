# Movie Review Corpus Lab — 조별 분산 버전

## 폴더 구조

```text
repo/
├─ index.html
├─ build_group_shards.py
└─ data/
   ├─ imdb50k.csv
   ├─ imdb_group_A.csv
   ├─ imdb_group_B.csv
   ├─ imdb_group_C.csv
   ├─ imdb_group_D.csv
   ├─ imdb_group_E.csv
   ├─ imdb_group_F.csv
   └─ group_manifest.csv
```

## 사용 순서

1. 기존 `data/imdb50k.csv` 준비
2. `python build_group_shards.py`
3. 생성된 A~F CSV를 GitHub에 push
4. `Movie_Review_Corpus_Lab.html`을 `index.html`로 올리기
5. GitHub Pages 활성화

## 조별 링크 예시

- A조: `https://USERNAME.github.io/REPO/?group=A`
- B조: `https://USERNAME.github.io/REPO/?group=B`
- C조: `https://USERNAME.github.io/REPO/?group=C`
- D조: `https://USERNAME.github.io/REPO/?group=D`
- E조: `https://USERNAME.github.io/REPO/?group=E`
- F조: `https://USERNAME.github.io/REPO/?group=F`

각 링크는 해당 조 CSV만 자동으로 읽습니다.

## 구성

- 조당 2,000개
- Positive 1,000
- Negative 1,000
- A~F 서로 겹치지 않는 표본
- 난수 시드 고정 → 재생성해도 동일한 분할
