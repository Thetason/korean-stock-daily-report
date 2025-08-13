import yfinance as yf
import pykrx.stock as pykrx_stock
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from ..utils.market_utils import KST, get_previous_trading_day, is_trading_day

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockDataCollector:
    def __init__(self):
        self.kospi_ticker = "^KS11"
        self.kosdaq_ticker = "^KQ11"
    
    def get_index_data(self, date: datetime = None) -> Dict:
        if date is None:
            date = datetime.now(KST)
            
        if not is_trading_day(date):
            date = get_previous_trading_day(date)
        
        date_str = date.strftime('%Y%m%d')
        previous_date = get_previous_trading_day(date)
        previous_date_str = previous_date.strftime('%Y%m%d')
        
        try:
            # KOSPI 데이터
            kospi_data = stock.get_index_ohlcv(date_str, date_str, "1001")
            kospi_prev = stock.get_index_ohlcv(previous_date_str, previous_date_str, "1001")
            
            # KOSDAQ 데이터  
            kosdaq_data = stock.get_index_ohlcv(date_str, date_str, "2001")
            kosdaq_prev = stock.get_index_ohlcv(previous_date_str, previous_date_str, "2001")
            
            result = {
                'date': date.strftime('%Y-%m-%d'),
                'kospi': {
                    'current': float(kospi_data['종가'].iloc[0]) if not kospi_data.empty else 0,
                    'previous': float(kospi_prev['종가'].iloc[0]) if not kospi_prev.empty else 0,
                    'change_rate': 0
                },
                'kosdaq': {
                    'current': float(kosdaq_data['종가'].iloc[0]) if not kosdaq_data.empty else 0,
                    'previous': float(kosdaq_prev['종가'].iloc[0]) if not kosdaq_prev.empty else 0,
                    'change_rate': 0
                }
            }
            
            # 등락률 계산
            if result['kospi']['previous'] > 0:
                result['kospi']['change_rate'] = ((result['kospi']['current'] - result['kospi']['previous']) / result['kospi']['previous']) * 100
            
            if result['kosdaq']['previous'] > 0:
                result['kosdaq']['change_rate'] = ((result['kosdaq']['current'] - result['kosdaq']['previous']) / result['kosdaq']['previous']) * 100
            
            logger.info(f"지수 데이터 수집 완료: KOSPI {result['kospi']['current']:.2f}, KOSDAQ {result['kosdaq']['current']:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"지수 데이터 수집 실패: {e}")
            return self._get_fallback_index_data(date)
    
    def _get_fallback_index_data(self, date: datetime) -> Dict:
        try:
            # yfinance를 이용한 대체 데이터 수집
            kospi = yf.Ticker(self.kospi_ticker)
            kosdaq = yf.Ticker(self.kosdaq_ticker)
            
            # 2일치 데이터 가져오기
            end_date = date + timedelta(days=1)
            start_date = date - timedelta(days=5)  # 주말 고려하여 여유있게
            
            kospi_hist = kospi.history(start=start_date, end=end_date)
            kosdaq_hist = kosdaq.history(start=start_date, end=end_date)
            
            if len(kospi_hist) >= 2 and len(kosdaq_hist) >= 2:
                kospi_current = kospi_hist['Close'].iloc[-1]
                kospi_previous = kospi_hist['Close'].iloc[-2]
                kosdaq_current = kosdaq_hist['Close'].iloc[-1]
                kosdaq_previous = kosdaq_hist['Close'].iloc[-2]
                
                return {
                    'date': date.strftime('%Y-%m-%d'),
                    'kospi': {
                        'current': float(kospi_current),
                        'previous': float(kospi_previous),
                        'change_rate': ((kospi_current - kospi_previous) / kospi_previous) * 100
                    },
                    'kosdaq': {
                        'current': float(kosdaq_current),
                        'previous': float(kosdaq_previous),
                        'change_rate': ((kosdaq_current - kosdaq_previous) / kosdaq_previous) * 100
                    }
                }
        except Exception as e:
            logger.error(f"대체 지수 데이터 수집도 실패: {e}")
        
        return {
            'date': date.strftime('%Y-%m-%d'),
            'kospi': {'current': 0, 'previous': 0, 'change_rate': 0},
            'kosdaq': {'current': 0, 'previous': 0, 'change_rate': 0}
        }
    
    def get_stock_list(self, market: str = "ALL") -> List[str]:
        try:
            if market == "KOSPI":
                tickers = stock.get_market_ticker_list(market="KOSPI")
            elif market == "KOSDAQ":
                tickers = stock.get_market_ticker_list(market="KOSDAQ")
            else:
                kospi_tickers = stock.get_market_ticker_list(market="KOSPI")
                kosdaq_tickers = stock.get_market_ticker_list(market="KOSDAQ")
                tickers = kospi_tickers + kosdaq_tickers
            
            logger.info(f"{market} 종목 리스트 수집 완료: {len(tickers)}개")
            return tickers
        except Exception as e:
            logger.error(f"종목 리스트 수집 실패: {e}")
            return []
    
    def get_stock_data(self, tickers: List[str], date: datetime = None) -> pd.DataFrame:
        if date is None:
            date = datetime.now(KST)
            
        if not is_trading_day(date):
            date = get_previous_trading_day(date)
            
        date_str = date.strftime('%Y%m%d')
        previous_date = get_previous_trading_day(date)
        previous_date_str = previous_date.strftime('%Y%m%d')
        
        try:
            # 당일 주가 데이터
            current_data = stock.get_market_ohlcv(date_str, market="ALL")
            # 전일 주가 데이터
            previous_data = stock.get_market_ohlcv(previous_date_str, market="ALL")
            
            # 종목명 정보
            stock_names = {}
            for ticker in tickers:
                try:
                    name = stock.get_market_ticker_name(ticker)
                    stock_names[ticker] = name
                except:
                    stock_names[ticker] = ticker
            
            # 데이터 병합 및 계산
            result_data = []
            for ticker in tickers:
                try:
                    current_price = current_data.loc[ticker, '종가'] if ticker in current_data.index else 0
                    previous_price = previous_data.loc[ticker, '종가'] if ticker in previous_data.index else 0
                    volume = current_data.loc[ticker, '거래량'] if ticker in current_data.index else 0
                    
                    if previous_price > 0:
                        change_rate = ((current_price - previous_price) / previous_price) * 100
                    else:
                        change_rate = 0
                    
                    result_data.append({
                        'ticker': ticker,
                        'name': stock_names.get(ticker, ticker),
                        'current_price': current_price,
                        'previous_price': previous_price,
                        'change_rate': change_rate,
                        'volume': volume
                    })
                except Exception as e:
                    logger.warning(f"종목 {ticker} 데이터 처리 실패: {e}")
                    continue
            
            df = pd.DataFrame(result_data)
            logger.info(f"주식 데이터 수집 완료: {len(df)}개 종목")
            return df
            
        except Exception as e:
            logger.error(f"주식 데이터 수집 실패: {e}")
            return pd.DataFrame()
    
    def get_sector_data(self, date: datetime = None) -> Dict:
        if date is None:
            date = datetime.now(KST)
            
        date_str = date.strftime('%Y%m%d')
        
        try:
            # 업종별 지수 데이터
            sector_data = stock.get_index_ohlcv_by_date(date_str, date_str)
            
            sectors = {}
            for idx, row in sector_data.iterrows():
                sector_name = stock.get_index_ticker_name(str(idx))
                sectors[sector_name] = {
                    'close': row['종가'],
                    'change': row['등락률']
                }
            
            logger.info(f"섹터 데이터 수집 완료: {len(sectors)}개 섹터")
            return sectors
            
        except Exception as e:
            logger.error(f"섹터 데이터 수집 실패: {e}")
            return {}