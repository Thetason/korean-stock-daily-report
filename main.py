#!/usr/bin/env python3
"""
한국 주식시장 일일 분석 보고서 자동화 시스템
Korean Stock Daily Report Automation System

사용법:
    python main.py                    # 스케줄러 시작 (자동 실행)
    python main.py manual             # 수동으로 즉시 실행
    python main.py test               # 시스템 테스트
"""

import sys
import os
import argparse
from datetime import datetime
import logging

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scheduler.daily_scheduler import DailyScheduler
from src.utils.email_sender import EmailSender
from src.utils.market_utils import KST

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_report.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_directories():
    """필요한 디렉토리 생성"""
    directories = ['logs', 'reports', 'data']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def run_scheduler():
    """스케줄러 실행 (자동 모드)"""
    try:
        create_directories()
        logger.info("=== 한국 주식시장 일일 분석 보고서 시스템 시작 ===")
        
        scheduler = DailyScheduler()
        scheduler.start()
        
    except KeyboardInterrupt:
        logger.info("사용자가 프로그램을 중단했습니다.")
    except Exception as e:
        logger.error(f"시스템 오류: {e}")
        sys.exit(1)

def run_manual(target_date=None):
    """수동 실행"""
    try:
        create_directories()
        if target_date:
            logger.info(f"=== {target_date} 날짜의 보고서 생성 시작 ===")
        else:
            logger.info("=== 수동으로 보고서 생성 시작 ===")
        
        scheduler = DailyScheduler()
        scheduler.run_manual(target_date=target_date)
        
        logger.info("수동 보고서 생성 완료")
        
    except Exception as e:
        logger.error(f"수동 실행 오류: {e}")
        sys.exit(1)

def run_test():
    """시스템 테스트"""
    try:
        create_directories()
        logger.info("=== 시스템 테스트 시작 ===")
        
        # 1. 모듈 임포트 테스트
        logger.info("1. 모듈 임포트 테스트...")
        from src.data_collector.stock_data_collector import StockDataCollector
        from src.data_collector.investor_data_collector import InvestorDataCollector
        from src.news_crawler.news_crawler import NewsCrawler
        from src.data_processor.stock_analyzer import StockAnalyzer
        from src.report_generator.report_generator import ReportGenerator
        logger.info("✓ 모든 모듈 임포트 성공")
        
        # 2. 설정 파일 테스트
        logger.info("2. 설정 파일 테스트...")
        import json
        with open('config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info("✓ 설정 파일 로드 성공")
        
        # 3. 디렉토리 구조 테스트
        logger.info("3. 디렉토리 구조 테스트...")
        required_dirs = ['src', 'templates', 'config', 'reports', 'data', 'logs']
        for directory in required_dirs:
            if os.path.exists(directory):
                logger.info(f"✓ {directory} 디렉토리 존재")
            else:
                logger.warning(f"✗ {directory} 디렉토리 없음")
        
        # 4. 데이터 수집 테스트 (간단한 테스트)
        logger.info("4. 데이터 수집 테스트...")
        try:
            collector = StockDataCollector()
            market_data = collector.get_index_data()
            if market_data:
                logger.info("✓ 시장 데이터 수집 테스트 성공")
            else:
                logger.warning("✗ 시장 데이터 수집 실패")
        except Exception as e:
            logger.warning(f"✗ 데이터 수집 테스트 실패: {e}")
        
        # 5. 보고서 생성 테스트
        logger.info("5. 보고서 생성 테스트...")
        try:
            report_gen = ReportGenerator()
            
            # 테스트 데이터 생성
            test_data = {
                'market_data': {
                    'kospi': {'current': 2500, 'previous': 2480, 'change_rate': 0.8},
                    'kosdaq': {'current': 750, 'previous': 745, 'change_rate': 0.7}
                },
                'surge_stocks': [],
                'plunge_stocks': [],
                'themes': [],
                'investor_data': {}
            }
            
            html_path = report_gen.generate_daily_report(test_data)
            if os.path.exists(html_path):
                logger.info(f"✓ 테스트 보고서 생성 성공: {html_path}")
            else:
                logger.warning("✗ 테스트 보고서 생성 실패")
                
        except Exception as e:
            logger.warning(f"✗ 보고서 생성 테스트 실패: {e}")
        
        logger.info("=== 시스템 테스트 완료 ===")
        
    except Exception as e:
        logger.error(f"테스트 실행 오류: {e}")
        sys.exit(1)

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='한국 주식시장 일일 분석 보고서 자동화 시스템',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python main.py              # 스케줄러 시작 (평일 16:00 자동 실행)
  python main.py manual       # 지금 즉시 보고서 생성
  python main.py test         # 시스템 테스트 실행
        """
    )
    
    parser.add_argument(
        'mode',
        nargs='?',
        default='scheduler',
        choices=['scheduler', 'manual', 'test'],
        help='실행 모드 선택 (기본값: scheduler)'
    )
    
    parser.add_argument(
        '--date',
        type=str,
        help='특정 날짜의 데이터를 가져옴 (형식: YYYY-MM-DD)'
    )
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║          한국 주식시장 일일 분석 보고서 자동화 시스템          ║
║              Korean Stock Daily Report System               ║
╠══════════════════════════════════════════════════════════════╣
║ 실행 모드: {args.mode:<15}                                 ║
║ 시작 시간: {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S'):<15}                    ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    if args.mode == 'scheduler':
        run_scheduler()
    elif args.mode == 'manual':
        run_manual(target_date=args.date)
    elif args.mode == 'test':
        run_test()

if __name__ == "__main__":
    main()