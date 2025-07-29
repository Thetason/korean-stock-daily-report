#!/bin/bash

# Korean Stock Report Web Server Runner

echo "=== Korean Stock Daily Report Web Server ==="
echo "Starting web server at http://localhost:5000"
echo ""

# 가상환경이 있다면 활성화
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 필요한 패키지 설치 확인
pip install flask flask-cors

# Flask 앱 실행
export FLASK_APP=app.py
export FLASK_ENV=development

python app.py