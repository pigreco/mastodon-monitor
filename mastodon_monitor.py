import feedparser
import requests
import schedule
import time
import json
import os
from datetime import datetime

# Configurazione
MASTODON_FEED = "https://norden.social/@jef.rss"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
POSTS_FILE = "seen_posts.json"

def load_seen_posts():
    """Carica i post già visti da file"""
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, "r") as f:
            return json.load(f)
    return []

def save_seen_posts(posts):
    """Salva i post visti su file"""
    with open(POSTS_FILE, "w") as f:
        json.dump(posts, f)

def send_telegram_message(message):
    """Invia un messaggio su Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print(f"✅ Messaggio inviato: {message[:50]}...")
        else:
            print(f"❌ Errore Telegram: {response.text}")
    except Exception as e:
        print(f"❌ Errore invio: {e}")

def check_mastodon():
    """Controlla feed Mastodon e invia notifiche"""
    try:
        print(f"\n🔍 Controllo feed... ({datetime.now().strftime('%H:%M:%S')})")
        
        # Fetch del feed
        feed = feedparser.parse(MASTODON_FEED)
        
        if not feed.entries:
            print("⚠️ Feed vuoto o non raggiungibile")
            return
        
        seen_posts = load_seen_posts()
        new_posts = []
        
        # Controlla i nuovi post (ordine inverso per cronologia)
        for entry in reversed(feed.entries):
            post_id = entry.link
            
            if post_id not in seen_posts:
                new_posts.append(post_id)
                seen_posts.append(post_id)
                
                # Manda notifica
                message = f"📌 Nuovo post da @jef:\n\n{entry.link}"
                send_telegram_message(message)
        
        # Salva i post aggiornati
        save_seen_posts(seen_posts)
        
        if new_posts:
            print(f"✨ Trovati {len(new_posts)} nuovo/i post!")
        else:
            print("✓ Nessun nuovo post")
            
    except Exception as e:
        print(f"❌ Errore: {e}")
        send_telegram_message(f"⚠️ Errore nel monitoraggio: {str(e)}")

def start_scheduler():
    """Avvia lo scheduler"""
    print("🚀 Monitor Mastodon avviato!")
    print(f"📊 Feed: {MASTODON_FEED}")
    print(f"⏱️ Controllo ogni 30 minuti")
    print(f"💬 ID Telegram: {TELEGRAM_CHAT_ID}")
    
    # Primo controllo subito
    check_mastodon()
    
    # Scheduler ogni 30 minuti
    schedule.every(30).minutes.do(check_mastodon)
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    try:
        start_scheduler()
    except KeyboardInterrupt:
        print("\n⏸️ Monitor fermato")
