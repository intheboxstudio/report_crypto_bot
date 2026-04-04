# 📊 Crypto Report Bot

> An automated Python bot that aggregates crypto news, market data, social signals, and trending tokens — and compiles everything into a clean, formatted PDF report. No APIs required for news. Just run it.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen)]()

---

## 📋 Table of Contents

- [What It Does](#-what-it-does)
- [How the PDF Looks](#-how-the-pdf-looks)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [First-Time Setup](#-first-time-setup)
- [How to Run](#-how-to-run)
- [How It Works — Module by Module](#-how-it-works--module-by-module)
  - [Financial Indices](#1-financial-indices)
  - [RSS News Feeds](#2-rss-news-feeds)
  - [YouTube Channels](#3-youtube-channels)
  - [X / Twitter](#4-x--twitter)
  - [Telegram Channels](#5-telegram-channels)
  - [Trending Tokens](#6-trending-tokens)
  - [PDF Generation](#7-pdf-generation)
- [Customization](#-customization)
  - [Change News Sources](#change-news-sources)
  - [Change YouTube Channels](#change-youtube-channels)
  - [Change X Accounts](#change-x-accounts)
  - [Change Telegram Channels](#change-telegram-channels)
- [About the Default Sources](#-about-the-default-sources)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## 🔍 What It Does

**Crypto Report Bot** runs once, collects data from every major crypto information source simultaneously, and outputs a single polished PDF file that contains:

| Section | What you get |
|---|---|
| 📈 **Financial Indices** | Real-time prices and % change for Nasdaq, S&P 500, DXY, BTC, ETH, MSTR, COIN, MARA and more — with automatic market analysis |
| 📰 **Crypto News** | Latest headlines (title + link only) from 10 major news sites |
| 🎥 **YouTube** | Two most recent video titles from 8 top crypto channels |
| 🐦 **X / Twitter** | Latest 3 tweets from 12 curated crypto accounts |
| 📱 **Telegram** | Latest 3 messages from 8 curated crypto channels |
| 🔥 **Trending Tokens** | Top 6 trending tokens from CoinGecko with risk level and holding horizon |

The bot is designed to be your **morning briefing in one click** — open the PDF and you have everything you need to understand the market before you make any decision.

---

## 🖼 How the PDF Looks

The output is a multi-page PDF structured as follows:

```
┌─────────────────────────────────────────┐
│         Report Crypto - 03/04/2026      │  ← dark header with timestamp
├─────────────────────────────────────────┤
│  FINANCIAL INDICES AND MARKETS          │  ← dark section banner
│    ▸ US Equities                        │  ← grey subsection
│      Nasdaq 100:  24,046                │
│      +0.11% [UP]  => Sideways market    │  ← green/red color for % change
│    ▸ Currency & Liquidity               │
│    ▸ Global Indices                     │
│    ▸ Crypto-Equities                    │
│    ▸ Crypto                             │
├─────────────────────────────────────────┤
│  CRYPTO NEWS                            │
│  [CoinTelegraph] Bitcoin 'done' with... │  ← bold title
│  Link: https://cointelegraph.com/...    │  ← small italic link
├─────────────────────────────────────────┤
│  RECENT YOUTUBE VIDEOS                  │
│  [Coin Bureau] Taiwan is sitting on...  │
│  Published: 2026-04-03T11:16:31         │
├─────────────────────────────────────────┤
│  RECENT TWEETS FROM X                   │
│  @hardrockcrypto                        │
│  - GUERRA, CROLLI E HACK: Tutto Quello  │
│  - E uscito ora il nostro nuovo video   │
├─────────────────────────────────────────┤
│  LATEST TELEGRAM MESSAGES               │
│  @thecryptogateway                      │
│  - Circle annuncia il lancio di cirBTC  │
├─────────────────────────────────────────┤
│  TOP 6 TRENDING CRYPTOCURRENCIES        │
│  1. Bittensor (TAO)                     │
│     Rank: #36 | Risk: Low | Hold: Long  │
└─────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
crypto-report-bot/
│
├── report_crypto.py          # Main bot — generates the full PDF report
├── start_report.bat          # Windows launcher (double-click to run)
│
├── telegram_login.py         # One-time Telegram authentication
├── x_login_manuale.py        # One-time X/Twitter cookie export (via Brave)
├── test_browser.py           # ChromeDriver health check
│
├── session.session           # Telegram session file (auto-generated)
├── x_cookies.json            # X session cookies (auto-generated)
├── youtube_channel_cache.json # YouTube channel ID cache (auto-generated)
│
└── report_crypto_YYYYMMDD_HHMM.pdf  # Output PDF (auto-generated on each run)
```

> **Auto-generated files** are created the first time you run the bot. You don't need to create them manually.

---

## ⚙️ Prerequisites

- **Python 3.10+** — [Download](https://www.python.org/downloads/)
- **Google Chrome** — [Download](https://www.google.com/chrome/)
- **ChromeDriver** — must match your Chrome version exactly → [Download](https://googlechromelabs.github.io/chrome-for-testing/)
- **Brave Browser** *(optional, only for X/Twitter login)* — [Download](https://brave.com/)
- A **Telegram account** with API credentials (free) → [Get them](https://my.telegram.org/auth)

---

## 🚀 Installation

**1. Clone the repository**

```bash
git clone https://github.com/your-username/crypto-report-bot.git
cd crypto-report-bot
```

**2. Install Python dependencies**

```bash
pip install fpdf2 requests feedparser telethon selenium yfinance nest_asyncio beautifulsoup4
```

**3. Place ChromeDriver in your PATH**

Download ChromeDriver for your exact Chrome version, then either:
- Place `chromedriver.exe` in the same folder as the scripts, OR
- Add it to your system PATH

To verify it works:
```bash
python test_browser.py
```
You should see: `✅ ChromeDriver started correctly!`

---

## 🔐 First-Time Setup

Before the first run, you need to authenticate with Telegram and X/Twitter. This is a **one-time operation** — credentials are saved locally and reused automatically.

### Step 1 — Telegram

Open `report_crypto.py` and set your Telegram API credentials (obtained for free at [my.telegram.org](https://my.telegram.org/auth)):

```python
TELEGRAM_API_ID   = 12345678          # ← your API ID here
TELEGRAM_API_HASH = 'your_hash_here'  # ← your API hash here
```

Then run the login helper:

```bash
python telegram_login.py
```

Enter your phone number when prompted. A `session.session` file is created. You won't need to do this again.

### Step 2 — X / Twitter

Make sure you are **already logged into X** in your Brave browser. Close Brave completely, then run:

```bash
python x_login_manuale.py
```

This exports your session cookies to `x_cookies.json`. The bot will use them automatically on every run.

---

## ▶️ How to Run

**Option A — Double-click (Windows)**

Just double-click `start_report.bat`. The bot runs, collects all data, and saves a PDF like `report_crypto_20260403_0922.pdf` in the same folder.

**Option B — Command line**

```bash
python report_crypto.py
```

**Typical runtime:** 3–6 minutes (X/Twitter scraping is the slowest part).

---

## 🔧 How It Works — Module by Module

### 1. Financial Indices

```python
# report_crypto.py — get_market_indices()

_INDICES = {
    "US Equities": {
        "Nasdaq 100":  "^NDX",
        "S&P 500":     "^GSPC",
        "Russell 2000":"^RUT",
    },
    "Crypto": {
        "Bitcoin (BTC-USD)":  "BTC-USD",
        "Ethereum (ETH-USD)": "ETH-USD",
    },
    # ... more sections
}
```

Uses **yfinance** to pull the last 2 days of price history for each ticker. Computes the daily % change and generates a one-line automatic analysis (e.g. *"Risk-On: positive sentiment, crypto may follow"*). Displayed with **green** for positive and **red** for negative moves in the PDF.

---

### 2. RSS News Feeds

```python
# report_crypto.py — get_rss_news()

rss_feeds = {
    'CoinTelegraph':   'https://cointelegraph.com/rss',
    'BeInCrypto':      'https://beincrypto.com/feed',
    'Decrypt':         'https://decrypt.co/feed',
    'Bitcoin Magazine':'https://bitcoinmagazine.com/feed',
    # ... 10 sources total
}

feed = feedparser.parse(url, request_headers=_REQ_HEADERS)
entries = feed.entries[:3]  # top 3 articles per source
```

Parses 10 RSS feeds using **feedparser**, collecting the 3 most recent headlines per source. Only the title and link are written to the PDF — no article body — keeping the report concise.

---

### 3. YouTube Channels

```python
# report_crypto.py — _fetch_yt_feed()

def _fetch_yt_feed(channel_id):
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 ... Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*',
        'Referer': 'https://www.youtube.com/',
    }
    res = requests.get(feed_url, headers=headers, timeout=15)
    return feedparser.parse(res.text)  # parse XML string, not URL
```

> **Key fix:** YouTube silently returns 0 entries when `feedparser` fetches the feed URL directly (empty User-Agent). The bot downloads the XML with `requests` using a full Chrome User-Agent first, then passes the raw text to `feedparser`. This reliably returns the latest videos.

Channel IDs are hardcoded for reliability. For channels that only have a `@handle`, the bot resolves the handle to a channel ID on first run using Selenium, then caches the result in `youtube_channel_cache.json`.

---

### 4. X / Twitter

```python
# report_crypto.py — get_latest_tweets_selenium()

driver.get(f"https://x.com/{username}")
time.sleep(7)
driver.execute_script("window.scrollBy(0, 500);")
time.sleep(3)
els = driver.find_elements(By.XPATH, '//div[@data-testid="tweetText"]')
texts = [el.text.strip() for el in els[:3] if el.text.strip()]
```

Uses **Selenium** with a headless Chrome instance. Cookies from `x_cookies.json` are injected before navigating to each profile, so the bot sees the logged-in timeline and avoids login walls. Extracts up to 3 tweets per account. In the PDF, only the **first meaningful line** of each tweet is shown.

---

### 5. Telegram Channels

```python
# report_crypto.py — _fetch_telegram_async()

async for msg in client.iter_messages(channel, limit=3):
    txt = msg.text or getattr(msg, 'message', '') or ''
    if txt.strip():
        chan_msgs.append(txt.strip()[:2000])
```

Uses the **Telethon** library with the MTProto protocol — meaning it reads channels as a real Telegram user account, not a bot. This gives access to any public channel without restrictions. Fetches the last 3 messages per channel. In the PDF, only the **first meaningful line** of each message is shown.

---

### 6. Trending Tokens

```python
# report_crypto.py — get_trending_tokens()

res = requests.get(
    'https://api.coingecko.com/api/v3/search/trending',
    headers={'Accept': 'application/json'}, timeout=15
)
coins = res.json().get('coins', [])[:6]
```

Calls the **CoinGecko free API** (no key required) to get the top 6 trending tokens. For each token it shows the market cap rank, a risk level (Low / Medium / High based on rank), and a suggested holding horizon.

---

### 7. PDF Generation

```python
# report_crypto.py — pdf_trend_row()

def pdf_trend_row(pdf, label, value, change_pct, trend, analysis):
    if change_pct >= 0:
        pdf.set_text_color(0, 130, 0)   # green
    else:
        pdf.set_text_color(180, 0, 0)   # red
    pdf.multi_cell(0, LINE_H, f"  {sign}{change_pct:.2f}%  [{trend}]", ...)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, f"  => {analysis}", ...)
```

Uses **fpdf2** for PDF generation. All text passes through a `to_latin1()` function that strips emoji, normalizes accented characters, and encodes to latin-1 — the charset required by fpdf2's built-in Helvetica font. Section headers use a dark navy background with white text. Financial change percentages are rendered in green or red. Everything uses `multi_cell()` to ensure text never overflows the page margins.

---

## 🛠 Customization

Every data source in the bot is defined as a simple Python dictionary or list at the top of `report_crypto.py`. You can add, remove, or replace any entry without touching any other part of the code.

### Change News Sources

```python
# report_crypto.py — lines ~45-56

rss_feeds = {
    'CoinTelegraph':   'https://cointelegraph.com/rss',
    'BeInCrypto':      'https://beincrypto.com/feed',
    'Decrypt':         'https://decrypt.co/feed',
    'Bitcoin Magazine':'https://bitcoinmagazine.com/feed',
    'The Block':       'https://www.theblock.co/rss.xml',
    'Blockworks':      'https://blockworks.co/feed',
    # ↑ Remove any line to drop that source
    # ↓ Add any RSS feed URL to add a new source
    'Your Source':     'https://yoursite.com/feed',
}
```

Any website that publishes an RSS feed can be added. Just find its `/feed` or `/rss` URL.

---

### Change YouTube Channels

```python
# report_crypto.py — lines ~59-68

youtube_channels = {
    'Altcoin Daily':      'UCbLhGKVY-bJPcawebgtNfbw',  # ← channel ID
    'Coin Bureau':        'UCR93yACeNzxMSk6Y1cHM2pw',
    'Hard Rock Crypto':   'UCd2rBO4z1XAwka2ti1hhJJw',
    # ↑ Use the channel ID (UC...) for reliability
    # ↓ Or use the @handle — it will be auto-resolved on first run
    'New Channel':        '@thehandle',
}
```

To find a channel's ID: go to the channel page on YouTube → right-click → View Page Source → search for `"channelId"`. Or use any free channel ID finder tool online.

---

### Change X Accounts

```python
# report_crypto.py — lines ~70-74

x_accounts = [
    "AFTSDCrypto",
    "crypto_ita2",
    "giacomozucco",
    # ↑ Remove any username to stop following them
    # ↓ Add any X username (without @)
    "newaccount",
]
```

---

### Change Telegram Channels

```python
# report_crypto.py — lines ~37-42

telegram_channels = [
    "thecryptogateway",
    "criptovalutait",
    "whale_alert",
    # ↑ Remove any channel to stop reading it
    # ↓ Add the @handle of any public Telegram channel (without @)
    "newchannel",
]
```

> Only **public** Telegram channels can be accessed. Private channels require an invitation.

---

## 🌐 About the Default Sources

The default sources were hand-picked after consulting with professional crypto traders and analysts who operate in this market full-time. They represent a balanced mix of English and Italian language sources covering all major angles:

**News sites** — CoinTelegraph, BeInCrypto, Decrypt, Bitcoin Magazine, The Block, Blockworks, Crypto News, CoinDesk, CoinMarketCap, CoinGecko Blog

**YouTube channels** — Altcoin Daily and Coin Bureau (global English-language leaders), Hard Rock Crypto, The Crypto Gateway, David Pascucci Trading, Eugenio Benetazzo, Massimo Rea, Leonardo Vecchio (top Italian-language crypto creators)

**X / Twitter accounts** — A curated mix of Italian and international analysts, traders, DeFi researchers and on-chain monitors including @giacomozucco, @TizianoTridico, @whale_alert style accounts and more

**Telegram channels** — A selection of Italian and international signal channels, news channels and whale alert services

You are free to replace all of them with sources relevant to your own language, market focus, or investment style.

---

## 🛠 Troubleshooting

| Problem | Solution |
|---|---|
| `ChromeDriver not found` | Make sure `chromedriver.exe` is in the same folder or in PATH. Version must match Chrome exactly. |
| `Cookie X expired` | Re-run `x_login_manuale.py` to generate new cookies. |
| `Telegram session invalid` | Delete `session.session` and re-run `telegram_login.py`. |
| `YouTube: no videos found` | Delete `youtube_channel_cache.json` and re-run — it will re-resolve the channel IDs. |
| `CoinGecko: rate limit` | The free CoinGecko API allows ~30 req/min. Wait a minute and retry. |
| `RSS feed: no articles` | Some sites block scrapers temporarily. Try again later or replace the feed URL. |
| PDF output has garbled text | A character that can't be encoded to latin-1 slipped through. Open a GitHub Issue with the channel name. |

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Built with ❤️ for the crypto community · Stars ⭐ are appreciated

</div>
