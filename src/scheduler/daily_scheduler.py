from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from datetime import datetime
import logging
import json
import os
import pandas as pd
from ..utils.market_utils import is_trading_day, KST
from ..data_collector.stock_data_collector import StockDataCollector
from ..data_collector.investor_data_collector import InvestorDataCollector
from ..news_crawler.news_crawler import NewsCrawler
from ..data_processor.stock_analyzer import StockAnalyzer
from ..report_generator.report_generator import ReportGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DailyScheduler:
    def __init__(self, config_path: str = "config/config.json"):
        self.config = self._load_config(config_path)
        self.scheduler = BlockingScheduler(timezone=KST)
        
        # 모듈 초기화
        self.stock_collector = StockDataCollector()
        self.investor_collector = InvestorDataCollector()
        self.news_crawler = NewsCrawler()
        self.analyzer = StockAnalyzer()
        self.report_generator = ReportGenerator()
        
        self._setup_jobs()
    
    def _load_config(self, config_path: str) -> dict:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
            return {}
    
    def _setup_jobs(self):
        # 일일 보고서 생성 작업 (평일 16:00)
        run_time = self.config.get('scheduler', {}).get('run_time', '16:00')
        hour, minute = map(int, run_time.split(':'))
        
        self.scheduler.add_job(
            func=self.generate_daily_report,
            trigger=CronTrigger(
                hour=hour,
                minute=minute,
                day_of_week='mon-fri',  # 평일만
                timezone=KST
            ),
            id='daily_report',
            name='일일 주식 보고서 생성',
            misfire_grace_time=300  # 5분 지연 허용
        )
        
        logger.info(f"일일 보고서 스케줄 설정 완료: 평일 {run_time}")
    
    def generate_daily_report(self):
        """현재 날짜의 보고서 생성"""
        self.generate_daily_report_for_date(datetime.now(KST))
    
    def generate_daily_report_for_date(self, target_date):
        """특정 날짜의 보고서 생성"""
        try:
            # 거래일 확인
            if not is_trading_day(target_date):
                logger.info(f"{target_date.strftime('%Y-%m-%d')}은 거래일이 아닙니다. 보고서 생성을 건너뜁니다.")
                return
            
            logger.info(f"{target_date.strftime('%Y-%m-%d')} 날짜의 보고서 생성 시작")
            
            # 1. 데이터 수집
            logger.info("1. 데이터 수집 중...")
            report_data = self._collect_all_data(target_date)
            
            # 2. 데이터 분석
            logger.info("2. 데이터 분석 중...")
            analyzed_data = self._analyze_data(report_data)
            
            # 3. 보고서 생성
            logger.info("3. 보고서 생성 중...")
            html_path = self.report_generator.generate_daily_report(analyzed_data, target_date)
            
            # 4. PDF 생성 (선택사항)
            logger.info("4. PDF 생성 중...")
            pdf_path = self.report_generator.generate_pdf_report(html_path)
            if not pdf_path:
                logger.info("PDF는 생성되지 않았습니다. HTML 보고서만 사용합니다.")
            
            # 5. 데이터 백업
            logger.info("5. 데이터 백업 중...")
            self.report_generator.save_report_data(analyzed_data, target_date)
            
            logger.info(f"일일 보고서 생성 완료: {html_path}, {pdf_path}")
            
            # 6. 이메일 발송 (선택사항)
            if self.config.get('email', {}).get('recipients'):
                logger.info("6. 이메일 발송 중...")
                self._send_email(html_path, pdf_path, target_date)
            
        except Exception as e:
            logger.error(f"일일 보고서 생성 실패: {e}")
            raise
    
    def _collect_all_data(self, date: datetime) -> dict:
        data = {}
        
        try:
            # 지수 데이터 수집
            logger.info("지수 데이터 수집 중...")
            data['market_data'] = self.stock_collector.get_index_data(date)
            
            # 종목 리스트 수집
            logger.info("종목 리스트 수집 중...")
            tickers = self.stock_collector.get_stock_list("ALL")
            
            # 주식 데이터 수집 (메모리 고려하여 배치 처리)
            logger.info(f"주식 데이터 수집 중... ({len(tickers)}개 종목)")
            batch_size = 500
            all_stock_data = []
            
            for i in range(0, len(tickers), batch_size):
                batch_tickers = tickers[i:i+batch_size]
                batch_data = self.stock_collector.get_stock_data(batch_tickers, date)
                if not batch_data.empty:
                    all_stock_data.append(batch_data)
                logger.info(f"배치 {i//batch_size + 1}/{(len(tickers) + batch_size - 1)//batch_size} 완료")
            
            # 데이터 병합
            if all_stock_data:
                data['stock_data'] = pd.concat(all_stock_data, ignore_index=True)
            else:
                data['stock_data'] = pd.DataFrame()
            
            # 투자자별 거래 데이터 수집
            logger.info("투자자별 거래 데이터 수집 중...")
            data['investor_data'] = self.investor_collector.get_investor_trading_data(date)
            data['hourly_investor_data'] = self.investor_collector.get_hourly_investor_data(date)
            
            # 뉴스 데이터 수집
            logger.info("뉴스 데이터 수집 중...")
            data['news_data'] = self.news_crawler.get_market_news(date)
            data['overseas_data'] = self.news_crawler.get_overseas_market_news()
            
        except Exception as e:
            logger.error(f"데이터 수집 중 오류: {e}")
            raise
        
        return data
    
    def _analyze_data(self, data: dict) -> dict:
        try:
            stock_data = data.get('stock_data', pd.DataFrame())
            
            if stock_data.empty:
                logger.warning("주식 데이터가 없어 기본 분석만 수행합니다.")
                return {
                    'market_data': data.get('market_data', {}),
                    'investor_data': data.get('hourly_investor_data', {}),
                    'overseas_data': data.get('overseas_data', {}),
                    'surge_stocks': [],
                    'plunge_stocks': [],
                    'themes': [],
                    'market_sentiment': {}
                }
            
            # 급등/급락 종목 분석
            surge_stocks = self.analyzer.analyze_surge_stocks(stock_data)
            plunge_stocks = self.analyzer.analyze_plunge_stocks(stock_data)
            
            # 테마 분석
            themes = self.analyzer.identify_themes(surge_stocks)
            
            # 시장 심리 분석
            market_sentiment = self.analyzer.calculate_market_sentiment(stock_data)
            
            return {
                'market_data': data.get('market_data', {}),
                'investor_data': data.get('hourly_investor_data', {}),
                'overseas_data': data.get('overseas_data', {}),
                'surge_stocks': surge_stocks,
                'plunge_stocks': plunge_stocks,
                'themes': themes,
                'market_sentiment': market_sentiment,
                'news_data': data.get('news_data', [])
            }
            
        except Exception as e:
            logger.error(f"데이터 분석 중 오류: {e}")
            raise
    
    def _send_email(self, html_path: str, pdf_path: str, date: datetime):
        try:
            # 이메일 발송 기능은 별도 모듈로 구현 예정
            logger.info("이메일 발송 기능은 추후 구현 예정입니다.")
            pass
        except Exception as e:
            logger.error(f"이메일 발송 실패: {e}")
    
    def run_manual(self, target_date=None):
        """수동 실행"""
        if target_date:
            # 문자열을 datetime 객체로 변환
            from datetime import datetime
            try:
                date = datetime.strptime(target_date, "%Y-%m-%d")
                date = KST.localize(date)
                logger.info(f"{target_date} 날짜의 보고서를 생성합니다.")
                self.generate_daily_report_for_date(date)
            except ValueError:
                logger.error(f"잘못된 날짜 형식: {target_date}. YYYY-MM-DD 형식을 사용하세요.")
                raise
        else:
            logger.info("수동으로 일일 보고서 생성을 시작합니다.")
            self.generate_daily_report()
    
    def start(self):
        """스케줄러 시작"""
        logger.info("일일 주식 보고서 스케줄러를 시작합니다.")
        logger.info("예정된 작업:")
        for job in self.scheduler.get_jobs():
            logger.info(f"- {job.name}: {job.next_run_time}")
        
        try:
            self.scheduler.start()
        except KeyboardInterrupt:
            logger.info("스케줄러가 사용자에 의해 중단되었습니다.")
            self.scheduler.shutdown()
        except Exception as e:
            logger.error(f"스케줄러 실행 중 오류: {e}")
            raise
    
    def stop(self):
        """스케줄러 중지"""
        logger.info("스케줄러를 중지합니다.")
        self.scheduler.shutdown()