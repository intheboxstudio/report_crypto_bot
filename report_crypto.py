import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests
import yfinance as yf
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import datetime
import feedparser
import unicodedata
import asyncio
import time
import nest_asyncio
from telethon import TelegramClient
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

nest_asyncio.apply()

# === CONFIG ===

TELEGRAM_API_ID = 26134051
TELEGRAM_API_HASH = 'b1855096745f810ea48fab762c63346c'
SESSION_PATH = 'session'

# === CREDENZIALI X (Twitter) ===
# Inserisci il tuo username X (senza @) e la tua password
X_USERNAME = 'il_tuo_username'   # <-- MODIFICA con il tuo username X
X_PASSWORD = 'la_tua_password'   # <-- MODIFICA con la tua password X

telegram_channels = [
    "KoinsquareNews", "thecryptogateway", "cryptosignals_org",
    "criptovalutait", "dash2trade", "defimillion",
    "rocketwalletsignal", "btcchamp", "whale_alert"
]

rss_feeds = {
    'CoinDesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
    'CoinTelegraph': 'https://cointelegraph.com/rss',
    'Crypto News': 'https://cryptonews.com/news/feed',
    'BeInCrypto': 'https://beincrypto.com/feed',
    'CoinMarketCap': 'https://coinmarketcap.com/headlines/news/rss/',
    'CoinGecko': 'https://www.coingecko.com/en/news.rss',
    'Traders Union': 'https://tradersunion.com/feed/',
}

youtube_channels = {
    'Altcoin Daily': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCbLhGKVY-bJPcawebgtNfbw',
    'Coin Bureau': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCR93yACeNzxMSk6Y1cHM2pw',
    'Massimo Rea': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCiLrQAYVZ8qOwJshydfTAvQ',
    'David Pascucci Trading': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCVW36xMRTRiKke_GxRSBdkg',
    'Leonardo Vecchio': 'https://www.youtube.com/feeds/videos.xml?channel_id=UC8vOE6RGzkTqKHwU4RUwCQQ',
    'Hard Rock Crypto': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCm9cWb-H2LJ7BdkszFQvHLw',
    'The Crypto Gateway': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCQ01e9VY08pJLlvqOhLSywA',
    'Eugenio Benetazzo': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCZm6ztjqPOepPbT3QzGQ6Gg',
}

x_accounts = [
    "AFTSDCrypto", "crypto_ita2", "DeFi_Italia", "giacomozucco",
    "zaragast_crypto", "AngeloniFilippo", "hardrockcrypto",
    "TradingonIt", "MarcheseCrypto", "ChartMind",
    "crypto_gateway", "TizianoTridico"
]

# === UTILS ===

def safe_text(text):
    if not text:
        return "N/A"
    text = str(text)
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = text.replace('\x00', '').replace('\r', '').strip()
    text = text[:400]
    # Se dopo tutto il testo e' vuoto, restituisce placeholder
    if not text.strip():
        return "N/A"
    return text

def pdf_title(pdf, title):
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, safe_text(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)

def pdf_line(pdf, text):
    text = safe_text(text)
    try:
        pdf.multi_cell(0, 5, text)
    except Exception:
        pass

# === RSS NEWS ===

def get_rss_news():
    news = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    for name, url in rss_feeds.items():
        try:
            feed = feedparser.parse(url, request_headers=headers)
            for entry in feed.entries[:2]:
                title = getattr(entry, 'title', 'N/A')
                link = getattr(entry, 'link', url)
                news.append((name, title, link))
        except Exception as e:
            news.append((name, f"Errore: {str(e)[:60]}", url))
    return news

# === YOUTUBE ===

def get_youtube_videos():
    videos = []
    for name, url in youtube_channels.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:1]:
                title = getattr(entry, 'title', 'N/A')
                link = getattr(entry, 'link', url)
                videos.append((name, title, link))
        except Exception as e:
            videos.append((name, f"Errore: {str(e)[:60]}", url))
    return videos

# === COINGECKO TRENDING ===

