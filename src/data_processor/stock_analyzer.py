import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging
from ..utils.market_utils import KST
from ..utils.sector_classifier import SectorClassifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockAnalyzer:
    def __init__(self, surge_threshold: float = 5.0, plunge_threshold: float = -5.0):
        self.surge_threshold = surge_threshold
        self.plunge_threshold = plunge_threshold
        self.sector_classifier = SectorClassifier()
    
    def analyze_surge_stocks(self, stock_data: pd.DataFrame, max_count: int = 50) -> List[Dict]:
        if stock_data.empty:
            return []
        
        # 5% 이상 상승 종목 필터링
        surge_stocks = stock_data[stock_data['change_rate'] >= self.surge_threshold].copy()
        
        # 상승률 기준 내림차순 정렬
        surge_stocks = surge_stocks.sort_values('change_rate', ascending=False)
        
        # 최대 개수 제한
        surge_stocks = surge_stocks.head(max_count)
        
        result = []
        for _, row in surge_stocks.iterrows():
            stock_info = {
                'ticker': row['ticker'],
                'name': row['name'],
                'sector': self._get_sector_info(row['ticker']),
                'base_price': int(row['previous_price']),
                'current_price': int(row['current_price']),
                'change_rate': round(row['change_rate'], 2),
                'volume': int(row['volume']),
                'volume_surge': self._check_volume_surge(row),
                'reason': self._get_surge_reason(row['ticker'], row['change_rate'])
            }
            result.append(stock_info)
        
        logger.info(f"급등 종목 분석 완료: {len(result)}개 종목")
        return result
    
    def analyze_plunge_stocks(self, stock_data: pd.DataFrame, max_count: int = 30) -> List[Dict]:
        if stock_data.empty:
            return []
        
        # 5% 이상 하락 종목 필터링
        plunge_stocks = stock_data[stock_data['change_rate'] <= self.plunge_threshold].copy()
        
        # 하락률 기준 오름차순 정렬 (가장 많이 떨어진 순)
        plunge_stocks = plunge_stocks.sort_values('change_rate', ascending=True)
        
        # 최대 개수 제한
        plunge_stocks = plunge_stocks.head(max_count)
        
        result = []
        for _, row in plunge_stocks.iterrows():
            stock_info = {
                'ticker': row['ticker'],
                'name': row['name'],
                'sector': self._get_sector_info(row['ticker']),
                'base_price': int(row['previous_price']),
                'current_price': int(row['current_price']),
                'change_rate': round(row['change_rate'], 2),
                'volume': int(row['volume']),
                'volume_surge': self._check_volume_surge(row),
                'reason': self._get_plunge_reason(row['ticker'], row['change_rate'])
            }
            result.append(stock_info)
        
        logger.info(f"급락 종목 분석 완료: {len(result)}개 종목")
        return result
    
    def analyze_volume_surge_stocks(self, stock_data: pd.DataFrame, multiplier: float = 3.0) -> List[Dict]:
        if stock_data.empty:
            return []
        
        # 거래량 급증 종목 (전일 대비 3배 이상, 임시로 상위 거래량 기준 사용)
        # 실제로는 전일 거래량 데이터와 비교 필요
        high_volume_stocks = stock_data.nlargest(20, 'volume')
        
        result = []
        for _, row in high_volume_stocks.iterrows():
            if row['volume'] > 0:  # 거래량이 있는 종목만
                stock_info = {
                    'ticker': row['ticker'],
                    'name': row['name'],
                    'volume': int(row['volume']),
                    'change_rate': round(row['change_rate'], 2),
                    'current_price': int(row['current_price'])
                }
                result.append(stock_info)
        
        logger.info(f"거래량 급증 종목 분석 완료: {len(result)}개 종목")
        return result
    
    def analyze_sector_performance(self, stock_data: pd.DataFrame) -> Dict:
        if stock_data.empty:
            return {}
        
        # 섹터별 성과 분석 (간단한 분류)
        sectors = {}
        
        for _, row in stock_data.iterrows():
            sector = self._get_sector_info(row['ticker'])
            if sector not in sectors:
                sectors[sector] = {
                    'stocks': [],
                    'avg_change_rate': 0,
                    'total_volume': 0
                }
            
            sectors[sector]['stocks'].append({
                'ticker': row['ticker'],
                'name': row['name'],
                'change_rate': row['change_rate']
            })
            sectors[sector]['total_volume'] += row['volume']
        
        # 각 섹터별 평균 수익률 계산
        for sector_name, sector_data in sectors.items():
            if sector_data['stocks']:
                avg_rate = np.mean([stock['change_rate'] for stock in sector_data['stocks']])
                sectors[sector_name]['avg_change_rate'] = round(avg_rate, 2)
        
        # 성과 기준으로 정렬
        sorted_sectors = dict(sorted(sectors.items(), 
                                   key=lambda x: x[1]['avg_change_rate'], 
                                   reverse=True))
        
        logger.info(f"섹터 성과 분석 완료: {len(sorted_sectors)}개 섹터")
        return sorted_sectors
    
    def identify_themes(self, surge_stocks: List[Dict], news_keywords: List[str] = None) -> List[Dict]:
        if not surge_stocks:
            return []
        
        # 섹터 기반 테마 분석
        sector_groups = {}
        
        for stock in surge_stocks:
            sector = stock.get('sector', '기타')
            if sector not in sector_groups:
                sector_groups[sector] = []
            sector_groups[sector].append(stock)
        
        # 추가 테마 키워드 (뉴스 기반)
        special_themes = {
            'AI/ChatGPT': ['AI', '인공지능', 'ChatGPT', '챗GPT', '생성AI'],
            'K-컬처': ['한류', 'BTS', 'K-POP', '웹툰', 'OTT'],
            '메타버스': ['메타버스', 'VR', 'AR', '가상현실'],
            '수소경제': ['수소', '연료전지', '그린수소'],
            '우주항공': ['우주', '위성', '발사체', '항공우주'],
            '탄소중립': ['ESG', '친환경', '태양광', '풍력'],
            '국방': ['방산', '국방', '무기', '방위산업']
        }
        
        # 특별 테마 식별
        for theme_name, keywords in special_themes.items():
            matching_stocks = []
            for stock in surge_stocks:
                stock_name = stock['name']
                if any(keyword in stock_name for keyword in keywords):
                    matching_stocks.append(stock)
            
            if matching_stocks:
                sector_groups[theme_name] = matching_stocks
        
        # 테마별 분석 결과 생성
        theme_analysis = []
        for theme_name, theme_stocks in sector_groups.items():
            if len(theme_stocks) >= 2:  # 2개 이상 종목이 있는 테마만
                avg_change_rate = np.mean([stock['change_rate'] for stock in theme_stocks])
                
                # 상승률과 거래량을 고려한 대표 종목 선정
                representative_stocks = sorted(
                    theme_stocks, 
                    key=lambda x: (x['change_rate'] * 0.7 + (x['volume']/1000000) * 0.3), 
                    reverse=True
                )[:3]  # 상위 3개
                
                # 메가 섹터 정보 추가
                mega_sector = self.sector_classifier.get_mega_sector(theme_name)
                
                theme_analysis.append({
                    'theme': theme_name,
                    'mega_sector': mega_sector,
                    'stock_count': len(theme_stocks),
                    'avg_change_rate': round(avg_change_rate, 2),
                    'total_volume': sum(stock['volume'] for stock in theme_stocks),
                    'representative_stocks': representative_stocks,
                    'description': self.sector_classifier.get_sector_description(theme_name)
                })
        
        # 평균 상승률과 종목 수를 고려한 정렬
        theme_analysis.sort(
            key=lambda x: (x['avg_change_rate'] * x['stock_count']), 
            reverse=True
        )
        
        logger.info(f"고도화된 테마 분석 완료: {len(theme_analysis)}개 테마")
        return theme_analysis
    
    def _get_sector_info(self, ticker: str) -> str:
        try:
            # pykrx를 사용해 종목명 가져오기
            from pykrx import stock
            company_name = stock.get_market_ticker_name(ticker)
            
            # 고도화된 섹터 분류기 사용
            sector = self.sector_classifier.classify_sector(ticker, company_name)
            
            return sector
            
        except Exception as e:
            logger.warning(f"섹터 정보 조회 실패 ({ticker}): {e}")
            # 분류기만으로 시도
            try:
                return self.sector_classifier.classify_sector(ticker, ticker)
            except:
                return '기타'
    
    def _check_volume_surge(self, stock_row: pd.Series) -> bool:
        # 거래량 급증 여부 (임시로 높은 거래량 기준)
        return stock_row['volume'] > 1000000  # 100만주 이상
    
    def _get_surge_reason(self, ticker: str, change_rate: float) -> str:
        # 급등 이유 추정 (실제로는 뉴스 분석과 연계)
        if change_rate > 20:
            return "급등 / 재료 발생 의심"
        elif change_rate > 10:
            return "강세 / 시장 주목"
        else:
            return "상승 / 매수세 유입"
    
    def _get_plunge_reason(self, ticker: str, change_rate: float) -> str:
        # 급락 이유 추정
        if change_rate < -20:
            return "급락 / 악재 발생 의심"
        elif change_rate < -10:
            return "약세 / 매도 압력"
        else:
            return "하락 / 조정"
    
    def calculate_market_sentiment(self, stock_data: pd.DataFrame) -> Dict:
        if stock_data.empty:
            return {}
        
        # 시장 심리 지표 계산
        total_stocks = len(stock_data)
        rising_stocks = len(stock_data[stock_data['change_rate'] > 0])
        falling_stocks = len(stock_data[stock_data['change_rate'] < 0])
        unchanged_stocks = total_stocks - rising_stocks - falling_stocks
        
        # 등락 비율
        rising_ratio = (rising_stocks / total_stocks) * 100 if total_stocks > 0 else 0
        falling_ratio = (falling_stocks / total_stocks) * 100 if total_stocks > 0 else 0
        
        # 시장 강도
        avg_change_rate = stock_data['change_rate'].mean()
        
        sentiment = {
            'total_stocks': total_stocks,
            'rising_stocks': rising_stocks,
            'falling_stocks': falling_stocks,
            'unchanged_stocks': unchanged_stocks,
            'rising_ratio': round(rising_ratio, 1),
            'falling_ratio': round(falling_ratio, 1),
            'avg_change_rate': round(avg_change_rate, 2),
            'market_mood': self._determine_market_mood(rising_ratio, avg_change_rate)
        }
        
        return sentiment
    
    def _determine_market_mood(self, rising_ratio: float, avg_change_rate: float) -> str:
        if rising_ratio > 60 and avg_change_rate > 1:
            return "강세"
        elif rising_ratio > 50 and avg_change_rate > 0:
            return "보합강세"
        elif rising_ratio < 40 and avg_change_rate < -1:
            return "약세"
        elif rising_ratio < 50 and avg_change_rate < 0:
            return "보합약세"
        else:
            return "보합"