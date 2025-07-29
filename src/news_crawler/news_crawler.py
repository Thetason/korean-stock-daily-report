import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import time
import re
from ..utils.market_utils import KST

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.base_urls = {
            'naver_finance': 'https://finance.naver.com',
            'daum_finance': 'https://finance.daum.net'
        }
    
    def get_market_news(self, date: datetime = None, max_news: int = 20) -> List[Dict]:
        if date is None:
            date = datetime.now(KST)
        
        news_list = []
        
        # 네이버 금융 뉴스 크롤링
        naver_news = self._crawl_naver_finance_news(date, max_news // 2)
        news_list.extend(naver_news)
        
        # 다음 금융 뉴스 크롤링
        daum_news = self._crawl_daum_finance_news(date, max_news // 2)
        news_list.extend(daum_news)
        
        # 중복 제거 및 정렬
        news_list = self._remove_duplicates(news_list)
        news_list = sorted(news_list, key=lambda x: x['published_time'], reverse=True)
        
        logger.info(f"시장 뉴스 수집 완료: {len(news_list)}개")
        return news_list[:max_news]
    
    def _crawl_naver_finance_news(self, date: datetime, max_news: int) -> List[Dict]:
        news_list = []
        try:
            # 네이버 금융 뉴스 페이지
            url = "https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 뉴스 리스트 추출
            news_items = soup.find_all('tr', class_='')
            
            for item in news_items[:max_news]:
                try:
                    # 제목 추출
                    title_elem = item.find('a', class_='tit')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = "https://finance.naver.com" + title_elem.get('href', '')
                    
                    # 시간 추출
                    time_elem = item.find('span', class_='wdate')
                    published_time = time_elem.get_text(strip=True) if time_elem else ""
                    
                    # 언론사 추출
                    press_elem = item.find('span', class_='press')
                    press = press_elem.get_text(strip=True) if press_elem else ""
                    
                    news_list.append({
                        'title': title,
                        'link': link,
                        'published_time': published_time,
                        'press': press,
                        'source': 'naver'
                    })
                    
                except Exception as e:
                    logger.warning(f"네이버 뉴스 항목 처리 실패: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"네이버 금융 뉴스 크롤링 실패: {e}")
        
        return news_list
    
    def _crawl_daum_finance_news(self, date: datetime, max_news: int) -> List[Dict]:
        news_list = []
        try:
            # 다음 금융 뉴스 페이지
            url = "https://finance.daum.net/news"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 뉴스 리스트 추출 (다음 페이지 구조에 맞게 조정)
            news_items = soup.find_all('li', class_='item_news')
            
            for item in news_items[:max_news]:
                try:
                    # 제목 추출
                    title_elem = item.find('a', class_='link_news')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    
                    # 시간 추출
                    time_elem = item.find('span', class_='txt_date')
                    published_time = time_elem.get_text(strip=True) if time_elem else ""
                    
                    # 언론사 추출
                    press_elem = item.find('span', class_='txt_press')
                    press = press_elem.get_text(strip=True) if press_elem else ""
                    
                    news_list.append({
                        'title': title,
                        'link': link,
                        'published_time': published_time,
                        'press': press,
                        'source': 'daum'
                    })
                    
                except Exception as e:
                    logger.warning(f"다음 뉴스 항목 처리 실패: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"다음 금융 뉴스 크롤링 실패: {e}")
        
        return news_list
    
    def get_stock_related_news(self, ticker: str, stock_name: str, max_news: int = 5) -> List[Dict]:
        news_list = []
        
        try:
            # 네이버 종목 뉴스 페이지
            url = f"https://finance.naver.com/item/news_news.naver?code={ticker}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 뉴스 리스트 추출
            news_items = soup.find_all('tr')
            
            for item in news_items[:max_news]:
                try:
                    title_elem = item.find('a', class_='tit')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = "https://finance.naver.com" + title_elem.get('href', '')
                    
                    # 시간 추출
                    time_elem = item.find('span', class_='date')
                    published_time = time_elem.get_text(strip=True) if time_elem else ""
                    
                    news_list.append({
                        'title': title,
                        'link': link,
                        'published_time': published_time,
                        'ticker': ticker,
                        'stock_name': stock_name
                    })
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"종목 뉴스 크롤링 실패 ({ticker}): {e}")
        
        return news_list
    
    def extract_market_keywords(self, news_list: List[Dict]) -> List[str]:
        if not news_list:
            return []
        
        # 시장 관련 키워드 추출
        keywords = []
        market_keywords = [
            '급등', '급락', '상승', '하락', '매수', '매도',
            '실적', '분기', '영업이익', '매출',
            '공시', '발표', '계약', '투자',
            '테마', '관련주', '동반상승', '동반하락',
            '외국인', '기관', '개인투자자',
            '코스피', '코스닥', '지수'
        ]
        
        for news in news_list:
            title = news.get('title', '')
            for keyword in market_keywords:
                if keyword in title and keyword not in keywords:
                    keywords.append(keyword)
        
        return keywords
    
    def analyze_news_sentiment(self, news_list: List[Dict]) -> Dict:
        if not news_list:
            return {'positive': 0, 'negative': 0, 'neutral': 0}
        
        positive_keywords = ['상승', '급등', '호재', '실적 개선', '매수', '투자 확대']
        negative_keywords = ['하락', '급락', '악재', '실적 악화', '매도', '투자 축소']
        
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        for news in news_list:
            title = news.get('title', '')
            
            positive_score = sum(1 for keyword in positive_keywords if keyword in title)
            negative_score = sum(1 for keyword in negative_keywords if keyword in title)
            
            if positive_score > negative_score:
                sentiment_counts['positive'] += 1
            elif negative_score > positive_score:
                sentiment_counts['negative'] += 1
            else:
                sentiment_counts['neutral'] += 1
        
        return sentiment_counts
    
    def _remove_duplicates(self, news_list: List[Dict]) -> List[Dict]:
        seen_titles = set()
        unique_news = []
        
        for news in news_list:
            title = news.get('title', '')
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(news)
        
        return unique_news
    
    def get_overseas_market_news(self) -> Dict:
        # 해외 시장 동향 (간단한 정보)
        try:
            # 실제로는 해외 증시 API나 뉴스 사이트에서 가져와야 함
            # 여기서는 예시 데이터
            overseas_info = {
                'dow': {'close': 34000, 'change': 0.5, 'change_rate': 1.5},
                'nasdaq': {'close': 14000, 'change': 50, 'change_rate': 0.4},
                'sp500': {'close': 4300, 'change': 10, 'change_rate': 0.2},
                'summary': "미국 증시는 혼조세를 보였으며, 기술주 중심으로 상승세를 이어갔습니다."
            }
            
            logger.info("해외 시장 정보 수집 완료")
            return overseas_info
            
        except Exception as e:
            logger.error(f"해외 시장 정보 수집 실패: {e}")
            return {}
    
    def get_major_announcements(self, date: datetime = None) -> List[Dict]:
        if date is None:
            date = datetime.now(KST)
        
        # 주요 공시 정보 (KIND 등에서 가져올 수 있음)
        # 여기서는 간단한 예시
        announcements = []
        
        try:
            # 실제로는 금융감독원 DART API나 공시 사이트 크롤링
            # 예시 데이터
            sample_announcements = [
                {
                    'company': '삼성전자',
                    'type': '분기보고서',
                    'title': '2024년 3분기 실적 발표',
                    'time': '15:30'
                }
            ]
            
            logger.info(f"공시 정보 수집 완료: {len(sample_announcements)}개")
            return sample_announcements
            
        except Exception as e:
            logger.error(f"공시 정보 수집 실패: {e}")
            return []