def get_trending_tokens():
    results = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        res = requests.get(
            'https://api.coingecko.com/api/v3/search/trending',
            headers=headers, timeout=15
        )
        if res.status_code == 429:
            print("[WARN] CoinGecko: rate limit raggiunto.")
            return []
        if res.status_code != 200:
            print(f"[WARN] CoinGecko: errore HTTP {res.status_code}")
            return []
        data = res.json()
        for c in data.get('coins', []):
            it = c['item']
            name = it.get('name', 'N/A')
            symbol = it.get('symbol', 'N/A')
            rank = it.get('market_cap_rank') or 9999
            score = it.get('score', 0)
            results.append((name, symbol, rank, score))
    except Exception as e:
        print(f"[WARN] CoinGecko exception: {e}")
    return results[:6]

def risk_level(rank):
    if rank <= 100: return "Basso"
    if rank <= 500: return "Medio"
    return "Alto"

def duration(score):
    if score > 70: return "Compra ora e vendi entro 24 ore"
    elif score > 50: return "Compra ora e vendi entro 48 ore"
    elif score > 30: return "Compra ora e vendi entro 7 giorni"
    else: return "Lungo termine (10+ giorni)"

# === SELENIUM / X ===

def x_login(driver):
    """
    Login a X salvando i cookie dopo il primo accesso manuale.
    Al primo avvio apre Chrome visibile per fare il login manuale,
    poi salva i cookie. Dai avvii successivi usa i cookie salvati.
    """
    import json
    import os
    COOKIE_FILE = 'x_cookies.json'

    # Se esistono cookie salvati, usali direttamente
    if os.path.exists(COOKIE_FILE):
        try:
            driver.get("https://x.com")
            time.sleep(4)
            with open(COOKIE_FILE, 'r') as f:
                cookies = json.load(f)
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception:
                    pass
            driver.refresh()
            time.sleep(5)
            if "login" not in driver.current_url and "flow" not in driver.current_url:
                print("[OK] Login X via cookie completato.")
                return True
            else:
                print("[WARN] Cookie X scaduti, elimino e riprovo al prossimo avvio.")
                os.remove(COOKIE_FILE)
                return False
        except Exception as e:
            print(f"[WARN] Errore caricamento cookie X: {e}")
            return False

    # Nessun cookie salvato: apri Chrome VISIBILE per login manuale
    print("[*] PRIMO AVVIO: apro Chrome per il login manuale a X.")
    print("[*] Accedi a X nel browser che si apre, poi torna qui e premi INVIO.")
    return False

def get_latest_tweets_selenium():
    tweets = []
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--log-level=3")
    opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    try:
        driver = webdriver.Chrome(options=opts)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception as e:
        print(f"[ERRORE] ChromeDriver non avviabile: {e}")
        return [(u, "ChromeDriver non disponibile") for u in x_accounts]

    # Login a X via cookie salvati
    import json, os
    COOKIE_FILE = 'x_cookies.json'
    logged_in = False

    if os.path.exists(COOKIE_FILE):
        logged_in = x_login(driver)
    else:
        print("[WARN] Nessun cookie X trovato. Esegui x_login_manuale.py per fare il login la prima volta.")

    for u in x_accounts:
        try:
            driver.get(f"https://x.com/{u}")
            time.sleep(8)
            els = driver.find_elements(By.XPATH, '//div[@data-testid="tweetText"]')
            if els:
                tweets.append((u, els[0].text[:200]))
            else:
                msg = "Nessun tweet trovato" if logged_in else "Credenziali X non configurate"
                tweets.append((u, msg))
        except Exception as e:
            tweets.append((u, f"Errore: {str(e)[:80]}"))

    try:
        driver.quit()
    except Exception:
        pass
    return tweets

# === TELEGRAM ===

async def fetch_telegram():
    client = TelegramClient(SESSION_PATH, TELEGRAM_API_ID, TELEGRAM_API_HASH)
    messages = []
    try:
        await client.start()
        if not await client.is_user_authorized():
            print("[ERRORE] Sessione Telegram non valida. Riesegui telegram_login.py")
            await client.disconnect()
            return [(ch, "Sessione non valida") for ch in telegram_channels]
        for chan in telegram_channels:
            try:
                async for msg in client.iter_messages(chan, limit=1):
                    if msg.text:
                        messages.append((chan, msg.text.replace("\n", " ")[:200]))
                    else:
                        messages.append((chan, "Messaggio senza testo (media/sticker)"))
                    break
            except Exception as e:
                messages.append((chan, f"Errore: {str(e)[:80]}"))
    except Exception as e:
        print(f"[ERRORE] Connessione Telegram: {e}")
        return [(ch, f"Errore: {str(e)[:80]}") for ch in telegram_channels]
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass
    return messages

