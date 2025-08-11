from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import sqlite3
import re
import time
import smtplib
import requests
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import gspread
from oauth2client.service_account import ServiceAccountCredentials


print(os.listdir("."))




#-------------------adding to sheets---------------------





def export_to_google_sheets():
    try:
       
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        
       
        c.execute('SELECT date, title, link, site FROM articles ORDER BY site, date DESC')
        data = c.fetchall()
        
       
        sheet = client.open('Automotive Articles').sheet1
        sheet.clear()
        sheet.update('A1', [['Date', 'Title', 'Link', 'Site']] + data)
        
        print(f"✅ Exported {len(data)} articles to Google Sheets")
        
    except Exception as e:
        print(f"❌ Google Sheets export failed: {str(e)}")




# -----------------------Database setup-----------------------------




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




# ------------------------- Scrapers ------------------------- #




def scrape_ather_energy():
    articles = []
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=get_chrome_options())
        driver.get("https://press.atherenergy.com")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.pr-box'))
        )
        boxes = driver.find_elements(By.CSS_SELECTOR, 'div.pr-box')[:5]
        for box in boxes:
            try:
                link_elem = box.find_element(By.TAG_NAME, 'a')
                link = link_elem.get_attribute('href')
            except:
                link = "https://press.atherenergy.com"
            articles.append({
                'date': box.find_element(By.CSS_SELECTOR, 'div.pr-bottom span').text.strip() or 'N/A',
                'title': box.find_element(By.CSS_SELECTOR, 'div.pr-title h4').text.strip() or 'N/A',
                'link': link,
                'site': 'Ather Energy'
            })
    except Exception as e:
        print(f"Ather Energy Error: {str(e)}")
    finally:
        if driver: driver.quit()
    return articles

def scrape_bmw_india():
    articles = []
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=get_chrome_options())
        driver.get("https://www.press.bmwgroup.com/india")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'article.newsfeed'))
        )
        for article in driver.find_elements(By.CSS_SELECTOR, 'article.newsfeed')[:5]:
            try:
                title_elem = article.find_element(By.CSS_SELECTOR, 'div.text h3 a')
                date_elem = article.find_element(By.CSS_SELECTOR, 'div.info span.date')
                articles.append({
                    'date': date_elem.text.strip() or 'N/A',
                    'title': title_elem.text.strip() or 'N/A',
                    'link': title_elem.get_attribute('href') or 'N/A',
                    'site': 'BMW India'
                })
            except Exception:
                continue
    except Exception as e:
        print(f"BMW India Error: {str(e)}")
    finally:
        if driver: driver.quit()
    return articles

def scrape_isuzu_india():
    articles = []
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=get_chrome_options())
        driver.get("https://www.isuzu.in/newsroom.html")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.blognews-box'))
        )
        for card in driver.find_elements(By.CSS_SELECTOR, 'div.blognews-box')[:5]:
            try:
                title = card.find_element(By.TAG_NAME, 'h4').text.strip() or 'N/A'
                img_elem = card.find_element(By.CSS_SELECTOR, 'img.lozad')
                img_src = img_elem.get_attribute('src')
                date_match = re.search(r'/Pressrelease/(\d{2}\.\d{2}\.\d{4})/', img_src)
                articles.append({
                    'date': date_match.group(1) if date_match else 'N/A',
                    'title': title,
                    'link': card.find_element(By.TAG_NAME, 'a').get_attribute('href') or 'N/A',
                    'site': 'Isuzu India'
                })
            except Exception:
                continue
    except Exception as e:
        print(f"Isuzu India Error: {str(e)}")
    finally:
        if driver: driver.quit()
    return articles

def scrape_jeep_india():
    articles = []
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--window-size=1920,1080')
   

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get("https://www.jeep-india.com/press-release.html")

    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        press_releases = []
        containers = driver.find_elements(By.CSS_SELECTOR, 'div[class*="banner"], div[class*="content"], div[class*="grid"]')
        for container in containers:
            try:
                text_content = container.text.strip()
                if text_content and ('READ MORE' in text_content or 'DOWNLOAD PDF' in text_content):
                    lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                    date = ""
                    title = ""
                    link = ""
                    for line in lines:
                        if re.search(r'\w+,?\s+\d{1,2}\s+\w+\s+\d{4}', line):
                            date = line
                            break
                    for line in lines:
                        if line not in ['READ MORE', 'DOWNLOAD PDF'] and not re.search(r'\d{1,2}\s+\w+\s+\d{4}', line) and len(line) > 20:
                            title = line
                            break
                    try:
                        read_more_link = container.find_element(By.XPATH, './/a[contains(text(), "READ MORE")]')
                        link = read_more_link.get_attribute('href')
                    except:
                        try:
                            any_link = container.find_element(By.TAG_NAME, 'a')
                            link = any_link.get_attribute('href')
                        except:
                            link = "No link found"
                    if title and title not in [pr['title'] for pr in press_releases]:
                        press_releases.append({
                            'title': title or 'N/A',
                            'date': date if date else 'N/A',
                            'link': link or 'N/A',
                            'site': 'Jeep India'
                        })
            except:
                continue
        return press_releases[:5]
    finally:
        driver.quit()



