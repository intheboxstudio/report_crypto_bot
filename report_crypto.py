import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests
import re
import json
import os
import time
import asyncio
import feedparser
import nest_asyncio
import yfinance as yf
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import datetime
from telethon import TelegramClient
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

nest_asyncio.apply()

# ============================================================
# CONFIG
# ============================================================

TELEGRAM_API_ID   = 26134051
TELEGRAM_API_HASH = 'b1855096745f810ea48fab762c63346c'
SESSION_PATH      = 'session'
COOKIE_FILE       = 'x_cookies.json'
YT_CACHE_FILE     = 'youtube_channel_cache.json'

telegram_channels = [
    "thecryptogateway", "cryptosignals_org",
    "criptovalutait", "dash2trade", "defimillion",
    "rocketwalletsignal", "btcchamp", "whale_alert"
]

rss_feeds = {
    'CoinDesk':        'https://www.coindesk.com/arc/outboundfeeds/rss/',
    'CoinTelegraph':   'https://cointelegraph.com/rss',
    'Crypto News':     'https://cryptonews.com/news/feed',
    'BeInCrypto':      'https://beincrypto.com/feed',
    'CoinMarketCap':   'https://coinmarketcap.com/headlines/news/rss/',
    'CoinGecko Blog':  'https://blog.coingecko.com/rss/',
    'Decrypt':         'https://decrypt.co/feed',
    'Bitcoin Magazine':'https://bitcoinmagazine.com/feed',
    'The Block':       'https://www.theblock.co/rss.xml',
    'Blockworks':      'https://blockworks.co/feed',
}

# Valori: channel_id diretto (UC...) oppure handle (@nome) da risolvere con Selenium + cache.
youtube_channels = {
    'Altcoin Daily':          'UCbLhGKVY-bJPcawebgtNfbw',
    'Coin Bureau':            'UCR93yACeNzxMSk6Y1cHM2pw',
    'Hard Rock Crypto':       'UCd2rBO4z1XAwka2ti1hhJJw',
    'David Pascucci Trading': 'UCs2TIe_2qF1k0vjaG-CcP1A',
    'Eugenio Benetazzo':      'UCYwmP5UBYjbH8Zb2P-JliFg',
    'The Crypto Gateway':     'UC9X2f4pVXSNzsJ2c6ZQVqBQ',
    'Massimo Rea':            '@massimorea-quant-analyst',
    'Leonardo Vecchio':       '@leonardovecchio',
}

x_accounts = [
    "AFTSDCrypto", "crypto_ita2", "DeFi_Italia", "giacomozucco",
    "zaragast_crypto", "AngeloniFilippo", "hardrockcrypto",
    "TradingonIt", "MarcheseCrypto", "ChartMind",
    "crypto_gateway", "TizianoTridico"
]

# ============================================================
# TESTO: pulizia e conversione per FPDF (latin-1)
# ============================================================

def remove_emoji(text):
    pattern = re.compile(
        "[\U0001F000-\U0001FFFF"
        "\U00002300-\U000027FF"
        "\U00002900-\U00002BFF"
        "\U0000FE00-\U0000FEFF"
        "\U0000200B-\U0000200F"
        "\U00002060-\U00002064"
        "]+",
        flags=re.UNICODE
    )
    return pattern.sub('', text)

def to_latin1(text):
    """Converte testo in stringa latin-1 sicura per FPDF."""
    if not text:
        return ""
    text = str(text).replace('\x00', '').replace('\r', '').strip()
    text = remove_emoji(text)
    subs = [
        ('\u00e0','a'), ('\u00e8','e'), ('\u00e9','e'), ('\u00ec','i'),
        ('\u00f2','o'), ('\u00f9','u'), ('\u00c0','A'), ('\u00c8','E'),
        ('\u00c9','E'), ('\u00cc','I'), ('\u00d2','O'), ('\u00d9','U'),
        ('\u00e1','a'), ('\u00e2','a'), ('\u00e3','a'), ('\u00e4','a'),
        ('\u00eb','e'), ('\u00ea','e'), ('\u00ef','i'), ('\u00ee','i'),
        ('\u00f3','o'), ('\u00f4','o'), ('\u00f6','o'), ('\u00fa','u'),
        ('\u00fc','u'), ('\u00f1','n'),
        ('\u2019',"'"), ('\u2018',"'"), ('\u201c','"'), ('\u201d','"'),
        ('\u2013','-'), ('\u2014','-'), ('\u2022','-'), ('\u2026','...'),
        ('\u20ac','EUR'), ('\u00a0',' '), ('\u00b0',''), ('\u00ae',''),
        ('\u2122',''), ('\u00ab','"'), ('\u00bb','"'),
    ]
    for a, b in subs:
        text = text.replace(a, b)
    text = text.encode('latin-1', errors='ignore').decode('latin-1')
    text = re.sub(r'  +', ' ', text)
    return text

