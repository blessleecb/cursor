# Strength Week

FastAPI, SQLite, HTML/CSS/JavaScript 기반 운동관리 웹앱입니다.

## 기능

- 2분할 / 3분할 주간 루틴 생성
- 스트렝스 4세트, 근비대 3세트 기본 규칙 반영
- 모든 Day에 이두, 삼두, 어깨 측후면 보조운동 자동 포함
- 운동 도감과 간단한 SVG 일러스트 제공
- 수행 기록 저장
- 최근 기록 기반 다음 중량 추천
- 볼륨 및 추정 1RM 기반 진행 현황 표시

## 실행

```bash
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload
```

브라우저에서 `http://127.0.0.1:8000` 접속.

## 파일 구조

- `app/main.py`: API, DB 초기화, 시드 데이터, 추천 로직
- `static/index.html`: 메인 UI
- `static/styles.css`: Apple 스타일 기반 UI
- `static/app.js`: 프론트엔드 로직
- `workout_app.db`: SQLite 데이터베이스
