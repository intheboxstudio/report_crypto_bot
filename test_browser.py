from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# FIX: Aggiunge tutti i flag necessari per evitare blocchi anti-bot
options = Options()
options.add_argument("--headless=new")              # FIX: nuovo formato headless Chrome 112+
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

try:
    driver = webdriver.Chrome(options=options)
    # FIX: nasconde il flag webdriver dalla pagina
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    print("✅ ChromeDriver avviato correttamente!")
    driver.get("https://x.com")
    time.sleep(5)
    print(f"   Titolo pagina: {driver.title}")
    driver.quit()
    print("✅ Test completato con successo.")

except Exception as e:
    print(f"❌ Errore ChromeDriver: {e}")
    print()
    print("   Possibili cause:")
    print("   1. ChromeDriver non installato o non nel PATH")
    print("   2. Versione ChromeDriver diversa da Chrome installato")
    print("   3. Scarica la versione corretta da:")
    print("      https://googlechromelabs.github.io/chrome-for-testing/")

input("\nPremi INVIO per uscire...")
