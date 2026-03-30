📦 Requirements

To run the Crypto Report Bot, you need the following components:

Python 3.10.x
Core programming language used to execute the bot scripts.
Google Chrome (latest stable version)
Required for scraping data (especially from X/Twitter) via browser automation.
ChromeDriver (matching Chrome version)
Enables Python (via Selenium) to control Chrome programmatically.

Python Libraries
Install via pip:

requests
beautifulsoup4
fpdf2
feedparser
selenium
telethon
nest_asyncio
yfinance

These handle web scraping, PDF generation, Telegram access, RSS feeds, and financial data.

Telegram Account
Required to access and read messages from crypto Telegram channels.
⚙️ How the Bot Works

The bot is a data aggregation and reporting system that collects crypto-related information from multiple sources and generates a structured PDF report.

🔄 Workflow
Initialization
The bot is started via a .bat file.
It loads configuration and initializes all modules.
Data Collection
The bot gathers data from multiple sources:
RSS feeds → crypto news websites
YouTube feeds → latest crypto-related videos
X (Twitter) → posts from selected traders/analysts (via Selenium + Chrome)
Telegram channels → messages via Telethon API
Financial APIs → indices and market data (via yfinance)
CoinGecko (or similar) → trending cryptocurrencies
Processing
Extracts relevant content (titles, messages, trends)
Filters and organizes the data into structured sections
Report Generation
Uses fpdf2 to generate a PDF report
The report includes:
Crypto news
YouTube videos
Tweets
Telegram messages
Financial indices
Trending cryptocurrencies
Output
A timestamped PDF file is created in the bot directory
Execution time: ~3–5 minutes
📄 Output Structure

The generated report contains:

Crypto News → Market sentiment overview
YouTube Videos → Educational and analysis content
Tweets (X) → Insights from traders
Telegram Messages → Real-time signals and discussions
Financial Indices → Macro market context
Trending Cryptos → Potential investment opportunities
🔐 Authentication
Telegram login is required only once
A local session file (session.session) is created and reused
This file must be kept secure
🚀 Usage

After setup:

Double-click → avvia_report.bat

That’s it. The bot runs automatically and generates a new report each time.
