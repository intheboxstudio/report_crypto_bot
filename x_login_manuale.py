"""
Salva i cookie di X usando Brave (dove sei gia loggato).
Esegui UNA SOLA VOLTA, poi il bot usa i cookie automaticamente.
"""
import json
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

COOKIE_FILE = 'x_cookies.json'

# Percorso Brave
BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
BRAVE_PROFILE = os.path.expandvars(r'%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data')

print("=== Salvataggio Cookie X tramite Brave ===")
print()

if not os.path.exists(BRAVE_PATH):
    print("[ERRORE] Brave non trovato in:", BRAVE_PATH)
    print("         Controlla che Brave sia installato.")
    input("\nPremi INVIO per uscire...")
    exit()

opts = Options()
opts.binary_location = BRAVE_PATH
opts.add_argument(f"--user-data-dir={BRAVE_PROFILE}")
opts.add_argument("--profile-directory=Default")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--disable-blink-features=AutomationControlled")
opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
opts.add_experimental_option("useAutomationExtension", False)

print("IMPORTANTE: chiudi Brave completamente prima di procedere!")
print()
input("Premi INVIO quando Brave e chiuso...")
print()

try:
    print("Apro Brave con il tuo profilo...")
    driver = webdriver.Chrome(options=opts)
    driver.get("https://x.com/home")
    time.sleep(8)

    current = driver.current_url
    print(f"URL attuale: {current}")

    if "login" not in current and "x.com" in current:
        cookies = driver.get_cookies()
        with open(COOKIE_FILE, 'w') as f:
            json.dump(cookies, f)
        print(f"[OK] Cookie salvati con successo: {len(cookies)} cookie")
        print(f"[OK] File: {COOKIE_FILE}")
        print("[OK] Da ora il bot legge X automaticamente!")
    else:
        print("[WARN] Non risulti loggato a X su Brave.")
        print("       Accedi a X su Brave manualmente, poi riesegui questo script.")

    driver.quit()

except Exception as e:
    err = str(e)
    if "user data directory is already in use" in err.lower():
        print("[ERRORE] Brave e ancora aperto! Chiudilo dal Task Manager e riprova.")
    elif "cannot find" in err.lower() or "binary" in err.lower():
        print("[ERRORE] ChromeDriver non compatibile con Brave.")
        print("         Scarica ChromeDriver dalla stessa versione di Brave.")
        print("         Controlla la versione Brave su: brave://settings/help")
    else:
        print(f"[ERRORE] {err[:300]}")

input("\nPremi INVIO per uscire...")
