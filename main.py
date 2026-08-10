import feedparser
import requests
import json
import os
from datetime import datetime

# Configurazione - Lista di feed da monitorare
MASTODON_FEEDS = [
    {
        "url": "https://norden.social/@jef.rss",
        "handle": "@jef"
    },
    {
        "url": "https://fosstodon.org/@underdarkGIS.rss",
        "handle": "@underdarkGIS@fosstodon.org"
    },
    {
        "url": "https://fosstodon.org/tags/qgis.rss",
        "handle": "#qgis"
    },
    {
        "url": "https://fosstodon.org/@qgis.rss",
        "handle": "@qgis@fosstodon.org"
    },
    {
        "url": "https://fosstodon.org/tags/qgisuc2026.rss",
        "handle": "#qgisuc2026"
    }
]

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
POSTS_FILE = "seen_posts.json"

def load_seen_posts():
    """Carica i post già visti da file (per tutti i feed)"""
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, "r") as f:
            return json.load(f)
    # Inizializza con una lista vuota per ogni feed
    return {feed["url"]: [] for feed in MASTODON_FEEDS}

def cleanup_old_posts(posts, days=7):
    """Rimuove i post più vecchi di N giorni per limitare la crescita del file"""
    cutoff_date = datetime.now() - __import__('datetime').timedelta(days=days)

    for feed_url in posts:
        # I link di Mastodon contengono l'ID del post alla fine
        # Es: https://mastodon.uno/@pigreco71/117064411555755509
        # Manteniamo solo i post recenti
        posts[feed_url] = posts[feed_url][-500:]  # Max 500 post per feed

    return posts

def save_seen_posts(posts):
    """Salva i post visti su file"""
    with open(POSTS_FILE, "w") as f:
        json.dump(posts, f, indent=2)

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
    """Controlla tutti i feed Mastodon e invia notifiche"""
    print(f"\n🔍 Controllo feed... ({datetime.now().strftime('%H:%M:%S')})")

    seen_posts = load_seen_posts()
    seen_posts = cleanup_old_posts(seen_posts)  # Pulisci i post vecchi
    total_new_posts = 0

    for feed_config in MASTODON_FEEDS:
        feed_url = feed_config["url"]
        handle = feed_config["handle"]

        try:
            # Fetch del feed
            feed = feedparser.parse(feed_url)

            if not feed.entries:
                print(f"⚠️ Feed {handle} vuoto o non raggiungibile")
                continue

            # Inizializza la lista per questo feed se non esiste
            if feed_url not in seen_posts:
                seen_posts[feed_url] = []

            new_posts_for_feed = []

            # Controlla i nuovi post (ordine inverso per cronologia)
            for entry in reversed(feed.entries):
                post_id = entry.link

                if post_id not in seen_posts[feed_url]:
                    new_posts_for_feed.append(post_id)
                    seen_posts[feed_url].append(post_id)
                    total_new_posts += 1

                    # Manda notifica
                    message = f"📌 Nuovo post da {handle}:\n\n{entry.link}"
                    send_telegram_message(message)

            if new_posts_for_feed:
                print(f"✨ {handle}: trovati {len(new_posts_for_feed)} nuovo/i post!")
            else:
                print(f"✓ {handle}: nessun nuovo post")

        except Exception as e:
            print(f"❌ Errore per {handle}: {e}")
            send_telegram_message(f"⚠️ Errore nel monitoraggio di {handle}: {str(e)}")

    # Salva i post aggiornati
    save_seen_posts(seen_posts)

    if total_new_posts > 0:
        print(f"\n✨ Totale: {total_new_posts} nuovo/i post!")
    else:
        print("\n✓ Nessun nuovo post da nessun feed")

def start_scheduler():
    """Esegue un singolo controllo (per GitHub Actions)"""
    print("🚀 Monitor Mastodon avviato!")
    print(f"📊 Feed monitorati ({len(MASTODON_FEEDS)}):")
    for feed_config in MASTODON_FEEDS:
        print(f"   - {feed_config['handle']}: {feed_config['url']}")
    print(f"💬 ID Telegram: {TELEGRAM_CHAT_ID}")

    # Un singolo controllo
    check_mastodon()
    print("\n✅ Controllo completato!")

if __name__ == "__main__":
    try:
        start_scheduler()
    except KeyboardInterrupt:
        print("\n⏸️ Monitor fermato")