def scrape_hero_motocorp():
    articles = []
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--window-size=1920,1080')
    

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get("https://www.heromotocorp.com/en-in/company/newsroom/press-release-news-and-media.html")

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.block--card-container'))
        )
        cards = driver.find_elements(By.CSS_SELECTOR, 'a.block--card-container')

        for card in cards[:5]:
            try:
                lines = [line.strip() for line in card.text.strip().split('\n') if line.strip()]
                if len(lines) >= 3:
                    
                    date = lines[1]
                    title = ' '.join(lines[2:])
                elif len(lines) == 2:
                    date = lines[1]
                    title = ''
                else:
                    date = ''
                    title = ''
                link = card.get_attribute('href')

                if title and date:
                    articles.append({
                        'date': date or 'N/A',
                        'title': title or 'N/A',
                        'link': link or 'N/A',
                        'site': 'Hero Motocorp'
                    })
            except Exception as e:
                print(f"Error extracting card: {e}")

    finally:
        driver.quit()
    return articles


def scrape_harley_davidson():
    articles = []
    BASE_URL = "https://investor.harley-davidson.com"

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--window-size=1920,1080')
    

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get("https://investor.harley-davidson.com/news/default.aspx")

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.module_item'))
        )
        cards = driver.find_elements(By.CSS_SELECTOR, 'div.module_item')
        print(f"Found {len(cards)} press releases")

        for card in cards[:5]:  
            try:
              
                date = card.find_element(By.CSS_SELECTOR, 'div.module_date-time').text.strip()
               
                headline_elem = card.find_element(By.CSS_SELECTOR, 'div.module_headline a')
                title = headline_elem.text.strip()
                link = headline_elem.get_attribute('href')
             
                if link.startswith('/'):
                    link = BASE_URL + link
                articles.append({
                    'date': date or 'N/A',
                    'title': title or 'N/A',
                    'link': link or 'N/A',
                    'site': 'Harley-Davidson'
                })
            except Exception as e:
                print(f"Error extracting card: {e}")

    finally:
        driver.quit()
    return articles



def scrape_mg_motor():
    articles = []
    try:
        response = requests.get('https://www.mgmotor.co.in/content/mgmotor/in/en/media-center/downloads.document.json')
        response.raise_for_status()
        
        for item in response.json():
            try:
                date = item['members'][0]['dateText']
                title = item['title']
                link = item['members'][0]['mediaOriginalUrl']
                
                articles.append({
                    'date': date,
                    'title': title,
                    'link': link,
                    'site': 'MG Motor'
                })
                
            except (KeyError, IndexError):
                continue
                
    except Exception as e:
        print(f"MG Motor scraping error: {str(e)}")
    
    return articles[:5] 

def scrape_tvs_motor():
    articles = []
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=get_chrome_options())
        driver.get("https://www.tvsmotor.com/media/press-release")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.col-xs-5.col-sm-6')))
        cards = driver.find_elements(By.CSS_SELECTOR, 'div.col-xs-5.col-sm-6')
        for card in cards[:5]:
            try:
                link_elem = card.find_element(By.TAG_NAME, 'a')
                link = link_elem.get_attribute('href')
                if link and not link.startswith("http"):
                    link = "https://www.tvsmotor.com" + link
                title = link_elem.text.strip() if link_elem else "N/A"
                articles.append({
                    "date": "N/A",
                    "title": title,
                    "link": link,
                    "site": "TVS Motor"
                })
            except Exception as e:
                continue
    except Exception as e:
        print(f"TVS Motor Error: {str(e)}")
    finally:
        if driver: driver.quit()
    return articles


def create_bajaj_url(title):
    slug = re.sub(r'[^\w\s-]', '', title.lower()).strip()
    slug = re.sub(r'[-\s]+', '-', slug)
    return f"https://www.bajajauto.com/corporate/media-centre/press-releases/{slug}"



def scrape_bajaj_auto():
    articles = []
    try:
        response = requests.get('https://www.bajajauto.com/corporate/media-centre', 
                              headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        for article in soup.find_all('li', class_='list-group-item')[:5]:
            ps = article.find_all('p')
            if len(ps) >= 2:
                articles.append({
                    "date": ps[1].text.strip(),
                    "title": ps[0].text.strip(),
                    "link": create_bajaj_url(ps[0].text.strip()),
                    "site": "Bajaj Auto"
                })
    except Exception as e:
        print(f"Bajaj Auto Error: {str(e)}")
    return articles




def scrape_simple_energy():
    articles = []
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=get_chrome_options())
        driver.get("https://www.simpleenergy.in/media")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.media-card-content'))
        )
        cards = driver.find_elements(By.CSS_SELECTOR, 'div.media-card-content')
        for card in cards[:5]:
            try:
              
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, 'h3.media-card-title')
                    title = title_elem.text.strip()
                except:
                    title = "N/A"
               
                try:
                    date_elem = card.find_element(By.CSS_SELECTOR, 'span.media-card-date')
                    date = date_elem.text.strip()
                except:
                    date = "N/A"
                link = "https://www.simpleenergy.in/media"
                articles.append({
                    'date': date,
                    'title': title,
                    'link': link,
                    'site': 'Simple Energy'
                })
            except Exception as e:
                continue
    except Exception as e:
        print(f"Simple Energy Error: {str(e)}")
    finally:
        if driver: driver.quit()
    return articles





