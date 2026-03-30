from telethon import TelegramClient
import asyncio

# ✅ Dati di accesso Telegram
api_id = 26134051
api_hash = 'b1855096745f810ea48fab762c63346c'

# FIX: Metti qui il percorso COMPLETO dove vuoi salvare la sessione
# Esempio: r'C:\Users\TuoNome\Desktop\CryptoBot\session'
# IMPORTANTE: deve corrispondere al SESSION_PATH in report_crypto.py
SESSION_PATH = 'session'

async def login():
    client = TelegramClient(SESSION_PATH, api_id, api_hash)
    try:
        # FIX: start() con phone evita blocchi su terminali non interattivi
        await client.start()

        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"✅ Sessione creata con successo!")
            print(f"   Account: {me.first_name} (@{me.username})")
            print(f"   File sessione salvato come: {SESSION_PATH}.session")
            print(f"\n   Ora puoi avviare avvia_report.bat")
        else:
            print("❌ Autenticazione non completata.")
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.disconnect()

if __name__ == "__main__":
    print("=== Login Telegram ===")
    print("Inserisci il tuo numero di telefono quando richiesto (es: +39XXXXXXXXXX)\n")
    asyncio.run(login())
    input("\nPremi INVIO per uscire...")
