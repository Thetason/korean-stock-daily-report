from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import os
import json
from typing import Dict, List, Any
import logging
from ..utils.market_utils import KST, format_price, format_change_rate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self, template_dir: str = "templates", output_dir: str = "reports"):
        self.template_dir = template_dir
        self.output_dir = output_dir
        
        # Jinja2 환경 설정
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            extensions=['jinja2.ext.do']
        )
        
        # 커스텀 필터 등록
        self.env.filters['format_price'] = self._format_price
        self.env.filters['format_change_rate'] = self._format_change_rate
        self.env.filters['format_volume'] = self._format_volume
        
        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_daily_report(self, data: Dict[str, Any], date: datetime = None) -> str:
        if date is None:
            date = datetime.now(KST)
        
        try:
            # 템플릿 로드
            template = self.env.get_template('daily_report.html')
            
            # 보고서 데이터 준비
            report_data = self._prepare_report_data(data, date)
            
            # HTML 렌더링
            html_content = template.render(**report_data)
            
            # 파일명 생성
            date_str = date.strftime('%Y%m%d')
            html_filename = f"daily_report_{date_str}.html"
            html_path = os.path.join(self.output_dir, html_filename)
            
            # HTML 파일 저장
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"일일 보고서 생성 완료: {html_path}")
            return html_path
            
        except Exception as e:
            logger.error(f"보고서 생성 실패: {e}")
            raise
    
    def generate_pdf_report(self, html_path: str) -> str:
        try:
            # weasyprint가 제대로 설치되지 않은 경우를 대비한 처리
            try:
                import weasyprint
                pdf_path = html_path.replace('.html', '.pdf')
                weasyprint.HTML(filename=html_path).write_pdf(pdf_path)
                logger.info(f"PDF 보고서 생성 완료: {pdf_path}")
                return pdf_path
            except ImportError:
                logger.warning("WeasyPrint를 찾을 수 없습니다. PDF 생성을 건너뜁니다.")
                return ""
            except Exception as e:
                logger.warning(f"PDF 생성 실패, HTML만 사용: {e}")
                return ""
            
        except Exception as e:
            logger.error(f"PDF 생성 실패: {e}")
            return ""
    
    def _prepare_report_data(self, data: Dict[str, Any], date: datetime) -> Dict[str, Any]:
        # 한국어 날짜 형식
        weekdays = ['월', '화', '수', '목', '금', '토', '일']
        korean_date = f"{date.year}년 {date.month}월 {date.day}일 ({weekdays[date.weekday()]}요일)"
        
        # 시간대별 데이터 준비
        hourly_data = self._prepare_hourly_data(data.get('investor_data', {}))
        
        # 시장 분석 텍스트 생성
        market_analysis = self._generate_market_analysis(data)
        
        # 시황 하이라이트 생성
        market_highlights = self._generate_market_highlights(data)
        
        # 숙제 생성
        homework = self._generate_homework(data)
        
        return {
            'report_date': date.strftime('%Y-%m-%d'),
            'report_date_korean': korean_date,
            'generation_time': datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S'),
            'market_data': data.get('market_data', {}),
            'hourly_data': hourly_data,
            'market_analysis': market_analysis,
            'market_highlights': market_highlights,
            'surge_stocks': data.get('surge_stocks', []),
            'plunge_stocks': data.get('plunge_stocks', []),
            'themes': data.get('themes', []),
            'homework': homework
        }
    
    def _prepare_hourly_data(self, investor_data: Dict) -> List[Dict]:
        time_slots = ["09:30", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "15:30"]
        hourly_data = []
        
        hourly_investor = investor_data.get('hourly', {})
        
        for time_slot in time_slots:
            slot_data = hourly_investor.get(time_slot, {})
            kospi_data = slot_data.get('kospi', {})
            kosdaq_data = slot_data.get('kosdaq', {})
            
            # 실제 시간대별 지수 변화율 사용
            kospi_change = slot_data.get('kospi_change', 0)
            kosdaq_change = slot_data.get('kosdaq_change', 0)
            
            hourly_data.append({
                'time': time_slot,
                'kospi_change': kospi_change,
                'kosdaq_change': kosdaq_change,
                'individual': kospi_data.get('개인', 0),
                'foreign': kospi_data.get('외국인', 0),
                'institution': kospi_data.get('기관계', 0),
                'financial': kospi_data.get('금융투자', 0),
                'investment': kospi_data.get('투신', 0),
                'pension': kospi_data.get('연기금', 0)
            })
        
        return hourly_data
    
    def _generate_market_analysis(self, data: Dict) -> Dict:
        market_data = data.get('market_data', {})
        overseas_data = data.get('overseas_data', {})
        
        # 전일 해외 시장 동향
        overseas_summary = overseas_data.get('summary', '전일 미국 증시는 혼조세를 보였습니다.')
        
        # 당일 시장 분석
        kospi_change = market_data.get('kospi', {}).get('change_rate', 0)
        kosdaq_change = market_data.get('kosdaq', {}).get('change_rate', 0)
        
        if kospi_change > 0 and kosdaq_change > 0:
            market_trend = "상승세"
        elif kospi_change < 0 and kosdaq_change < 0:
            market_trend = "하락세"
        else:
            market_trend = "혼조세"
        
        analysis_text = f"""
        {overseas_summary}
        
        국내 증시는 {market_trend}로 출발하여 {market_trend}로 마감했습니다. 
        KOSPI는 전일 대비 {format_change_rate(kospi_change)}, 
        KOSDAQ은 {format_change_rate(kosdaq_change)}를 기록했습니다.
        
        투자주체별로는 {"개인투자자가 순매수세를 보인 반면, 외국인과 기관은 매도 우위를 보였습니다." if kospi_change > 0 else "외국인과 기관의 매도세가 지속되면서 지수 하락을 이끌었습니다."}
        """.strip()
        
        return {
            'summary': analysis_text
        }
    
    def _generate_market_highlights(self, data: Dict) -> List[str]:
        highlights = []
        
        # 테마 기반 하이라이트
        themes = data.get('themes', [])
        if themes:
            for theme in themes[:5]:  # 상위 5개 테마
                highlights.append(f"{theme['theme']} 관련주들이 {theme['avg_change_rate']:.1f}% 상승하며 주목받았습니다.")
        
        # 급등/급락 종목 기반 하이라이트
        surge_stocks = data.get('surge_stocks', [])
        if surge_stocks:
            top_surge = surge_stocks[0]
            highlights.append(f"{top_surge['name']}이 {top_surge['change_rate']:.1f}% 급등하며 상승률 1위를 기록했습니다.")
        
        plunge_stocks = data.get('plunge_stocks', [])
        if plunge_stocks:
            top_plunge = plunge_stocks[0]
            highlights.append(f"{top_plunge['name']}은 {abs(top_plunge['change_rate']):.1f}% 급락했습니다.")
        
        # 기본 하이라이트 (데이터가 부족한 경우)
        if not highlights:
            highlights = [
                "개별 종목들의 혼조세가 지속되었습니다.",
                "거래량은 평소 수준을 유지했습니다.",
                "특별한 테마주 움직임은 관찰되지 않았습니다."
            ]
        
        return highlights
    
    def _generate_homework(self, data: Dict) -> List[str]:
        homework = []
        
        # 다음날 주목 사항 생성
        themes = data.get('themes', [])
        if themes:
            homework.append(f"{themes[0]['theme']} 관련주들의 추가 상승 여부 확인")
        
        market_data = data.get('market_data', {})
        kospi_change = market_data.get('kospi', {}).get('change_rate', 0)
        
        if abs(kospi_change) > 1:
            if kospi_change > 0:
                homework.append("상승 모멘텀 지속 가능성 점검")
            else:
                homework.append("추가 하락 위험 모니터링")
        
        # 기본 숙제가 없는 경우
        if not homework:
            return []
        
        return homework
    
    def _format_price(self, price: float) -> str:
        if price == 0:
            return "0"
        return f"{price:,.0f}"
    
    def _format_change_rate(self, rate: float) -> str:
        if rate == 0:
            return "0.00%"
        sign = "+" if rate > 0 else ""
        return f"{sign}{rate:.2f}%"
    
    def _format_volume(self, volume: int) -> str:
        if volume == 0:
            return "0"
        if volume >= 100000000:  # 1억 이상
            return f"{volume/100000000:.1f}억"
        elif volume >= 10000:  # 1만 이상
            return f"{volume/10000:.0f}만"
        else:
            return f"{volume:,}"
    
    def save_report_data(self, data: Dict, date: datetime = None) -> str:
        if date is None:
            date = datetime.now(KST)
        
        date_str = date.strftime('%Y%m%d')
        json_filename = f"report_data_{date_str}.json"
        json_path = os.path.join(self.output_dir, json_filename)
        
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"보고서 데이터 저장 완료: {json_path}")
            return json_path
            
        except Exception as e:
            logger.error(f"보고서 데이터 저장 실패: {e}")
            raise