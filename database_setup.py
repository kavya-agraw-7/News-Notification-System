import sqlite3                              
import smtplib                                 
from selenium.webdriver.chrome.options import Options 
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText           

conn = sqlite3.connect('automotive_articles.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        title TEXT,
        link TEXT UNIQUE,
        site TEXT
    )
''')
conn.commit()

def get_chrome_options():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    return options

def fetch_all_articles():
    c.execute('SELECT site, date, title, link FROM articles ORDER BY site, date DESC')
    rows = c.fetchall()
    articles = []
    for row in rows:
        articles.append({
            'site': row[0] or 'N/A',
            'date': row[1] or 'N/A',
            'title': row[2] or 'N/A',
            'link': row[3] or 'N/A'
        })
    return articles

def articles_to_html_table(articles):
    html = """
    <table border="1" cellpadding="5" style="border-collapse: collapse; width: 100%;">
        <tr>
            <th>Site</th>
            <th>Date</th>
            <th>Title</th>
            <th>Link</th>
        </tr>
    """
    for a in articles:
        html += f"""
        <tr>
            <td>{a.get('site', 'N/A')}</td>
            <td>{a.get('date', 'N/A')}</td>
            <td>{a.get('title', 'N/A')}</td>
            <td><a href="{a.get('link', 'N/A')}">View</a></td>
        </tr>
        """
    html += "</table>"
    return html

def send_email_notification(articles,is_new=True):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_ADDRESS = "kavya.agrawal@collegedunia.com"
    EMAIL_PASSWORD = 'xmbi bdob ltvs lbvz'
    RECIPIENT_EMAIL = "kavya.agrawal@collegedunia.com"
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = "NEW Automotive Press Releases" if is_new else "Full Automotive Press Releases Database"
    html_content = f"""
    <html>
        <body>
            <h2>Press Release Update: {len(articles)} Articles</h2>
            {articles_to_html_table(articles)}
        </body>
    </html>
    """
    msg.attach(MIMEText(html_content, 'html'))
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        print("Email notification sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")

