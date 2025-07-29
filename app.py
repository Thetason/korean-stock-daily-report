#!/usr/bin/env python3
"""
Korean Stock Daily Report Web Application
"""

from flask import Flask, render_template, jsonify, send_file, request
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import sys
import logging
import json
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scheduler.daily_scheduler import DailyScheduler
from src.utils.market_utils import KST, is_trading_day

app = Flask(__name__)
CORS(app)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 전역 스케줄러 인스턴스
scheduler = None

def get_scheduler():
    global scheduler
    if scheduler is None:
        scheduler = DailyScheduler()
    return scheduler

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('web_interface.html')

@app.route('/api/generate', methods=['POST'])
def generate_report():
    """리포트 생성 API"""
    try:
        data = request.get_json()
        date_str = data.get('date')
        
        if date_str:
            # 특정 날짜 리포트 생성
            date = datetime.strptime(date_str, "%Y-%m-%d")
            date = KST.localize(date)
            
            # 거래일 확인
            if not is_trading_day(date):
                return jsonify({
                    'success': False,
                    'message': f'{date_str}은 거래일이 아닙니다.'
                }), 400
            
            logger.info(f"Generating report for {date_str}")
            scheduler = get_scheduler()
            scheduler.generate_daily_report_for_date(date)
        else:
            # 오늘 날짜 리포트 생성
            logger.info("Generating report for today")
            scheduler = get_scheduler()
            scheduler.generate_daily_report()
        
        return jsonify({
            'success': True,
            'message': '리포트 생성이 완료되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return jsonify({
            'success': False,
            'message': f'리포트 생성 실패: {str(e)}'
        }), 500

@app.route('/api/reports')
def list_reports():
    """생성된 리포트 목록"""
    try:
        reports_dir = Path('reports')
        reports = []
        
        if reports_dir.exists():
            for date_dir in sorted(reports_dir.iterdir(), reverse=True):
                if date_dir.is_dir():
                    date_str = date_dir.name
                    html_file = date_dir / f'daily_report_{date_str}.html'
                    pdf_file = date_dir / f'daily_report_{date_str}.pdf'
                    
                    if html_file.exists():
                        reports.append({
                            'date': date_str,
                            'html': html_file.exists(),
                            'pdf': pdf_file.exists(),
                            'created_at': datetime.fromtimestamp(html_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        })
        
        return jsonify({
            'success': True,
            'reports': reports
        })
        
    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/report/<date>')
def view_report(date):
    """리포트 보기"""
    try:
        html_path = Path(f'reports/{date}/daily_report_{date}.html')
        
        if not html_path.exists():
            return jsonify({
                'success': False,
                'message': '리포트가 존재하지 않습니다.'
            }), 404
        
        return send_file(html_path)
        
    except Exception as e:
        logger.error(f"Failed to view report: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/report/<date>/download/<format>')
def download_report(date, format):
    """리포트 다운로드"""
    try:
        if format == 'html':
            file_path = Path(f'reports/{date}/daily_report_{date}.html')
        elif format == 'pdf':
            file_path = Path(f'reports/{date}/daily_report_{date}.pdf')
        else:
            return jsonify({
                'success': False,
                'message': '지원하지 않는 형식입니다.'
            }), 400
        
        if not file_path.exists():
            return jsonify({
                'success': False,
                'message': '파일이 존재하지 않습니다.'
            }), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f'korean_stock_report_{date}.{format}'
        )
        
    except Exception as e:
        logger.error(f"Failed to download report: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/trading-days')
def get_trading_days():
    """최근 30일간의 거래일 목록"""
    try:
        trading_days = []
        today = datetime.now(KST)
        
        for i in range(30):
            date = today - timedelta(days=i)
            if is_trading_day(date):
                trading_days.append(date.strftime('%Y-%m-%d'))
        
        return jsonify({
            'success': True,
            'trading_days': trading_days
        })
        
    except Exception as e:
        logger.error(f"Failed to get trading days: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/status')
def get_status():
    """시스템 상태 확인"""
    try:
        config_path = Path('config/config.json')
        config = {}
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        return jsonify({
            'success': True,
            'status': 'online',
            'config': {
                'scheduler_time': config.get('scheduler', {}).get('run_time', '16:00'),
                'surge_threshold': config.get('analysis', {}).get('surge_threshold', 5),
                'plunge_threshold': config.get('analysis', {}).get('plunge_threshold', -5)
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # 필요한 디렉토리 생성
    os.makedirs('logs', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # 개발 서버 실행
    app.run(host='0.0.0.0', port=5000, debug=True)