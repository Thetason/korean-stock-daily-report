import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime
from typing import List, Optional
import logging
from ..utils.market_utils import KST

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
    
    def send_daily_report(self, 
                         sender_email: str,
                         sender_password: str,
                         recipients: List[str],
                         html_path: str,
                         pdf_path: Optional[str] = None,
                         date: datetime = None) -> bool:
        
        if date is None:
            date = datetime.now(KST)
        
        try:
            # 이메일 메시지 생성
            message = self._create_message(sender_email, recipients, html_path, pdf_path, date)
            
            # SMTP 서버 연결 및 발송
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(sender_email, sender_password)
                
                # 각 수신자에게 개별 발송
                for recipient in recipients:
                    individual_message = message.copy()
                    individual_message["To"] = recipient
                    text = individual_message.as_string()
                    server.sendmail(sender_email, recipient, text)
                    logger.info(f"이메일 발송 완료: {recipient}")
            
            logger.info(f"총 {len(recipients)}명에게 이메일 발송 완료")
            return True
            
        except Exception as e:
            logger.error(f"이메일 발송 실패: {e}")
            return False
    
    def _create_message(self, 
                       sender_email: str,
                       recipients: List[str],
                       html_path: str,
                       pdf_path: Optional[str],
                       date: datetime) -> MIMEMultipart:
        
        # 멀티파트 메시지 생성
        message = MIMEMultipart("alternative")
        
        # 메시지 헤더 설정
        date_str = date.strftime('%Y년 %m월 %d일')
        message["Subject"] = f"대박노트 데일리 메일 - {date_str}"
        message["From"] = sender_email
        message["To"] = ", ".join(recipients)
        
        # HTML 본문 읽기
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except Exception as e:
            logger.error(f"HTML 파일 읽기 실패: {e}")
            html_content = self._create_fallback_html(date)
        
        # 텍스트 버전 생성 (간단한 요약)
        text_content = self._create_text_summary(date)
        
        # MIME 파트 생성
        text_part = MIMEText(text_content, "plain", "utf-8")
        html_part = MIMEText(html_content, "html", "utf-8")
        
        # 메시지에 파트 추가
        message.attach(text_part)
        message.attach(html_part)
        
        # PDF 첨부 (선택사항)
        if pdf_path and os.path.exists(pdf_path):
            try:
                with open(pdf_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= "daily_report_{date.strftime("%Y%m%d")}.pdf"',
                )
                
                message.attach(part)
                logger.info("PDF 첨부 완료")
                
            except Exception as e:
                logger.warning(f"PDF 첨부 실패: {e}")
        
        return message
    
    def _create_text_summary(self, date: datetime) -> str:
        """이메일 텍스트 버전 (HTML을 볼 수 없는 경우)"""
        date_str = date.strftime('%Y년 %m월 %d일')
        
        text_content = f"""
대박노트 데일리 메일 - {date_str}

안녕하세요!
오늘의 한국 주식시장 분석 보고서를 보내드립니다.

📊 시장 요약:
- 상세한 시장 분석은 첨부된 HTML 보고서를 확인해주세요.
- 급등/급락 종목 정보가 포함되어 있습니다.
- 오늘의 주요 테마와 투자 포인트를 제공합니다.

📎 첨부 파일:
- HTML 보고서 (이메일 본문)
- PDF 보고서 (첨부 파일)

투자에 참고하시기 바라며, 항상 신중한 투자 결정을 내리시기 바랍니다.

※ 본 보고서는 공개된 시장 데이터를 기반으로 자동 생성되었으며, 
   투자 판단의 참고용으로만 활용하시기 바랍니다.

생성 시간: {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        return text_content
    
    def _create_fallback_html(self, date: datetime) -> str:
        """HTML 파일을 읽을 수 없는 경우의 대체 HTML"""
        date_str = date.strftime('%Y년 %m월 %d일')
        
        fallback_html = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <title>대박노트 데일리 메일 - {date_str}</title>
            <style>
                body {{ font-family: 'Malgun Gothic', sans-serif; margin: 20px; }}
                .header {{ text-align: center; color: #2c3e50; margin-bottom: 30px; }}
                .content {{ background-color: #f8f9fa; padding: 20px; border-radius: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>대박노트 데일리 메일</h1>
                <h2>{date_str}</h2>
            </div>
            <div class="content">
                <p>죄송합니다. 보고서 생성 중 문제가 발생했습니다.</p>
                <p>자세한 내용은 첨부된 PDF 파일을 확인해주세요.</p>
                <p>문의사항이 있으시면 관리자에게 연락해주세요.</p>
            </div>
        </body>
        </html>
        """
        
        return fallback_html
    
    def test_connection(self, sender_email: str, sender_password: str) -> bool:
        """SMTP 서버 연결 테스트"""
        try:
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(sender_email, sender_password)
                logger.info("SMTP 서버 연결 테스트 성공")
                return True
                
        except Exception as e:
            logger.error(f"SMTP 서버 연결 테스트 실패: {e}")
            return False
    
    def send_test_email(self, 
                       sender_email: str,
                       sender_password: str,
                       test_recipient: str) -> bool:
        """테스트 이메일 발송"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = "대박노트 데일리 메일 - 테스트"
            message["From"] = sender_email
            message["To"] = test_recipient
            
            text_content = """
            대박노트 데일리 메일 시스템 테스트
            
            이 메일은 시스템 테스트용입니다.
            정상적으로 수신되었다면 설정이 완료된 것입니다.
            """
            
            html_content = """
            <html>
            <body>
                <h2>대박노트 데일리 메일 시스템 테스트</h2>
                <p>이 메일은 시스템 테스트용입니다.</p>
                <p>정상적으로 수신되었다면 설정이 완료된 것입니다.</p>
            </body>
            </html>
            """
            
            text_part = MIMEText(text_content, "plain", "utf-8")
            html_part = MIMEText(html_content, "html", "utf-8")
            
            message.attach(text_part)
            message.attach(html_part)
            
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, test_recipient, message.as_string())
            
            logger.info(f"테스트 이메일 발송 완료: {test_recipient}")
            return True
            
        except Exception as e:
            logger.error(f"테스트 이메일 발송 실패: {e}")
            return False