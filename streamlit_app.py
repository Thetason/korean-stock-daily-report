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
from src.utils.market_utils import KST, is_trading_day, can_generate_today_report, is_market_closed

# 페이지 설정
st.set_page_config(
    page_title="한국 주식 일일 리포트",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="auto"
)

# CSS 스타일 (모바일 최적화)
st.markdown("""
<style>
    .main {
        padding-top: 1rem;
    }
    
    /* 버튼 스타일 */
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        border: none;
        margin: 0.5rem 0;
        font-size: 16px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    
    /* 제목 크기 조정 */
    h1 {
        color: #2c3e50;
        text-align: center;
        padding-bottom: 1rem;
        font-size: 2rem;
    }
    
    h3 {
        font-size: 1.3rem;
        margin-bottom: 1rem;
    }
    
    /* 리포트 카드 스타일 */
    .report-item {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.75rem;
        margin: 0.75rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #4CAF50;
    }
    
    .report-date {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    
    .report-time {
        font-size: 0.85rem;
        color: #6c757d;
        margin-bottom: 0.75rem;
    }
    
    /* 모바일 전용 스타일 */
    @media (max-width: 768px) {
        .main {
            padding: 0.5rem;
        }
        
        h1 {
            font-size: 1.5rem;
            padding-bottom: 0.5rem;
        }
        
        h3 {
            font-size: 1.1rem;
        }
        
        /* 사이드바를 모바일에서 축소 */
        .css-1d391kg {
            padding-top: 1rem;
        }
        
        /* 버튼 크기 모바일 최적화 */
        .stButton>button {
            padding: 0.6rem 0.8rem;
            font-size: 14px;
        }
        
        /* 리포트 아이템 모바일 최적화 */
        .report-item {
            padding: 0.75rem;
            margin: 0.5rem 0;
        }
        
        .report-date {
            font-size: 1rem;
        }
        
        .report-time {
            font-size: 0.8rem;
        }
        
        /* 열 간격 줄이기 */
        .row-widget {
            gap: 0.5rem;
        }
    }
    
    /* 아주 작은 화면 (iPhone SE 등) */
    @media (max-width: 480px) {
        .main {
            padding: 0.25rem;
        }
        
        h1 {
            font-size: 1.3rem;
        }
        
        .report-item {
            padding: 0.5rem;
        }
        
        .stButton>button {
            padding: 0.5rem;
            font-size: 13px;
        }
    }
</style>
""", unsafe_allow_html=True)

# 제목
st.markdown("# 📈 한국 주식 일일 리포트")
st.markdown("### Korean Stock Daily Report")
st.markdown("---")

# URL 파라미터 확인
query_params = st.query_params

# 세션 상태 초기화
if 'scheduler' not in st.session_state:
    st.session_state.scheduler = DailyScheduler()
if 'generating' not in st.session_state:
    st.session_state.generating = False