def first_line(text, max_chars=120):
    """Estrae solo la prima riga significativa di un testo."""
    if not text:
        return ""
    for line in text.split('\n'):
        line = line.strip()
        # Salta righe vuote, sole menzioni, soli hashtag, soli URL
        if not line:
            continue
        if re.match(r'^@\w+$', line):
            continue
        if re.match(r'^#\w+$', line):
            continue
        if re.match(r'^https?://', line):
            continue
        # Trovata la prima riga utile: troncala se troppo lunga
        if len(line) > max_chars:
            line = line[:max_chars].rsplit(' ', 1)[0] + '...'
        return line
    return ""
    """Normalizza testo tweet: rimuove menzioni su righe sole, comprime vuoti."""
    if not text:
        return ""
    lines = [l.strip() for l in text.split('\n')]
    out = []
    for line in lines:
        if not line:
            if out and out[-1] != '':
                out.append('')
            continue
        if re.match(r'^@\w+$', line):
            if out and out[-1] != '':
                out[-1] += ' ' + line
            continue
        if re.match(r'^https?://', line) or re.match(r'^\w[\w.-]+\.\w{2,}/\S*\s*\.{0,3}$', line):
            if out and out[-1] != '':
                out[-1] += ' ' + line
                continue
        out.append(line)
    while out and out[0] == '':
        out.pop(0)
    while out and out[-1] == '':
        out.pop()
    return '\n'.join(out)