def scrape_benelli():
    articles = []
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=get_chrome_options())
        driver.get("https://www.benelli.com/in-en/news")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a.relative.w-full.cursor-pointer.group.hover\\:no-underline')))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        for article in soup.select('a.relative.w-full.cursor-pointer.group.hover\\:no-underline')[:5]:
        
            date_tag = article.find('span')
            date = date_tag.text.strip() if date_tag else "N/A"
           
            title_tag = article.find('h2') or article.find('div')
            title = title_tag.text.strip() if title_tag else "No title"
            link = "https://www.benelli.com" + article['href']
            articles.append({
                "date": date,
                "title": title,
                "link": link,
                "site": "Benelli"
            })
    except Exception as e:
        print(f"Benelli Error: {str(e)}")
    finally:
        if driver: driver.quit()
    return articles






def scrape_royal_enfield():
    articles = []
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=get_chrome_options())
        driver.get("https://www.royalenfield.com/in/en/our-world/media/press-releases/")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.card-list-comp')))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        for article in soup.find_all('div', class_='card-list-comp')[:5]:
            link_tag = article.find('a')
            articles.append({
                "date": "N/A",
                "title": article.find('div', class_='card-list-comp-txt').text.strip(),
                "link": f"https://www.royalenfield.com{link_tag['href']}" if link_tag else "N/A",
                "site": "Royal Enfield"
            })
    except Exception as e:
        print(f"Royal Enfield Error: {str(e)}")
    finally:
        if driver: driver.quit()
    return articles



def scrape_revolt_motors():
    articles = []
    driver = None
    try:
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get("https://revoltmotors.com/press")

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.press_list_grid'))
        )
        time.sleep(3)
        cards = driver.find_elements(By.CSS_SELECTOR, 'ul.press_list_grid li')
        for i, card in enumerate(cards[:5], 1):
            try:
                a_tag = card.find_element(By.CSS_SELECTOR, 'h5 a')
                title = a_tag.text.strip() if a_tag else "N/A"
                link = a_tag.get_attribute('href') if a_tag else "N/A"
                try:
                    date_elem = card.find_element(By.CSS_SELECTOR, 'div.release_date')
                    date = date_elem.text.strip()
                except:
                    date = "N/A"
                articles.append({
                    'date': date,
                    'title': title,
                    'link': link,
                    'site': 'Revolt Motors'
                })
                print(f"{i}. Date: {date}")
                print(f"   Title: {title}")
                print(f"   Link: {link}\n")
            except Exception as e:
                print(f"Error extracting article {i}: {str(e)}")
                continue
    except Exception as e:
        print(f"Revolt Motors Error: {str(e)}")
    finally:
        if driver:
            driver.quit()
    return articles





# ------------------------- Main Execution -------------------------




if __name__ == "__main__":
    scrapers = [
        scrape_ather_energy,
        scrape_bmw_india,
        scrape_hero_motocorp,
        scrape_isuzu_india,
        scrape_jeep_india,
        scrape_harley_davidson,
        scrape_tvs_motor,
        scrape_bajaj_auto,
        scrape_mg_motor,
        scrape_benelli,
        scrape_simple_energy,
        scrape_royal_enfield,
        scrape_revolt_motors  
    ]
    
    all_articles = []
    for scraper in scrapers:
        try:
            result = scraper()
            print(f"\n{scraper.__name__} found {len(result)} articles")
            for i, art in enumerate(result[:5], 1):
                print(f"{i}. Date: {art['date']}")
                print(f"   Title: {art['title']}")
                print(f"   Link: {art['link']}\n")
            all_articles.extend(result)
        except Exception as e:
            print(f"Error in {scraper.__name__}: {str(e)}")
    
    
    new_articles = []
    for article in all_articles:
        try:
            c.execute('SELECT 1 FROM articles WHERE link = ?', (article['link'],))
            if not c.fetchone():
                new_articles.append(article)
                c.execute('''
                    INSERT INTO articles (date, title, link, site)
                    VALUES (?, ?, ?, ?)
                ''', (
                    article.get('date', 'N/A'),
                    article.get('title', 'N/A'),
                    article.get('link', 'N/A'),
                    article.get('site', 'N/A')
                ))
        except sqlite3.IntegrityError:
            print(f"Duplicate article skipped: {article['link']}")
        except Exception as e:
            print(f"Database Error: {str(e)}")
    conn.commit()
    
    
    if new_articles:
        print(f"\nNew articles found: {len(new_articles)}")
        send_email_notification(new_articles, is_new=True)
    else:
        print("\nNo new articles - sending entire database")
        all_db_articles = fetch_all_articles()
        send_email_notification(all_db_articles, is_new=False)
    
    
    export_to_google_sheets()
    
    conn.close()