#!/bin/bash

# Korean Stock Report Streamlit Runner

echo "=== 한국 주식 일일 리포트 웹 서비스 ==="
echo "브라우저에서 http://localhost:8501 로 접속하세요"
echo ""

# 필요한 패키지 설치
pip install streamlit

# Streamlit 실행
streamlit run streamlit_app.py