def get_telegram_messages():
    try:
        return asyncio.run(fetch_telegram())
    except Exception as e:
        print(f"[ERRORE] Asyncio Telegram: {e}")
        return [(ch, f"Errore: {str(e)[:80]}") for ch in telegram_channels]


# === INDICI FINANZIARI ===

def get_market_indices():
    indices = {
        # Indici USA
        "Nasdaq 100":        "^NDX",
        "S&P 500":           "^GSPC",
        "Russell 2000":      "^RUT",
        # Valuta e Liquidita
        "DXY (Dollar Index)":"DX-Y.NYB",
        "US Treasury 10Y":   "^TNX",
        # Indici Globali
        "MSCI World":        "URTH",
        "Hang Seng":         "^HSI",
        "CSI 300 (Cina)":    "000300.SS",
        # Crypto-Equities
        "MicroStrategy":     "MSTR",
        "Coinbase":          "COIN",
        "Marathon Digital":  "MARA",
        # S&P Digital Markets
        "Bitcoin (BTC-USD)": "BTC-USD",
        "Ethereum (ETH-USD)":"ETH-USD",
    }
    results = []
    for name, ticker in indices.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="2d")
            if hist.empty or len(hist) < 1:
                results.append((name, ticker, None, None, "N/D"))
                continue
            current = hist["Close"].iloc[-1]
            if len(hist) >= 2:
                prev = hist["Close"].iloc[-2]
                change_pct = ((current - prev) / prev) * 100
            else:
                change_pct = 0.0
            trend = "SU" if change_pct >= 0 else "GIU"
            # Analisi testuale automatica
            if name == "DXY (Dollar Index)":
                if change_pct > 0.3:
                    analysis = "Dollaro forte: pressione ribassista sulle crypto"
                elif change_pct < -0.3:
                    analysis = "Dollaro debole: favorevole per Bitcoin e crypto"
                else:
                    analysis = "Dollaro stabile: impatto neutro sulle crypto"
            elif name == "US Treasury 10Y":
                if current > 4.5:
                    analysis = "Rendimenti alti: investitori preferiscono bond, pressione su crypto"
                elif current < 3.5:
                    analysis = "Rendimenti bassi: Bitcoin piu attrattivo come asset speculativo"
                else:
                    analysis = "Rendimenti nella norma: impatto moderato sulle crypto"
            elif name in ["Nasdaq 100", "S&P 500"]:
                if change_pct > 1.0:
                    analysis = "Risk-On: sentiment positivo, crypto potrebbero seguire al rialzo"
                elif change_pct < -1.0:
                    analysis = "Risk-Off: attenzione, possibile pressione anche sulle crypto"
                else:
                    analysis = "Mercato laterale: attendere conferme direzionali"
            elif name == "Russell 2000":
                if change_pct > 1.0:
                    analysis = "Liquidita abbondante: favorevole per altcoin speculative"
                elif change_pct < -1.0:
                    analysis = "Liquidita in contrazione: cautela sulle altcoin"
                else:
                    analysis = "Liquidita stabile"
            elif name in ["Hang Seng", "CSI 300 (Cina)"]:
                if change_pct > 1.0:
                    analysis = "Asia positiva: possibile iniezione di liquidita sul mercato crypto"
                elif change_pct < -1.0:
                    analysis = "Asia negativa: attenzione ai flussi di liquidita asiatici"
                else:
                    analysis = "Asia stabile"
            elif name in ["MicroStrategy", "Coinbase", "Marathon Digital"]:
                if change_pct > 2.0:
                    analysis = "Crypto-equity forte: possibile anticipo rialzo BTC"
                elif change_pct < -2.0:
                    analysis = "Crypto-equity debole: possibile anticipo ribasso BTC"
                else:
                    analysis = "Crypto-equity stabile"
            else:
                if change_pct > 1.0:
                    analysis = "Trend positivo"
                elif change_pct < -1.0:
                    analysis = "Trend negativo"
                else:
                    analysis = "Laterale"
            results.append((name, ticker, current, change_pct, trend, analysis))
        except Exception as e:
            results.append((name, ticker, None, None, "ERR", f"Errore: {str(e)[:60]}"))
    return results

# === PDF REPORT ===

