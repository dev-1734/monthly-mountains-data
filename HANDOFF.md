# 인수인계 — monthly-mountains-data (2026-09-14)

앱이 읽는 정적 데이터를 만들어 GitHub Pages 로 배포하는 레포.
전체 그림은 [앱 레포의 docs/HANDOFF.md](https://github.com/dev-1734/monthly-mountains/blob/main/docs/HANDOFF.md).

> 조직 이전 완료: 저장소는 `dev-1734/monthly-mountains-data`, Pages 루트는
> `https://dev-1734.github.io/monthly-mountains-data/` 를 사용한다.

## 현재 운영 상태

Pages 가 300개 산 데이터를 서빙하고, signals 수집기가 300개를 돌고,
예보가 3시간마다 300개 파일을 갱신한다.
세 레포의 관계는 `monthly-mountains`(앱) → `monthly-mountains-data`(공개 산출물) ← `monthly-mountains-signals`(private 수집) 구조다.

✅ 웹 사진 103장 저작권 검토는 2026-08-10 에 끝났다(문제 없음).

⚠️ **이 레포의 main 은 스스로 움직인다.** `forecast-weather` 등 자동화가 main 에 직접
커밋하므로 작업 브랜치는 가만히 있어도 뒤처지고 생성물에서 충돌할 수 있다.
**브랜치는 짧게 살리고 빨리 머지할 것.**

## ✅ `DATA_GO_KR_KEY` 등록 완료

**디코딩 키**를 등록해야 한다 — `collect_weather.py` 가 `serviceKey` 를 requests params 로
넘겨 다시 URL 인코딩하므로, 인코딩 키를 넣으면 이중 인코딩으로 인증에 실패한다.

```bash
gh secret set DATA_GO_KR_KEY --repo dev-1734/monthly-mountains-data --body "<디코딩 키>"
```

**세 워크플로 모두 크론이 켜져 있고 미구현 스크립트는 없다**.

### 파일데이터 2건 — 변환본을 커밋해 뒀다

원본은 다운로드에 로그인이 필요해 CI 가 못 받는다. `data/raw/`(gitignore)에 풀고
가벼운 JSON 으로 바꿔 레포에 넣었다. **CI 는 변환본만 읽는다.**

| 원본 | 스크립트 | 산출물 | 상태 |
|---|---|---|---|
| 전국등산로표준데이터 (265MB) | `build_trail_index.py` | `pipeline/trails.json` (1.9MB) | ✅ 산 2,932개 · 코스 7,759개 |
| 국립공원 공원경계 (SHP) | `build_park_index.py` | `pipeline/park_buffer_3km.json` | ⚠️ 경계가 아니라 **3km 버퍼** |

```bash
unzip mountain.zip -d data/raw/trails
python3 pipeline/build_trail_index.py
python3 pipeline/build_trail_index.py --match
python3 pipeline/build_park_index.py
python3 pipeline/geo.py
```

## 현재 배포 상태

```
https://dev-1734.github.io/monthly-mountains-data/data/v1/
  manifest.json          ✅
  mountains.json         ✅ 300개 (`seed: false`)
  crowd_model.json       ✅ 실측 학습본 · 산 300/300
  photos/<id>.jpg        ✅ 웹 수집분
  signals/<id>.json      ✅ signals 레포가 push
  restaurants/<id>.json ✅ signals 레포가 push
  forecast/<id>.json     ✅ 3시간마다 갱신
```

⚠️ **Pages 는 레포 루트를 서빙**하므로 URL 에 `data/` 가 들어간다.
앱의 `DataStore.remoteBase` 는 현재 `https://dev-1734.github.io/monthly-mountains-data/data/v1/` 로 맞춰져 있다.

## 워크플로

| 파일 | 주기 | 상태 |
|---|---|---|
| `build-mountains.yml` | 매월 1일 03:00 KST | ✅ 크론 활성 |
| `forecast-weather.yml` | 3시간마다 | ✅ 크론 활성 |
| `train-crowd.yml` | 매주 월 04:00 KST | ✅ 크론 활성 |
| GitHub Pages | push | ✅ 저장소 Pages 설정에 의존 |

⚠️ 산 300개면 `forecast-weather` 가 회차마다 300개 파일을 커밋한다.
레포가 꾸준히 커지므로 커지면 예보를 orphan 브랜치로 옮기는 걸 고려할 것.

### `build_mountains.py`

```bash
python3 pipeline/build_mountains.py
python3 pipeline/build_mountains.py --limit 40 --no-photo
python3 pipeline/build_crowd_params.py --refresh
python3 pipeline/validate.py data/v1/
```

- 조인은 **100대명산 `mtnCd` ↔ `trails.json` 코드**가 1순위, 없을 때만 `find_for()`
- `ascentM`·`kmaMountainCode` 는 원천이 없어 null 가능
- `parkType` 은 `NATIONAL_PARKS` 손 매핑
- 기존 `mountains.json` 의 **id 를 이름으로 승계**한다. id 는 즐겨찾기 저장 키라 바뀌면 안 된다
- 원천 응답은 `data/raw/api_cache/`(gitignore)에 캐시
- 코스 우선순위는 **`curated_courses.json` > 라우팅 > 이름 묶음**

### `build_crowd_params.py`

`build_mountains.py` 뒤에 **반드시 돌린다**. 안 돌리면 파라미터 없는 산이 앱 fallback으로 떨어져 혼잡도가 평평해진다.

## 이미 확보된 것

- `pipeline/crowd_fit.json` — 설악산 실측 계수
- `pipeline/flagship_species.json` — 국립공원 깃대종
- `pipeline/holidays.json` — 공휴일
- `pipeline/train_crowd.py` — 실측 학습기
- `pipeline/make_dev_samples.py` — 앱 번들 스키마 표본 생성
- `pipeline/geo.py` — 좌표 변환과 점-다각형 판정
- `pipeline/trails.json` — 산 코스·들머리
- `pipeline/curated_courses.json` — 손입력 코스
- `pipeline/fetch_visitor_stats.py` — 탐방객 CSV 수집
- `pipeline/fetch_web_photos.py` + `web_photos.json` — 사진 수집/대장
- `pipeline/validate.py` — 스키마·값 범위·커버리지 교차검사

## 주의

- 전 워크플로에 `timeout-minutes` 를 유지한다.
- public 레포지만 fork PR 워크플로에는 시크릿이 전달되지 않는다.
- `pull_request_target` 은 쓰지 않는다.