def clean_telegram(text):
    """Normalizza testo Telegram: rimuove markdown, comprime vuoti."""
    if not text:
        return ""
    text = re.sub(r'\[([^\]]+)\]\(https?://[^)]+\)', r'\1', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'__(.+?)__', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = [l.strip() for l in text.split('\n')]
    return '\n'.join(lines).strip()

# ============================================================
# PDF: scrittura compatta e ordinata
# ============================================================

LINE_H = 4.5

def pdf_write_lines(pdf, text, max_chars=3000):
    """Scrive testo paragrafo per paragrafo con spaziatura compatta."""
    text = to_latin1(text)
    if not text:
        return
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(' ', 1)[0] + '...'
    pdf.set_font("Helvetica", "", 9)
    for i, para in enumerate(text.split('\n')):
        para = para.strip()
        if not para:
            if i < len(text.split('\n')) - 1:
                pdf.ln(2)
        else:
            pdf.multi_cell(0, LINE_H, para, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

def pdf_label(pdf, text):
    """Etichetta piccola in grassetto."""
    text = to_latin1(text)
    if not text:
        return
    pdf.set_font("Helvetica", "B", 8)
    pdf.multi_cell(0, 4.0, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

def pdf_item_header(pdf, text):
    """Intestazione voce (account/canale/notizia)."""
    text = to_latin1(text)
    pdf.set_font("Helvetica", "B", 10)
    pdf.multi_cell(0, 5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)

def pdf_small_italic(pdf, text):
    """Testo piccolo corsivo (link, data, etichette)."""
    text = to_latin1(text)
    if not text:
        return
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)

def pdf_section_title(pdf, title):
    """Titolo sezione con sfondo blu scuro."""
    pdf.set_fill_color(20, 20, 60)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 12)
    pdf.multi_cell(0, 8, to_latin1(title),
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1)

def pdf_subsection_title(pdf, title):
    """Titolo sotto-sezione con sfondo grigio chiaro."""
    pdf.set_fill_color(230, 230, 240)
    pdf.set_text_color(20, 20, 60)
    pdf.set_font("Helvetica", "B", 9)
    pdf.multi_cell(0, 6, to_latin1(title),
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    pdf.ln(1)

def pdf_separator(pdf):
    pdf.set_draw_color(200, 200, 200)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(2)

def pdf_trend_row(pdf, label, value, change_pct, trend, analysis):
    """Riga formattata per indici finanziari con indicatore SU/GIU colorato."""
    label_t  = to_latin1(label)
    value_t  = to_latin1(value)
    sign     = "+" if change_pct >= 0 else ""
    chg_t    = f"{sign}{change_pct:.2f}%"
    analysis_t = to_latin1(analysis)

    # Nome + valore
    pdf.set_font("Helvetica", "B", 9)
    pdf.multi_cell(0, LINE_H, f"{label_t}:  {value_t}",
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Variazione con colore
    if change_pct >= 0:
        pdf.set_text_color(0, 130, 0)
    else:
        pdf.set_text_color(180, 0, 0)
    pdf.set_font("Helvetica", "B", 9)
    pdf.multi_cell(0, LINE_H, f"  {chg_t}  [{trend}]",
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)

    # Analisi
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, f"  => {analysis_t}",
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.ln(1)

# ============================================================
# RSS NEWS
# ============================================================

_REQ_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/124.0.0.0 Safari/537.36'),
    'Accept-Language': 'en-US,en;q=0.9',
}

def fetch_article_text(url):
    try:
        from bs4 import BeautifulSoup
        res = requests.get(url, headers=_REQ_HEADERS, timeout=12)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            for tag in soup(['script','style','nav','footer','header','aside','form','noscript']):
                tag.decompose()
            article = (soup.find('article') or
                       soup.find(class_=re.compile(r'article|content|post|entry', re.I)))
            paras = article.find_all('p') if article else soup.find_all('p')
            text = ' '.join(p.get_text(' ', strip=True)
                            for p in paras if len(p.get_text(strip=True)) > 40)
            return text[:3000] if text else ''
    except Exception:
        pass
    return ''

def get_rss_news():
    """Solo titolo e link — nessun download del testo completo."""
    news = []
    for name, url in rss_feeds.items():
        print(f"    [{name}] ...")
        try:
            feed = feedparser.parse(url, request_headers=_REQ_HEADERS)
            entries = feed.entries[:3]
            if not entries:
                news.append((name, "Nessun articolo trovato", url))
                continue
            for entry in entries:
                title = getattr(entry, 'title', 'N/A')
                link  = getattr(entry, 'link', url)
                news.append((name, title, link))
        except Exception as e:
            news.append((name, f"Errore: {str(e)[:60]}", url))
    return news

# ============================================================
# YOUTUBE
# ============================================================

def _fetch_yt_feed(channel_id):
    """
    FIX: scarica il feed XML con requests (headers completi) poi lo passa
    a feedparser come stringa — evita il blocco per User-Agent vuoto.
    """
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        headers = {
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/124.0.0.0 Safari/537.36'),
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
            'Referer': 'https://www.youtube.com/',
        }
        res = requests.get(feed_url, headers=headers, timeout=15)
        if res.status_code == 200 and res.text.strip():
            return feedparser.parse(res.text)
        print(f"    [WARN] Feed YT HTTP {res.status_code} per {channel_id}")
    except Exception as e:
        print(f"    [WARN] _fetch_yt_feed({channel_id}): {e}")
    return None

def _resolve_handle(handle):
    """Risolve @handle → channel_id con cache locale. Fallback Selenium."""
    cache = {}
    try:
        if os.path.exists(YT_CACHE_FILE):
            with open(YT_CACHE_FILE, 'r') as f:
                cache = json.load(f)
    except Exception:
        pass

    if handle in cache:
        print(f"    [{handle}] da cache: {cache[handle]}")
        return cache[handle]

    channel_id = None
    url = f"https://www.youtube.com/{handle}/videos"
    patterns = [
        r'"channelId"\s*:\s*"(UC[a-zA-Z0-9_-]{22})"',
        r'"externalId"\s*:\s*"(UC[a-zA-Z0-9_-]{22})"',
    ]

    # Tentativo 1: requests
    try:
        res = requests.get(url, headers=_REQ_HEADERS, timeout=12)
        if res.status_code == 200:
            for pat in patterns:
                m = re.search(pat, res.text)
                if m:
                    channel_id = m.group(1)
                    break
    except Exception:
        pass

    # Tentativo 2: Selenium
    if not channel_id:
        print(f"    [{handle}] provo Selenium...")
        try:
            opts = Options()
            opts.add_argument("--headless=new")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--window-size=1920,1080")
            opts.add_argument("--disable-blink-features=AutomationControlled")
            opts.add_argument("--log-level=3")
            opts.add_experimental_option("excludeSwitches",
                                         ["enable-automation","enable-logging"])
            opts.add_experimental_option("useAutomationExtension", False)
            opts.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            drv = webdriver.Chrome(options=opts)
            drv.execute_script(
                "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
            drv.get(url)
            time.sleep(6)
            src = drv.page_source
            drv.quit()
            for pat in patterns:
                m = re.search(pat, src)
                if m:
                    channel_id = m.group(1)
                    break
        except Exception as e:
            print(f"    [WARN] Selenium {handle}: {e}")

    if channel_id:
        cache[handle] = channel_id
        try:
            with open(YT_CACHE_FILE, 'w') as f:
                json.dump(cache, f)
        except Exception:
            pass
        print(f"    [{handle}] risolto: {channel_id}")
    else:
        print(f"    [WARN] {handle}: non risolvibile")

    return channel_id

def get_youtube_videos():
    videos = []
    for name, val in youtube_channels.items():
        print(f"    [{name}] ...")
        channel_id = _resolve_handle(val) if val.startswith('@') else val
        if not channel_id:
            videos.append((name, "Handle non risolvibile", '', '', ''))
            continue
        feed = _fetch_yt_feed(channel_id)
        if not feed or not feed.entries:
            videos.append((name, "Nessun video nel feed", '', '', ''))
            continue
        for entry in feed.entries[:2]:
            title = getattr(entry, 'title', 'N/A')
            link  = getattr(entry, 'link', '')
            pub   = getattr(entry, 'published', '') or getattr(entry, 'updated', '')
            desc  = ''
            if hasattr(entry, 'summary'):
                desc = re.sub(r'<[^>]+>', '', entry.summary).strip()
            if not desc or len(desc) < 20:
                try:
                    r = requests.get(link, headers=_REQ_HEADERS, timeout=10)
                    if r.status_code == 200:
                        m = re.search(
                            r'<meta name="description" content="([^"]{15,})"', r.text)
                        if m:
                            desc = m.group(1)
                except Exception:
                    pass
            videos.append((name, title, link, desc[:800], pub))
    return videos

# ============================================================
# COINGECKO TRENDING
# ============================================================

def get_trending_tokens():
    results = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        res = requests.get(
            'https://api.coingecko.com/api/v3/search/trending',
            headers=headers, timeout=15
        )
        if res.status_code == 429:
            print("[WARN] CoinGecko: rate limit.")
            return []
        if res.status_code != 200:
            print(f"[WARN] CoinGecko: HTTP {res.status_code}")
            return []
        data = res.json()
        for c in data.get('coins', []):
            it = c['item']
            results.append((
                it.get('name', 'N/A'),
                it.get('symbol', 'N/A'),
                it.get('market_cap_rank') or 9999,
                it.get('score', 0),
            ))
    except Exception as e:
        print(f"[WARN] CoinGecko: {e}")
    return results[:6]

def risk_level(rank):
    if rank <= 100: return "Basso"
    if rank <= 500: return "Medio"
    return "Alto"

def holding_duration(score):
    if score > 70: return "Breve (< 24h)"
    if score > 50: return "Breve-Medio (< 48h)"
    if score > 30: return "Medio (< 7 giorni)"
    return "Lungo termine (10+ giorni)"

# ============================================================
# INDICI FINANZIARI
# ============================================================

_INDICES = {
    "Indici Azionari USA": {
        "Nasdaq 100":   "^NDX",
        "S&P 500":      "^GSPC",
        "Russell 2000": "^RUT",
    },
    "Valuta e Liquidita": {
        "DXY (Dollar Index)": "DX-Y.NYB",
        "US Treasury 10Y":    "^TNX",
    },
    "Indici Globali": {
        "MSCI World":       "URTH",
        "Hang Seng":        "^HSI",
        "CSI 300 (Cina)":   "000300.SS",
    },
    "Crypto-Equities": {
        "MicroStrategy":    "MSTR",
        "Coinbase":         "COIN",
        "Marathon Digital": "MARA",
    },
    "Crypto": {
        "Bitcoin (BTC-USD)":  "BTC-USD",
        "Ethereum (ETH-USD)": "ETH-USD",
    },
}

def _analyse(name, price, chg):
    """Genera testo di analisi automatica in base all'indice e alla variazione."""
    if name == "DXY (Dollar Index)":
        if chg > 0.3:   return "Dollaro forte: pressione ribassista su crypto"
        if chg < -0.3:  return "Dollaro debole: favorevole per BTC e crypto"
        return "Dollaro stabile: impatto neutro"
    if name == "US Treasury 10Y":
        if price > 4.5: return "Rendimenti alti: pressione su asset rischiosi"
        if price < 3.5: return "Rendimenti bassi: BTC piu attrattivo"
        return "Rendimenti nella norma"
    if name in ("Nasdaq 100", "S&P 500"):
        if chg > 1.0:   return "Risk-On: sentiment positivo, crypto potrebbero seguire"
        if chg < -1.0:  return "Risk-Off: possibile pressione anche su crypto"
        return "Mercato laterale: attendere conferme"
    if name == "Russell 2000":
        if chg > 1.0:   return "Liquidita abbondante: favorevole per altcoin"
        if chg < -1.0:  return "Liquidita in contrazione: cautela sulle altcoin"
        return "Liquidita stabile"
    if name in ("Hang Seng", "CSI 300 (Cina)"):
        if chg > 1.0:   return "Asia positiva: possibile liquidita verso crypto"
        if chg < -1.0:  return "Asia negativa: attenzione ai flussi asiatici"
        return "Asia stabile"
    if name in ("MicroStrategy", "Coinbase", "Marathon Digital"):
        if chg > 2.0:   return "Crypto-equity forte: possibile anticipo rialzo BTC"
        if chg < -2.0:  return "Crypto-equity debole: possibile anticipo ribasso BTC"
        return "Crypto-equity stabile"
    if chg > 1.0:   return "Trend positivo"
    if chg < -1.0:  return "Trend negativo"
    return "Laterale"

def get_market_indices():
    """Ritorna dict: {section: [(name, ticker, price, chg_pct, trend, analysis)]}"""
    result = {}
    for section, tickers in _INDICES.items():
        rows = []
        for name, ticker in tickers.items():
            try:
                hist = yf.Ticker(ticker).history(period="2d")
                if hist.empty:
                    rows.append((name, ticker, None, None, "N/D", "Dati non disponibili"))
                    continue
                price = hist["Close"].iloc[-1]
                chg   = ((price - hist["Close"].iloc[-2]) / hist["Close"].iloc[-2] * 100
                         if len(hist) >= 2 else 0.0)
                trend = "SU" if chg >= 0 else "GIU"
                rows.append((name, ticker, price, chg, trend, _analyse(name, price, chg)))
            except Exception as e:
                rows.append((name, ticker, None, None, "ERR", str(e)[:60]))
        result[section] = rows
    return result

# ============================================================
# X / TWITTER
# ============================================================

def _load_x_cookies(driver):
    if not os.path.exists(COOKIE_FILE):
        print("[WARN] Nessun cookie X. Esegui x_login_manuale.py prima.")
        return False
    try:
        driver.get("https://x.com")
        time.sleep(4)
        with open(COOKIE_FILE, 'r') as f:
            cookies = json.load(f)
        for c in cookies:
            c.pop('sameSite', None)
            try:
                driver.add_cookie(c)
            except Exception:
                pass
        driver.refresh()
        time.sleep(6)
        if "login" not in driver.current_url and "flow" not in driver.current_url:
            print("[OK] Login X via cookie riuscito.")
            return True
        print("[WARN] Cookie X scaduti.")
        os.remove(COOKIE_FILE)
        return False
    except Exception as e:
        print(f"[WARN] Errore login X: {e}")
        return False

def get_latest_tweets_selenium():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--log-level=3")
    opts.add_argument("--disable-extensions")
    opts.add_experimental_option("excludeSwitches", ["enable-automation","enable-logging"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    try:
        driver = webdriver.Chrome(options=opts)
        driver.execute_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
    except Exception as e:
        print(f"[ERRORE] ChromeDriver: {e}")
        return [(u, ["ChromeDriver non disponibile"]) for u in x_accounts]

    _load_x_cookies(driver)
    tweets = []
    for u in x_accounts:
        print(f"    [@{u}] ...")
        try:
            driver.get(f"https://x.com/{u}")
            time.sleep(7)
            driver.execute_script("window.scrollBy(0,500);")
            time.sleep(3)
            els = driver.find_elements(By.XPATH, '//div[@data-testid="tweetText"]')
            texts, seen = [], set()
            for el in els[:3]:
                t = el.text.strip()
                if t and t not in seen:
                    seen.add(t)
                    texts.append(t)
            if texts:
                tweets.append((u, texts))
            else:
                src = driver.page_source
                msg = ("Cookie X scaduti - riesegui x_login_manuale.py"
                       if "Log in" in src or "Sign in" in src
                       else "Nessun tweet trovato")
                tweets.append((u, [msg]))
        except Exception as e:
            tweets.append((u, [f"Errore: {str(e)[:80]}"]))

    try:
        driver.quit()
    except Exception:
        pass
    return tweets

# ============================================================
# TELEGRAM
# ============================================================

async def _fetch_telegram_async():
    client = TelegramClient(SESSION_PATH, TELEGRAM_API_ID, TELEGRAM_API_HASH)
    messages = []
    try:
        await client.start()
        if not await client.is_user_authorized():
            print("[ERRORE] Sessione Telegram non valida. Riesegui telegram_login.py")
            return [(ch, ["Sessione non valida"]) for ch in telegram_channels]
        for chan in telegram_channels:
            print(f"    [@{chan}] ...")
            chan_msgs = []
            try:
                async for msg in client.iter_messages(chan, limit=3):
                    txt = msg.text or getattr(msg, 'message', '') or ''
                    if txt.strip():
                        chan_msgs.append(txt.strip()[:2000])
                    elif msg.media:
                        caption = getattr(msg, 'text', '') or ''
                        chan_msgs.append(
                            f"[Media]{': ' + caption[:150] if caption else ''}")
                messages.append((chan, chan_msgs if chan_msgs else ["Nessun messaggio"]))
            except Exception as e:
                messages.append((chan, [f"Errore: {str(e)[:80]}"]))
    except Exception as e:
        print(f"[ERRORE] Telegram: {e}")
        return [(ch, [f"Errore: {str(e)[:60]}"]) for ch in telegram_channels]
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass
    return messages

def get_telegram_messages():
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run,
                                   _fetch_telegram_async()).result(timeout=120)
        return loop.run_until_complete(_fetch_telegram_async())
    except Exception as e:
        print(f"[ERRORE] Asyncio Telegram: {e}")
        return [(ch, [f"Errore: {str(e)[:60]}"]) for ch in telegram_channels]

# ============================================================
# GENERA PDF
# ============================================================

def create_pdf():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ── INTESTAZIONE ─────────────────────────────────────────
    pdf.set_fill_color(10, 10, 60)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 14, f"Report Crypto - {now}",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C", fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    # ── INDICI FINANZIARI ─────────────────────────────────────
    print("[*] Recupero indici finanziari...")
    all_indices = get_market_indices()
    pdf_section_title(pdf, "INDICI FINANZIARI E MERCATI")
    for section_name, rows in all_indices.items():
        pdf_subsection_title(pdf, section_name)
        for row in rows:
            name, ticker, price, chg, trend, analysis = row
            if price is not None:
                if price >= 1000:
                    val_str = f"{price:,.0f}"
                else:
                    val_str = f"{price:.4f}" if price < 1 else f"{price:.2f}"
                pdf_trend_row(pdf, f"{name} ({ticker})", val_str, chg, trend, analysis)
            else:
                pdf_item_header(pdf, f"{name} ({ticker}): dati non disponibili")
                pdf_small_italic(pdf, f"  {analysis}")
                pdf.ln(1)
        pdf.ln(1)
    pdf.ln(2)

    # ── NOTIZIE RSS — solo titolo ─────────────────────────────
    print("[*] Recupero notizie RSS...")
    rss_news = get_rss_news()
    pdf_section_title(pdf, "NOTIZIE CRYPTO")
    for item in rss_news:
        source, title, link = item[0], item[1], item[2]
        # Titolo in grassetto
        pdf_item_header(pdf, f"[{source}] {title}")
        # Link in corsivo piccolo
        pdf_small_italic(pdf, f"Link: {link[:120]}")
        pdf.ln(1)
        pdf_separator(pdf)
    pdf.ln(3)

    # ── VIDEO YOUTUBE — solo titolo ───────────────────────────
    print("[*] Recupero video YouTube...")
    yt_videos = get_youtube_videos()
    pdf_section_title(pdf, "VIDEO YOUTUBE RECENTI")
    for item in yt_videos:
        source, title, link = item[0], item[1], item[2]
        pub = item[4] if len(item) > 4 else ''
        pdf_item_header(pdf, f"[{source}] {title}")
        if pub:
            pdf_small_italic(pdf, f"Pubblicato: {pub[:70]}")
        if link:
            pdf_small_italic(pdf, f"Link: {link[:120]}")
        pdf.ln(1)
        pdf_separator(pdf)
    pdf.ln(3)

    # ── TWEET DA X ───────────────────────────────────────────
    print("[*] Recupero tweet da X...")
    tweets = get_latest_tweets_selenium()
    pdf_section_title(pdf, "TWEET RECENTI DA X")
    for u, tweet_list in tweets:
        pdf_item_header(pdf, f"@{u}")
        if isinstance(tweet_list, list):
            for t in tweet_list:
                line = first_line(t)
                if line:
                    pdf_write_lines(pdf, f"- {line}", max_chars=150)
        else:
            line = first_line(str(tweet_list))
            if line:
                pdf_write_lines(pdf, f"- {line}", max_chars=150)
        pdf.ln(1)
        pdf_separator(pdf)
    pdf.ln(3)

    # ── MESSAGGI TELEGRAM ────────────────────────────────────
    print("[*] Recupero messaggi Telegram...")
    tg_msgs = get_telegram_messages()
    pdf_section_title(pdf, "ULTIMI MESSAGGI TELEGRAM")
    for ch, msg_list in tg_msgs:
        pdf_item_header(pdf, f"@{ch}")
        if isinstance(msg_list, list):
            for txt in msg_list:
                line = first_line(clean_telegram(txt))
                if line:
                    pdf_write_lines(pdf, f"- {line}", max_chars=150)
        else:
            line = first_line(clean_telegram(str(msg_list)))
            if line:
                pdf_write_lines(pdf, f"- {line}", max_chars=150)
        pdf.ln(1)
        pdf_separator(pdf)
    pdf.ln(3)

    # ── TOKEN TRENDING (in fondo) ─────────────────────────────
    print("[*] Recupero token trending CoinGecko...")
    tokens = get_trending_tokens()
    pdf_section_title(pdf, "TOP 6 CRIPTOVALUTE IN TENDENZA")
    if tokens:
        for i, (name, symbol, rank, score) in enumerate(tokens, 1):
            risk     = risk_level(rank)
            hold     = holding_duration(score)
            rank_str = str(rank) if rank < 9999 else "N/D"
            pdf_item_header(pdf, f"{i}. {to_latin1(name)} ({to_latin1(symbol)})")
            pdf_write_lines(pdf,
                f"Market Cap Rank: #{rank_str}  |  Rischio: {risk}  |  Orizzonte: {hold}",
                max_chars=200)
            pdf.ln(1)
            pdf_separator(pdf)
    else:
        pdf_write_lines(pdf, "Dati non disponibili (rate limit CoinGecko).")
    pdf.ln(3)

    # ── SALVA ────────────────────────────────────────────────
    filename = f"report_crypto_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    pdf.output(filename)
    print(f"\n[OK] Report salvato: {filename}")
    return filename

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=== Report Crypto Bot ===")
    print(f"Avviato il: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
    try:
        create_pdf()
    except Exception as e:
        print(f"\n[ERRORE] {e}")
        import traceback
        traceback.print_exc()
    input("\nPremi INVIO per uscire...")
