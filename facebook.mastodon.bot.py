import feedparser
from mastodon import Mastodon
from tempfile import NamedTemporaryFile
import re
import os
import requests
import time
import datetime
from dateutil.parser import parse

# Customizable Variables
api_base_url = 'yourinstance.social'  # The base URL of your Mastodon instance
access_token = 'yourTOKEN' # Your access token
feed_url = 'http://fetchrss.com/...'  # Insert RSS feed URL here, I used fetchrss.
    
def fetch_feed_entries(feed_url):
    # Parse the RSS feed and extract the entries
    feed = feedparser.parse(feed_url)
    entries = feed.entries
    return entries

def post_tweet(mastodon, message):
    # Post the tweet on Mastodon
    message_cut = truncate_text(message)
    mastodon.status_post(message_cut, visibility='private')

def post_tweet_with_images(mastodon, message, image_url_string):
    # Post the message with one or more images on Mastodon
    message_cut = truncate_text(message)
    
    # Upload the images and get the media IDs
    media_ids = []
    
    with NamedTemporaryFile(delete=False) as tmp_file:
            response = requests.get(image_url_string)
            tmp_file.write(response.content)
            image_path = tmp_file.name

    with open(image_path, 'rb') as image_file:
                media_info = mastodon.media_post(image_file, description="Source: Crunchyroll Facebook Page. Unfortunately, no automatic image description available.", mime_type='image/jpeg')
                media_ids.append(media_info['id'])
    # Post the message with the attached images
    mastodon.status_post(message_cut, media_ids=media_ids, visibility='private')
    
    # Delete temporary file
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
        with open("facebook.mastodon.bot.dat", "r") as file:
            for line in file:
                saved_entry_ids.append(line.strip())
    except FileNotFoundError:
        # File not found, create a new one
        with open("facebook.mastodon.bot.dat", "w") as file:
            pass

    for entry in feed_entries:
        title = str(entry.get('title', ''))
        content = entry.get('content', '')
        author = str(entry.get('author', ''))
        updated = str(entry.get('updated', ''))
        scr_link = str(entry.get('link', ''))
        image_url = entry.get('media_content', '')
        
        # Extract the numbers at the end of the URL
        match = re.search(r'\d+$', scr_link)
        if match:
            entry_id = match.group()
        else: 
            entry_id = ""
        
        # Check if the entry_id is already saved
        if entry_id not in saved_entry_ids:
        
            # Parse timestamp
            posted_time_utc = parse(updated)

            # Check if the timezone is Daylight Saving Time (DST)
            is_dst = bool(datetime.datetime.now().astimezone().dst())

            # Set local timezone (here using Berlin as an example)
            local_timezone = datetime.timezone(datetime.timedelta(hours=2 if is_dst else 1))  # CEST (UTC+2) or CET (UTC+1)

            # Convert timestamp to local timezone
            posted_time_local = posted_time_utc.astimezone(local_timezone)

            # Define desired format for date and time
            desired_format = "%d.%m.%Y %H:%M"

            # Output timestamp in desired format
            posted_time = posted_time_local.strftime(desired_format)
            
            image_found = False
            
            if content:  # Check if image_url is not empty
                content_string = content[0].get('value', '')  # Extract the URL from the first element of the list
            else:
                content_string = ""
            
            if image_url:  # Check if image_url is not empty
                image_url_string = image_url[0].get('url', '')  # Extract the URL from the first element of the list
                image_found = True

                
            clean_content = clean_content_keep_links(content_string)
            clean_content = clean_content.replace("(Feed generated with FetchRSS)", "") 
            message = f"{clean_content} \n\n #YOURHASHTAGS \n\n{posted_time}\n\nLink to original post: {scr_link}"

            if image_found:
                #print (images)
                #print (message)
                post_tweet_with_images(mastodon, message, image_url_string)
            else:
                #print(message)
                post_tweet(mastodon, message)
                
            # Add the entry_id to the list of saved entry_ids
            saved_entry_ids.append(entry_id)
            
            # Stelle sicher, dass nur die neuesten 5 Einträge behalten werden
            if len(saved_entry_ids) > 5:
                saved_entry_ids = saved_entry_ids[-5:]
    
    # Open the file in write mode (w for write)
    with open('Mastodon.crunchy.bot.dat', 'w') as file:
        # Write each entry_id followed by a line break in the file
        for entry_id in saved_entry_ids:
            file.write(str(entry_id) + '\n')
    
    time.sleep(900)

# Main program (where the bot is invoked)
if __name__ == "__main__":
    while True: #infinite loop
        feed_entries = fetch_feed_entries(feed_url)
        main(feed_entries)
