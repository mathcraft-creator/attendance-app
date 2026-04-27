# 시험지 유사도 분석 웹앱 (고도화 MVP)

Streamlit UI + FastAPI API 기반으로 다음 기능을 제공합니다.

## 구현 기능

1. **Mathpix OCR 결과(lines.json) 기반 시험지 분석 파이프라인**
   - lines.json 문항 자동 분리
   - 시험/OMR/총점 안내문 제거
   - OCR 오탈자 보정
   - 수식 영역(`$...$`, `\(...\)`, `\[...\]`) 보존 + 한글 OCR 오류만 보정

2. **문항별 수학 분석 필드 생성**
   - `unit`, `sub_concept`, `difficulty`, `item_format`, `production_method`, `variation_level`
   - `teacher_intent_type`, `expected_error_point`, `study_direction`, `final_link_level`, `training_method`

3. **유사도 분석 기준 확장**
   - 텍스트 유사도
   - 수식 구조 유사도
   - 단원/세부개념 유사도
   - 풀이 로직 유사도
   - 난이도 유사도
   - 출제 의도 유사도

4. **상담용 해석 라벨 자동 생성**
   - 거의 동일 문항
   - 동일 개념 숫자 변형
   - 풀이 구조 유사
   - 조건 변형
   - 출제 의도 유사
   - 단원만 동일

5. **시험 전체 출제경향 분석**
   - 단원별 문항 수
   - 난이도 분포
   - 출제방식 분포
   - 변형수준 분포
   - 출제 선생님 성향 분석
   - 문항 제작 로직 분석
   - 기말고사 예상 범위 및 대비 전략

6. **엑셀 리포트 생성**
   - `1_시험개요`
   - `2_문항별분석`
   - `3_유사도분석`
   - `4_출제경향분석`
   - `5_현재_다음범위`
   - `6_기말대비전략`
   - `7_수업설계전략`
   - `8_OCR검수로그`

7. **UI 버튼 추가**
   - 시험지 OCR 분석 실행
   - 문항별 수학 분석 실행
   - 유사도 분석 실행
   - 엑셀 상담자료 생성
   - 엑셀 다운로드

8. **카드뉴스 자동생성**
   - 이번 단계에서는 미구현
   - 확장 인터페이스(`extensions.py`)만 제공

---

## 프로젝트 구조

```bash
attendance-app/
├── app.py
├── api_server.py
├── db.py
├── mathpix_pipeline.py
├── math_analysis.py
├── similarity.py
├── trend_analysis.py
├── report_generator.py
├── result_storage.py
├── extensions.py
├── ocr_utils.py
├── question_parser.py
├── requirements.txt
└── .env.example
```

---

## 환경변수

`.env.example` 복사 후 사용:

```bash
cp .env.example .env
```

주요 변수:
- `OPENAI_API_KEY` (없으면 TF-IDF fallback)
- `OPENAI_EMBEDDING_MODEL`
- `REPORT_XLSX_PATH`
- `SIMILARITY_JSON_PATH`
- `GOOGLE_SHEETS_WEBHOOK_URL` (선택)

---

## 설치

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

OCR 사용 시 Tesseract 설치 필요.

---

## 실행

### Streamlit UI

```bash
streamlit run app.py
```

### FastAPI

```bash
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

Swagger: `http://localhost:8000/docs`

---

## API 엔드포인트

- `POST /materials/upload-csv` : 교재 CSV 업로드
- `POST /mathpix/analyze-lines` : Mathpix lines.json 분석
- `POST /similarity/analyze` : 고도화 유사도 분석 + 출제경향
- `POST /report/excel` : 엑셀 리포트 생성

---

## 참고

- OpenAI 키가 없으면 자동으로 TF-IDF 기반 유사도 계산으로 동작합니다.
- Google Sheets 저장은 Apps Script 웹훅 URL을 사용합니다.


---

## 패키징 (배포용)

### 1) 소스 패키지(zip) 생성

```bash
bash scripts/package_project.sh
```

생성물:
- `dist/attendance-app-package-<timestamp>.zip`

### 2) 오프라인 설치용 wheelhouse 생성 (네트워크 가능한 환경)

```bash
bash scripts/build_wheelhouse.sh
```

생성물:
- `wheelhouse/`

### 3) 오프라인 설치

```bash
pip install --no-index --find-links=wheelhouse -r requirements.txt
```

추가 문서: `packaging/README.md`
