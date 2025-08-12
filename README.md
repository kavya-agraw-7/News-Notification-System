# News-Notification-System

Overview
This project is an automated news aggregation and notification system designed specifically for the automotive industry. It scrapes official press releases from multiple car and bike manufacturers, stores them in a local SQLite database, exports them to a Google Sheet, and sends formatted HTML email notifications containing either newly found articles or the full collected dataset.

By automating the collection, storage, and sharing of news updates, the system makes it easy to keep track of automotive announcements from a variety of sources in one place. It supports multiple manufacturers' official websites and is designed to run on a schedule for continuous updates.

Key Features
Multi‑brand scraping
Retrieves the latest press releases from numerous manufacturers such as:
BMW India, Hero MotoCorp, Ather Energy, Royal Enfield, MG Motor, Bajaj Auto, Jeep India, TVS Motor, Harley‑Davidson, Isuzu India, Benelli, Revolt Motors, and Simple Energy.

Database storage
All articles are stored in an SQLite database (automotive_articles.db).
Duplicate entries are avoided by enforcing a UNIQUE constraint on article links.

Email notifications
Sends an HTML‑formatted email to a recipient:

If new articles are found, only the new articles are listed.

If no new articles are available, the complete database is sent.

Google Sheets integration
Syncs the database contents to a Google Sheets document for simplified viewing, filtering, and sharing.

Automation ready
Can be run manually or scheduled with cron (Linux/macOS) or Task Scheduler (Windows) for regular updates.

How It Works

Database setup
At runtime, the script checks for the presence of the SQLite database and the articles table.
If not present, it creates them. The table stores:

id (auto‑increment primary key)

date

title

link (unique)

site (manufacturer name)

Web scraping
Each manufacturer has its own scraper function.

Some sites are scraped with Selenium WebDriver for dynamic, JavaScript‑rendered content.

Others that return static HTML or JSON are processed with Requests and BeautifulSoup.

Each scraper extracts up to the latest 5 articles including date, title, link, and source.

Data insertion and filtering

For each scraped result, the script checks if the link already exists in the database.

New entries are inserted; old ones are skipped.

A list of new articles is maintained during the run.

Email generation

Uses smtplib with Gmail’s SMTP server to send messages.

HTML email content is generated as a simple styled table for readability.

Subject line changes depending on whether it is sending only new or all articles.

Export to Google Sheets

Connects to a specified Google Sheet using a service account (credentials.json required).

Clears existing data and writes the latest dataset from the database.

Columns: Date, Title, Link, Site.

Repeatable execution
You can run the script as often as you want. On subsequent runs, only new items trigger incremental updates in the database and email.

Technologies Used
Python 3 – Core programming language

Selenium WebDriver – Browser automation for scraping dynamic pages

BeautifulSoup4 – Parsing HTML content

Requests – Fetching static page content and JSON APIs

SQLite – Lightweight local data storage

gspread & oauth2client – Google Sheets API integration

smtplib, email.mime – Sending HTML email notifications

webdriver‑manager – Automatically downloads and manages ChromeDriver

