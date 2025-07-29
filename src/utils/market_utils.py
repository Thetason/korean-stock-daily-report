from datetime import datetime, timedelta
import pytz
from typing import List, Tuple
import pandas as pd

KST = pytz.timezone('Asia/Seoul')

def is_trading_day(date: datetime = None) -> bool:
    if date is None:
        date = datetime.now(KST)
    
    if date.weekday() >= 5:  # 토요일(5) 또는 일요일(6)
        return False
    
    # 한국 공휴일 리스트 (2024년 기준, 필요시 업데이트)
    holidays = [
        datetime(2024, 1, 1),   # 신정
        datetime(2024, 2, 9),   # 설날 연휴
        datetime(2024, 2, 10),  # 설날
        datetime(2024, 2, 11),  # 설날 연휴
        datetime(2024, 2, 12),  # 대체공휴일
        datetime(2024, 3, 1),   # 삼일절
        datetime(2024, 5, 15),  # 부처님오신날
        datetime(2024, 6, 6),   # 현충일
        datetime(2024, 8, 15),  # 광복절
        datetime(2024, 9, 16),  # 추석 연휴
        datetime(2024, 9, 17),  # 추석
        datetime(2024, 9, 18),  # 추석 연휴
        datetime(2024, 10, 3),  # 개천절
        datetime(2024, 10, 9),  # 한글날
        datetime(2024, 12, 25), # 크리스마스
    ]
    
    date_only = date.date()
    for holiday in holidays:
        if holiday.date() == date_only:
            return False
    
    return True

def get_trading_hours() -> List[str]:
    return ["09:30", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "15:30"]

def get_previous_trading_day(date: datetime = None) -> datetime:
    if date is None:
        date = datetime.now(KST)
    
    previous_day = date - timedelta(days=1)
    while not is_trading_day(previous_day):
        previous_day -= timedelta(days=1)
    
    return previous_day

def format_price(price: float) -> str:
    return f"{price:,.0f}"

def format_change_rate(rate: float) -> str:
    sign = "+" if rate > 0 else ""
    return f"{sign}{rate:.2f}%"

def calculate_change_rate(current: float, previous: float) -> float:
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100