# 리포트 페이지 처리
if query_params.get('page') == 'report':
    report_date = query_params.get('date')
    if report_date:
        st.markdown(f"# 📊 {report_date} 주식 리포트")
        
        # 뒤로 가기 버튼
        if st.button("← 메인으로 돌아가기"):
            st.query_params.clear()
            st.rerun()
        
        # 리포트 파일 찾기
        reports_dir = Path('reports')
        report_file = None
        
        # report_date를 YYYYMMDD 형식으로 변환
        date_parts = report_date.split('-')
        if len(date_parts) == 3:
            report_date_raw = ''.join(date_parts)
        else:
            report_date_raw = report_date
        
        # 새 구조 확인 (YYYYMMDD 형식)
        potential_file = reports_dir / f'daily_report_{report_date_raw}.html'
        if potential_file.exists():
            report_file = potential_file
        else:
            # 기존 구조 확인
            potential_file = reports_dir / report_date / f'daily_report_{report_date}.html'
            if potential_file.exists():
                report_file = potential_file
        
        if report_file:
            with open(report_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # HTML 내용을 더 크게 표시
            st.components.v1.html(html_content, height=1200, scrolling=True)
            
            # 다운로드 버튼도 추가
            st.download_button(
                label="📥 HTML 다운로드",
                data=html_content.encode('utf-8'),
                file_name=f"stock_report_{report_date}.html",
                mime="text/html"
            )
        else:
            st.error(f"❌ {report_date} 리포트를 찾을 수 없습니다.")
        
        st.stop()  # 메인 페이지 로드 중단

# 사이드바
with st.sidebar:
    st.markdown("### 🎯 빠른 실행")
    
    # 오늘 리포트 생성 버튼 (16:15 이후에만 활성화)
    today_report_enabled = can_generate_today_report()
    now = datetime.now(KST)
    
    if not today_report_enabled:
        if is_trading_day(now):
            st.warning("⏰ 오늘 리포트는 장 마감 후 16:15 이후에 생성할 수 있습니다.")
        else:
            st.info("📅 오늘은 거래일이 아닙니다.")
    
    if st.button(
        "📊 오늘 리포트 즉시 생성", 
        type="primary", 
        disabled=st.session_state.generating or not today_report_enabled
    ):
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
                    # 생성 전 디렉토리 확인
                    os.makedirs('reports', exist_ok=True)
                    
                    st.session_state.scheduler.generate_daily_report_for_date(selected_datetime)
                    
                    # 생성 후 파일 확인 (여러 경로에서 찾기)
                    reports_dir = Path('reports')
                    generated_files = []
                    
                    # 1. 새 구조: reports/daily_report_YYYY-MM-DD.html
                    new_format_file = reports_dir / f'daily_report_{selected_date}.html'
                    if new_format_file.exists():
                        generated_files.append(new_format_file)
                    
                    # 2. 기존 구조: reports/YYYY-MM-DD/daily_report_YYYY-MM-DD.html
                    old_format_file = reports_dir / str(selected_date) / f'daily_report_{selected_date}.html'
                    if old_format_file.exists():
                        generated_files.append(old_format_file)
                    
                    # 3. 일반적인 검색
                    pattern_files = list(reports_dir.glob(f'*{selected_date}*.html'))
                    generated_files.extend(pattern_files)
                    
                    # 중복 제거
                    generated_files = list(set(generated_files))
                    
                    if generated_files:
                        st.success(f"✅ {selected_date} 리포트가 생성되었습니다!")
                        # st.info(f"생성된 파일: {[str(f) for f in generated_files]}")  # 디버깅 메시지 제거
                    else:
                        # 좀 더 기다린 후 다시 확인
                        import time
                        time.sleep(1)
                        generated_files = list(reports_dir.glob(f'*{selected_date}*.html'))
                        if generated_files:
                            st.success(f"✅ {selected_date} 리포트가 생성되었습니다!")
                        else:
                            st.warning(f"⚠️ 리포트 생성이 완료되었지만 파일 확인에 시간이 걸릴 수 있습니다. 잠시 후 새로고침해주세요.")
                    
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 리포트 생성 실패: {str(e)}")
                    st.error(f"상세 오류: {type(e).__name__}")
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

# 메인 컨텐츠 (모바일에서는 1:1 비율로)
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### 📋 생성된 리포트 목록")
    
    # 리포트 목록 불러기 (새로운 방식)
    reports_dir = Path('reports')
    reports = []
    
    # 디렉토리 구조를 새로 확인
    if reports_dir.exists():
        # 새로운 구조: reports/daily_report_YYYYMMDD.html
        for html_file in reports_dir.glob('daily_report_*.html'):
            date_str_raw = html_file.stem.replace('daily_report_', '')
            # YYYYMMDD를 YYYY-MM-DD로 변환
            if len(date_str_raw) == 8 and date_str_raw.isdigit():
                date_str = f"{date_str_raw[:4]}-{date_str_raw[4:6]}-{date_str_raw[6:8]}"
            else:
                date_str = date_str_raw
            pdf_file = reports_dir / f'daily_report_{date_str_raw}.pdf'
            
            reports.append({
                'date': date_str,
                'html_path': html_file,
                'pdf_path': pdf_file if pdf_file.exists() else None,
                'created_at': datetime.fromtimestamp(html_file.stat().st_mtime)
            })
        
        # 기존 구조도 확인: reports/YYYY-MM-DD/daily_report_YYYY-MM-DD.html
        for date_dir in reports_dir.iterdir():
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
    
    # 중복 제거 및 정렬
    seen_dates = set()
    unique_reports = []
    for report in sorted(reports, key=lambda x: x['created_at'], reverse=True):
        if report['date'] not in seen_dates:
            unique_reports.append(report)
            seen_dates.add(report['date'])
    reports = unique_reports
    
    if reports:
        for i, report in enumerate(reports[:10]):  # 최근 10개만 표시
            # 모바일 최적화된 카드 형태
            st.markdown(f"""
            <div class="report-item">
                <div class="report-date">📅 {report['date']}</div>
                <div class="report-time">생성: {report['created_at'].strftime('%m/%d %H:%M')}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 모바일 친화적 버튼 배치 (항상 세로 배치)
            report_url = f"?page=report&date={report['date']}"
            
            # 큰 보기 버튼
            st.markdown(f"""
            <div style="margin-bottom: 10px;">
                <a href="{report_url}" target="_blank" style="text-decoration: none;">
                    <button style="
                        background: linear-gradient(135deg, #34c759, #28a745);
                        color: white;
                        border: none;
                        padding: 14px 20px;
                        border-radius: 12px;
                        cursor: pointer;
                        font-size: 16px;
                        width: 100%;
                        font-weight: bold;
                        box-shadow: 0 3px 10px rgba(52, 199, 89, 0.3);
                        transition: all 0.3s ease;
                    " onmouseover="this.style.transform='translateY(-2px)'" 
                       onmouseout="this.style.transform='translateY(0)'">
                        👁️ 리포트 보기
                    </button>
                </a>
            </div>
            """, unsafe_allow_html=True)
            
            # 다운로드 버튼
            with open(report['html_path'], 'rb') as f:
                st.download_button(
                    label="📥 HTML 다운로드",
                    data=f.read(),
                    file_name=f"stock_report_{report['date']}.html",
                    mime="text/html",
                    key=f"download_{report['date']}",
                    use_container_width=True
                )
            
            if i < len(reports) - 1:  # 마지막이 아니면 구분선
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
        st.markdown(f"**자동 실행 시간:** {config.get('scheduler', {}).get('run_time', '16:15')}")
        
        # 현재 시간과 다음 실행 시간 표시
        now = datetime.now(KST)
        if is_trading_day(now) and not is_market_closed(now):
            st.markdown("**장 상태:** 🟢 거래 중")
            st.markdown("**다음 리포트:** 16:15 예정")
        elif is_trading_day(now) and is_market_closed(now):
            st.markdown("**장 상태:** 🔴 마감")
            st.markdown("**오늘 리포트:** 생성 가능")
        else:
            st.markdown("**장 상태:** 📅 휴장일")
        
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