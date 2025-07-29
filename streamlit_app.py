#!/usr/bin/env python3
"""
Korean Stock Daily Report - Streamlit Web App
사용자가 가장 쉽게 사용할 수 있는 웹 인터페이스
"""

import streamlit as st
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path
import time

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scheduler.daily_scheduler import DailyScheduler
from src.utils.market_utils import KST, is_trading_day

# 페이지 설정
st.set_page_config(
    page_title="한국 주식 일일 리포트",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        border: none;
        margin: 0.5rem 0;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .report-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    h1 {
        color: #2c3e50;
        text-align: center;
        padding-bottom: 2rem;
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        color: #155724;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 제목
st.markdown("# 📈 한국 주식 일일 리포트")
st.markdown("### Korean Stock Daily Report")
st.markdown("---")

# 세션 상태 초기화
if 'scheduler' not in st.session_state:
    st.session_state.scheduler = DailyScheduler()
if 'generating' not in st.session_state:
    st.session_state.generating = False

# 사이드바
with st.sidebar:
    st.markdown("### 🎯 빠른 실행")
    
    # 오늘 리포트 생성 버튼
    if st.button("📊 오늘 리포트 즉시 생성", type="primary", disabled=st.session_state.generating):
        st.session_state.generating = True
        with st.spinner("리포트를 생성하고 있습니다... (약 1-2분 소요)"):
            try:
                st.session_state.scheduler.generate_daily_report()
                st.success("✅ 오늘 리포트가 생성되었습니다!")
                st.balloons()
                time.sleep(2)
                st.rerun()
            except Exception as e:
                st.error(f"❌ 리포트 생성 실패: {str(e)}")
            finally:
                st.session_state.generating = False
    
    st.markdown("---")
    
    # 날짜 선택
    st.markdown("### 📅 특정 날짜 리포트")
    
    # 최근 거래일 표시
    trading_days = []
    today = datetime.now(KST)
    for i in range(30):
        date = today - timedelta(days=i)
        if is_trading_day(date):
            trading_days.append(date.date())
            if len(trading_days) >= 10:
                break
    
    selected_date = st.date_input(
        "날짜 선택",
        value=trading_days[0] if trading_days else today.date(),
        max_value=today.date(),
        help="거래일만 선택 가능합니다"
    )
    
    if st.button("🔍 선택한 날짜 리포트 생성", disabled=st.session_state.generating):
        selected_datetime = KST.localize(datetime.combine(selected_date, datetime.min.time()))
        
        if not is_trading_day(selected_datetime):
            st.error("❌ 선택한 날짜는 거래일이 아닙니다.")
        else:
            st.session_state.generating = True
            with st.spinner(f"{selected_date} 리포트를 생성하고 있습니다..."):
                try:
                    st.session_state.scheduler.generate_daily_report_for_date(selected_datetime)
                    st.success(f"✅ {selected_date} 리포트가 생성되었습니다!")
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 리포트 생성 실패: {str(e)}")
                finally:
                    st.session_state.generating = False
    
    st.markdown("---")
    st.markdown("### ℹ️ 정보")
    st.info("""
    **사용법**
    1. '오늘 리포트 즉시 생성' 클릭
    2. 1-2분 기다리기
    3. 생성된 리포트 확인
    
    **포함 내용**
    - KOSPI/KOSDAQ 지수
    - 급등/급락 종목
    - 투자자별 매매동향
    - 주요 뉴스
    """)

# 메인 컨텐츠
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📋 생성된 리포트 목록")
    
    # 리포트 목록 불러오기
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
                        'html_path': html_file,
                        'pdf_path': pdf_file if pdf_file.exists() else None,
                        'created_at': datetime.fromtimestamp(html_file.stat().st_mtime)
                    })
    
    if reports:
        for report in reports[:10]:  # 최근 10개만 표시
            with st.container():
                col_date, col_actions = st.columns([3, 2])
                
                with col_date:
                    st.markdown(f"### 📅 {report['date']}")
                    st.caption(f"생성 시간: {report['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                
                with col_actions:
                    col_view, col_download = st.columns(2)
                    
                    with col_view:
                        if st.button(f"👁️ 보기", key=f"view_{report['date']}"):
                            with open(report['html_path'], 'r', encoding='utf-8') as f:
                                html_content = f.read()
                            st.components.v1.html(html_content, height=800, scrolling=True)
                    
                    with col_download:
                        with open(report['html_path'], 'rb') as f:
                            st.download_button(
                                label="📥 다운로드",
                                data=f.read(),
                                file_name=f"stock_report_{report['date']}.html",
                                mime="text/html",
                                key=f"download_{report['date']}"
                            )
                
                st.markdown("---")
    else:
        st.info("📭 아직 생성된 리포트가 없습니다. 위의 버튼을 눌러 리포트를 생성해주세요!")

with col2:
    st.markdown("### 📊 최근 거래일")
    
    # 최근 거래일 캘린더 표시
    st.markdown("**최근 10 거래일:**")
    for i, trading_day in enumerate(trading_days[:10]):
        if i == 0:
            st.markdown(f"- **{trading_day} (오늘)**")
        else:
            st.markdown(f"- {trading_day}")
    
    st.markdown("---")
    
    # 시스템 상태
    st.markdown("### 🔧 시스템 상태")
    
    config_path = Path('config/config.json')
    if config_path.exists():
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        st.success("✅ 시스템 정상 작동 중")
        st.markdown(f"**자동 실행 시간:** {config.get('scheduler', {}).get('run_time', '16:00')}")
        st.markdown(f"**급등 기준:** {config.get('analysis', {}).get('surge_threshold', 5)}%")
        st.markdown(f"**급락 기준:** {config.get('analysis', {}).get('plunge_threshold', -5)}%")
    else:
        st.warning("⚠️ 설정 파일을 찾을 수 없습니다")

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Korean Stock Daily Report System</p>
    <p>문의사항이나 오류 발생 시 관리자에게 연락해주세요</p>
</div>
""", unsafe_allow_html=True)