def create_pdf():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.add_page()

    # Intestazione
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Report Crypto - {now}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(5)

    # Notizie RSS
    print("[*] Recupero notizie RSS...")
    rss_news = get_rss_news()
    pdf_title(pdf, "NOTIZIE CRYPTO")
    for s, t, l in rss_news:
        pdf_line(pdf, f"[{s}] {t}")
        pdf_line(pdf, f"Link: {l[:100]}")
        pdf.ln(1)
    pdf.ln(3)

    # Video YouTube
    print("[*] Recupero video YouTube...")
    yt_videos = get_youtube_videos()
    pdf_title(pdf, "VIDEO YOUTUBE RECENTI")
    for s, t, l in yt_videos:
        pdf_line(pdf, f"[{s}] {t}")
        pdf_line(pdf, f"Link: {l[:100]}")
        pdf.ln(1)
    pdf.ln(3)

    # Tweet da X
    print("[*] Recupero tweet da X (potrebbe richiedere 1-2 minuti)...")
    tweets = get_latest_tweets_selenium()
    pdf_title(pdf, "TWEET RECENTI DA X")
    for u, t in tweets:
        pdf_line(pdf, f"@{u}: {t}")
        pdf.ln(1)
    pdf.ln(3)

    # Messaggi Telegram
    print("[*] Recupero messaggi Telegram...")
    tg_msgs = get_telegram_messages()
    pdf_title(pdf, "ULTIMI MESSAGGI TELEGRAM")
    for ch, txt in tg_msgs:
        pdf_line(pdf, f"@{ch}: {txt}")
        pdf.ln(1)
    pdf.ln(3)

    # Indici finanziari
    print("[*] Recupero indici finanziari...")
    indices = get_market_indices()
    pdf_title(pdf, "INDICI FINANZIARI E MERCATI")

    sections = {
        "Indici Azionari USA": ["Nasdaq 100", "S&P 500", "Russell 2000"],
        "Valuta e Liquidita": ["DXY (Dollar Index)", "US Treasury 10Y"],
        "Indici Globali": ["MSCI World", "Hang Seng", "CSI 300 (Cina)"],
        "Crypto-Equities": ["MicroStrategy", "Coinbase", "Marathon Digital"],
        "S&P Digital Markets": ["Bitcoin (BTC-USD)", "Ethereum (ETH-USD)"],
    }

    index_map = {r[0]: r for r in indices}

    for section_name, names in sections.items():
        pdf.set_font("Helvetica", "B", 10)
        pdf_line(pdf, f"-- {section_name} --")
        pdf.set_font("Helvetica", "", 9)
        for name in names:
            row = index_map.get(name)
            if not row:
                continue
            if len(row) == 6:
                n, ticker, price, chg, trend, analysis = row
                if price is not None:
                    sign = "+" if chg >= 0 else ""
                    line1 = f"{n} ({ticker}): {price:,.2f}  |  {sign}{chg:.2f}%  [{trend}]"
                    line2 = f"   => {analysis}"
                    pdf_line(pdf, line1)
                    pdf_line(pdf, line2)
                else:
                    pdf_line(pdf, f"{n} ({ticker}): dati non disponibili")
            else:
                pdf_line(pdf, f"{name}: dati non disponibili")
            pdf.ln(1)
        pdf.ln(2)

    # Token trending
    print("[*] Recupero token trending da CoinGecko...")
    tokens = get_trending_tokens()
    pdf_title(pdf, "TOP 6 CRIPTOVALUTE CONSIGLIATE")
    if tokens:
        for n, s, r, sc in tokens:
            pdf_line(pdf, f"{n} ({s}) - Rischio: {risk_level(r)} - {duration(sc)}")
            pdf.ln(1)
    else:
        pdf_line(pdf, "Dati non disponibili (rate limit CoinGecko).")

    # Salva PDF
    filename = f"report_crypto_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    pdf.output(filename)
    print(f"\n[OK] Report generato: {filename}")
    return filename

# === MAIN ===

if __name__ == "__main__":
    print("=== Report Crypto Bot ===")
    print(f"Avviato il: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
    try:
        create_pdf()
    except Exception as e:
        print(f"\n[ERRORE] Errore durante l'esecuzione: {e}")
        import traceback
        traceback.print_exc()
    input("\nPremi INVIO per uscire...")

