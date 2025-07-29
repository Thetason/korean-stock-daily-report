# 📈 Korean Stock Daily Report
한국 주식시장 일일 분석 리포트 자동화 시스템

## 🌟 주요 기능
- KOSPI/KOSDAQ 지수 분석
- 급등/급락 종목 탐지 (±5% 기준)
- 투자자별 매매 동향 분석
- 주요 뉴스 크롤링
- HTML/PDF 리포트 자동 생성
- 웹 인터페이스 제공

## 🚀 빠른 시작

### 1. 설치
```bash
git clone https://github.com/[your-username]/korean-stock-daily-report.git
cd korean-stock-daily-report
pip install -r requirements.txt
```

### 2. 웹 인터페이스 실행
```bash
streamlit run streamlit_app.py
```

### 3. 브라우저에서 접속
```
http://localhost:8501
```

## 💻 사용 방법

### 웹 인터페이스 (추천)
1. 브라우저에서 접속
2. "오늘 리포트 즉시 생성" 버튼 클릭
3. 생성된 리포트 확인 및 다운로드

### 명령줄 인터페이스
```bash
# 오늘 리포트 생성
python main.py manual

# 특정 날짜 리포트 생성
python main.py manual --date 2025-07-28

# 자동 스케줄러 실행 (매일 16:00)
python main.py
```

## 📊 리포트 내용
- 시장 개요 (KOSPI/KOSDAQ)
- 급등 종목 TOP 20
- 급락 종목 TOP 20
- 테마별 동향
- 투자자별 매매 분석
- 주요 뉴스

## 🛠️ 기술 스택
- Python 3.9+
- pandas, numpy (데이터 처리)
- yfinance, pykrx (주식 데이터)
- BeautifulSoup4 (뉴스 크롤링)
- Streamlit (웹 인터페이스)
- Jinja2 (리포트 템플릿)

## 📁 프로젝트 구조
```
korean-stock-daily-report/
├── streamlit_app.py      # 웹 인터페이스
├── main.py              # CLI 진입점
├── requirements.txt     # 패키지 의존성
├── config/             # 설정 파일
├── src/               # 소스 코드
│   ├── data_collector/   # 데이터 수집
│   ├── data_processor/   # 데이터 분석
│   ├── news_crawler/     # 뉴스 크롤링
│   ├── report_generator/ # 리포트 생성
│   └── utils/           # 유틸리티
├── templates/          # HTML 템플릿
├── reports/           # 생성된 리포트
└── logs/             # 로그 파일
```

## 🌐 온라인 배포

### Streamlit Cloud (무료)
1. 이 저장소를 Fork
2. [share.streamlit.io](https://share.streamlit.io) 접속
3. GitHub 연결 후 배포

## 📝 라이선스
MIT License

## 🤝 기여
이슈와 PR은 언제나 환영합니다!

---
Made with ❤️ for Korean stock investors