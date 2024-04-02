import feedparser
from mastodon import Mastodon
from tempfile import NamedTemporaryFile
import re
import os
import requests
import time
import datetime
from dateutil.parser import parse

# Anpassbare Variablen
api_base_url = 'https://mstdn.animexx.de'  # Die Basis-URL Ihrer Mastodon-Instanz
access_token = 'api_key' #Ihr Access-Token
feed_url = 'http://fetchrss.com/rss/6607f2e1d3469f6e5c14a2e26607f1c23da0c10d47218b12.atom'  # URL des RSS-Feeds hier einfügen
    
def fetch_feed_entries(feed_url):
    # Parse den RSS-Feed und extrahiere die Einträge
    feed = feedparser.parse(feed_url)
    entries = feed.entries
    return entries

def post_tweet(mastodon, message):
    # Veröffentliche den Tweet auf Mastodon
    message_cut = truncate_text(message)
    mastodon.status_post(message_cut, visibility='public')

def post_tweet_with_images(mastodon, message, image_url_string):
    # Veröffentliche den Beitrag mit einem oder mehreren Bildern auf Mastodon
    message_cut = truncate_text(message)
    
    # Lade die Bilder hoch und erhalte die Media-IDs
    media_ids = []
    
    with NamedTemporaryFile(delete=False) as tmp_file:
            response = requests.get(image_url_string)
            tmp_file.write(response.content)
            image_path = tmp_file.name

    with open(image_path, 'rb') as image_file:
                media_info = mastodon.media_post(image_file, description="Quelle: Crunchyroll Facebook Seite. Leider keine automatische Bildbeschreigung möglich", mime_type='image/jpeg')
                media_ids.append(media_info['id'])
    # Veröffentliche den Beitrag mit den angehängten Bildern
    mastodon.status_post(message_cut, media_ids=media_ids, visibility='public')
    
    # Temporäre Datei löschen
    os.unlink(image_path)

def truncate_text(text):
    # Prüfe, ob der Text länger als 500 Zeichen ist
    if len(text) > 500:
        return text[:500]
    else:
        return text

def clean_content_keep_links(content):
    # Entferne Bilder-Tags, behalte Links-Tags
    cleaned_content = re.sub(r'<img\s+[^>]*>', '', content)
    # Entferne alle anderen HTML-Tags
    cleaned_content = re.sub(r'<[^<]+?>', '', cleaned_content).strip()
    # Entferne Zeilenumbrüche und Leerzeichen
    cleaned_content = cleaned_content.replace('\n', ' ').replace('\r', '')
    # Entferne doppelte Leerzeichen
    cleaned_content = ' '.join(cleaned_content.split())
    return cleaned_content


def main(feed_entries):
    mastodon = Mastodon(
        access_token=access_token,
        api_base_url=api_base_url
    )
    # Liste zum Speichern der entry_ids
    saved_entry_ids = []
    
    # Öffne die Datei zum Lesen der gespeicherten entry_ids
    try:
        with open("Mastodon.crunchy.bot.dat", "r") as file:
            for line in file:
                saved_entry_ids.append(line.strip())
    except FileNotFoundError:
        # Datei nicht gefunden, erstelle eine neue
        with open("Mastodon.crunchy.bot.dat", "w") as file:
            pass
            
   #print(saved_entry_ids)
    entry_found = False
    for entry in feed_entries:
        title = str(entry.get('title', ''))
        content = entry.get('content', '')
        author = str(entry.get('author', ''))
        updated = str(entry.get('updated', ''))
        scr_link = str(entry.get('link', ''))
        image_url = entry.get('media_content', '')
        
        # Extrahiere die Zahlen am Ende der URL
        match = re.search(r'\d+$', scr_link)
        if match:
            entry_id = match.group()
        else: 
            entry_id = ""
        
        # Prüfe, ob die entry_id bereits gespeichert ist
        if entry_id not in saved_entry_ids:
            
            entry_found = True
            
            # Zeitstempel parsen
            posted_time_utc = parse(updated)

            # Prüfen, ob die Zeitzone Sommerzeit (DST) ist
            is_dst = bool(datetime.datetime.now().astimezone().dst())

            # Lokale Zeitzone festlegen (hier als Beispiel Berlin)
            local_timezone = datetime.timezone(datetime.timedelta(hours=2 if is_dst else 1))  # MESZ (UTC+2) oder MEZ (UTC+1)

            # Zeitstempel in lokale Zeitzone konvertieren
            posted_time_local = posted_time_utc.astimezone(local_timezone)

            # Gewünschtes Format für Datum und Uhrzeit definieren
            desired_format = "%d.%m.%Y %H:%M"

            # Zeitstempel im gewünschten Format ausgeben
            posted_time = posted_time_local.strftime(desired_format)
            
            bild_gefunden = False
            
            if content:  # Überprüfen, ob image_url nicht leer ist
                content_string = content[0].get('value', '')  # Extrahiere die URL aus dem ersten Element der Liste
            else:
                content_string = ""
            
            if image_url:  # Überprüfen, ob image_url nicht leer ist
                image_url_string = image_url[0].get('url', '')  # Extrahiere die URL aus dem ersten Element der Liste
                bild_gefunden = True

                
            clean_content = clean_content_keep_links(content_string)
            clean_content = clean_content.replace("(Feed generated with FetchRSS)", "") 
            message = f"{clean_content} \n\n #crunchyroll #Crunchyroll_de #AnimeDe #AnimeGer \n\n{posted_time}\n\nLink zum Orginalpost: {scr_link}"

            if bild_gefunden:
                #print (images)
                #print (message)
                post_tweet_with_images(mastodon, message, image_url_string)
            else:
                #print(message)
                post_tweet(mastodon, message)
                
            #Füge die entry_id zur Liste der gespeicherten entry_ids hinzu
            saved_entry_ids.append(entry_id)
            
            # Stelle sicher, dass nur die neuesten 5 Einträge behalten werden
            if len(saved_entry_ids) > 5:
                saved_entry_ids = saved_entry_ids[-5:]
            
        
        time.sleep(1500)
        
    if entry_found:
        # Öffne die Datei im Schreibmodus (w für write)
        with open('Mastodon.crunchy.bot.dat', 'w') as file:
            # Schreibe jede entry_id gefolgt von einem Zeilenumbruch in die Datei
            for entry_id in saved_entry_ids:
                file.write(str(entry_id) + '\n')
    else:
        time.sleep(9000)

    
# Hauptprogramm (z.B. wo der Bot aufgerufen wird)
if __name__ == "__main__":
    while True:  # Endlosschleife
        feed_entries = fetch_feed_entries(feed_url)
        main(feed_entries)
