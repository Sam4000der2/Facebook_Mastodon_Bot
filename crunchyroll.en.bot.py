import feedparser
from mastodon import Mastodon
from tempfile import NamedTemporaryFile
import re
import os
import requests
import time
import datetime
from dateutil.parser import parse
from bs4 import BeautifulSoup

# Customizable Variables
api_base_url = 'https://sakurajima.moe'  # The base URL of your Mastodon instance
access_token = 'api_key' # Your access token
feed_url = 'https://fetchrss.com/rss/6608692efac5834576331a82660868f40f8d3458ab64bde2.xml'  # Insert RSS feed URL here, I used fetchrss.
    
def extract_images_from_content(content):
    # Parse the content to extract image URLs
    soup = BeautifulSoup(content, 'html.parser')
    image_urls = []
    for img_tag in soup.find_all('img'):
        image_urls.append(img_tag['src'])
    return image_urls
    
def fetch_feed_entries(feed_url):
    # Parse the RSS feed and extract the entries
    feed = feedparser.parse(feed_url)
    entries = feed.entries
    return entries

def post_tweet(mastodon, message):
    # Post the tweet on Mastodon
    message_cut = truncate_text(message)
    mastodon.status_post(message_cut, visibility='public')

def post_tweet_with_images(mastodon, message, image_urls):
    # Post the message with one or more images on Mastodon
    message_cut = truncate_text(message)
    
    # Upload the images and get the media IDs
    media_ids = []
    image_paths = []
    
    for image_url in image_urls:
        with NamedTemporaryFile(delete=False) as tmp_file:
            response = requests.get(image_url)
            tmp_file.write(response.content)
            image_path = tmp_file.name

        with open(image_path, 'rb') as image_file:
            media_info = mastodon.media_post(image_file, description="Source: Crunchyroll Facebook Page. Unfortunately, no automatic image description available.", mime_type='image/jpeg')
            media_ids.append(media_info['id'])
            
    # Post the message with the attached images
    mastodon.status_post(message_cut, media_ids=media_ids, visibility='public')
    
     # Delete temporary files
    for image_path in image_paths:
        os.unlink(image_path)

def truncate_text(text):
    # Check if the text is longer than 500 characters
    if len(text) > 500:
        return text[:500]
    else:
        return text

def clean_content_keep_links(content):
    # Remove image tags, keep link tags
    cleaned_content = re.sub(r'<img\s+[^>]*>', '', content)
    # Remove all other HTML tags
    cleaned_content = re.sub(r'<[^<]+?>', '', cleaned_content).strip()
    # Remove line breaks and spaces
    cleaned_content = cleaned_content.replace('\n', ' ').replace('\r', '')
    # Remove double spaces
    cleaned_content = ' '.join(cleaned_content.split())
    return cleaned_content


def main(feed_entries):
    mastodon = Mastodon(
        access_token=access_token,
        api_base_url=api_base_url
    )
    # List to store the entry_ids
    saved_entry_ids = []
    
    # Open the file to read the saved entry_ids
    try:
        with open("Mastodon.crunchy.en.bot.dat", "r") as file:
            for line in file:
                saved_entry_ids.append(line.strip())
    except FileNotFoundError:
        # File not found, create a new one
        with open("Mastodon.crunchy.en.bot.dat", "w") as file:
            pass

    entry_found = False
    for entry in feed_entries:
        
        title = entry.get('title', '')
        scr_link = entry.get('link', '')
        content = entry.get('description', '')
        updated = entry.get('published', '')
        creator = entry.get('author', '')
        #media_content = entry.get('media_content', None)
        
        image_urls = extract_images_from_content(content)
        #media_url = None
        image_found = False
        
        if image_urls:
           image_found = True 
        
        # Extract the numbers at the end of the URL
        match = re.search(r'\d+$', scr_link)
        if match:
            entry_id = match.group()
            #entry_id = ""
        else: 
            entry_id = ""
        
        # Check if the entry_id is already saved
        if entry_id not in saved_entry_ids:
            
            entry_found = True
        
            # Parse timestamp
            posted_time_utc = parse(updated)

            # Check if the timezone is Daylight Saving Time (DST)
            is_dst = bool(datetime.datetime.now().astimezone().dst())

            # Set local timezone (here using Berlin as an example)
            local_timezone = datetime.timezone(datetime.timedelta(hours=8 if is_dst else 7))  # CEST (UTC+2) or CET (UTC+1)
            utc_timezone = datetime.timezone(datetime.timedelta(hours=0 if is_dst else 0))  # CEST (UTC+2) or CET (UTC+1)

            # Convert timestamp to local timezone
            posted_time_local = posted_time_utc.astimezone(local_timezone)
            posted_time_local_utc = posted_time_utc.astimezone(utc_timezone)

            # Define desired format for date and time
            desired_format = "%m/%d/%Y %H:%M"
            desired_format_utc = "%d.%m.%Y %H:%M"

            # Output timestamp in desired format
            posted_time_utc = posted_time_local_utc.strftime(desired_format_utc)
            posted_time = posted_time_local.strftime(desired_format)
            
            clean_content = clean_content_keep_links(content)
            clean_content = clean_content.replace("(Feed generated with FetchRSS)", "") 
            message = f"{clean_content} \n\n#crunchyroll #Anime\n\n{posted_time} (PT)\n{posted_time_utc} (UTC)\n\nLink to original post: {scr_link}"

            if image_found:
                #print (image_urls)
                #print (message)
                post_tweet_with_images(mastodon, message, image_urls)
            else:
                #print(message)
                post_tweet(mastodon, message)
                
            # Add the entry_id to the list of saved entry_ids
            saved_entry_ids.append(entry_id)
            
            # Make sure that only the latest 5 entries are kept
            if len(saved_entry_ids) > 10:
                saved_entry_ids = saved_entry_ids[-5:]
            # Open the file in write mode (w for write)
            with open('Mastodon.crunchy.en.bot.dat', 'w') as file:
                # Write each entry_id followed by a line break in the file
                for entry_id in saved_entry_ids:
                    file.write(str(entry_id) + '\n')
            time.sleep(1500)
        
    if entry_found != True:    
        time.sleep(9000)
    


# Main program (where the bot is invoked)
if __name__ == "__main__":
    while True: #infinite loop
        feed_entries = fetch_feed_entries(feed_url)
        main(feed_entries)
