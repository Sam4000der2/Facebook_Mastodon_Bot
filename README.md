# Facebook_Mastodon_Bot

## Overview:
This script allows you to mirror content from a Facebook page to Mastodon using an RSS feed. It posts updates from the specified Facebook page to your Mastodon instance automatically.

## How to Use:
1. **Installation:**
   - Make sure you have Python installed on your system.
   - Install the required dependencies by running:
     ```
     pip install -r requirements.txt
     ```

2. **Configuration:**
   - Open the script in a text editor.
   - Update the customizable variables section with your Mastodon instance URL, access token, and RSS feed URL.
   - Customize the hashtags and any other message formatting as needed.
   
3. **Execution:**
   - Run the script by executing the following command in your terminal:
     ```
     python script_name.py
     ```
   - Replace `script_name.py` with the name of the script file.
   
4. **Post Visibility and Hashtags:**
   - Once the script is functioning correctly, consider adjusting the Mastodon post visibility (e.g., public, unlisted, private) to suit your needs.
   - You can also add your own hashtags to the message for better categorization and visibility.

5. **Running as a Service:**
   - If you want the bot to run continuously, you can set it up as a service on Linux.
   - Refer to your distribution's documentation for instructions on setting up a service, and configure it to run the script automatically on system startup.

6. **Enjoy:**
   - The script will now automatically fetch updates from the specified Facebook page and post them to your Mastodon instance.
