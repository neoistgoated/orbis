import discord
import os
import re
import json
from dotenv import load_dotenv

# --- Configuration Loading ---
# Load environment variables (like DISCORD_TOKEN) from .env file
load_dotenv()

# Load configuration settings from config.json
CONFIG_PATH = "config.json"
try:
    with open(CONFIG_PATH, 'r') as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    print(f"error: configuration file '{CONFIG_PATH}' not found. please ensure config.json exists.")
    exit(1)

# Retrieve settings, using defaults as a fallback
# CAPS_THRESHOLD defaults to 0.6 (60% or more capital letters is 'shouting')
CAPS_THRESHOLD = CONFIG.get("caps_threshold", 0.6)
# MIN_ALPHA_CHARS ensures we only check messages with at least 5 letters
MIN_ALPHA_CHARS = CONFIG.get("min_alpha_chars", 5)

# Define the intents required by the bot
# Message Content Intent is required to read message content
intents = discord.Intents.default()
intents.message_content = True

# Regex pattern to detect common Unicode emojis (covers a broad range)
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
    "\U0001F680-\U0001F6FF"  # Transport and Map Symbols
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U00002702-\U000027B0"  # Dingbats
    "\U000024C2-\U0001F251"  # Miscellaneous symbols
    "]+", flags=re.UNICODE
)

def contains_too_much_caps(text):
    """
    Checks if the message is predominantly in uppercase, using the threshold 
    defined in config.json.
    """
    # Count uppercase characters and total alphabetic characters
    caps_count = sum(1 for char in text if char.isupper())
    alpha_count = sum(1 for char in text if char.isalpha())

    # Only check if there are a reasonable amount of letters (e.g., 5 or more)
    if alpha_count >= MIN_ALPHA_CHARS and caps_count / alpha_count > CAPS_THRESHOLD:
        return True
    return False

def contains_emojis(text):
    """
    Checks for Unicode emojis or Discord custom/animated emojis.
    """
    # 1. Check for standard Unicode emojis
    if EMOJI_PATTERN.search(text):
        return True
    
    # 2. Check for Discord custom emojis, e.g., <:name:id> or <a:name:id>
    # This regex is strict about Discord's standard format
    if re.search(r"<[a]?:[a-zA-Z0-9_]+:[0-9]+>", text):
        return True

    return False

class OrbisClient(discord.Client):
    async def on_ready(self):
        # Orbis only logs in in lowercase
        print(f'logged in as {self.user.name.lower()} ({self.user.id}).')
        print('orbis is now operational.')

    async def on_message(self, message):
        # ignore messages from itself
        if message.author == self.user:
            return
        
        # orbis only monitors text channels
        if not isinstance(message.channel, discord.TextChannel):
            return

        content = message.content
        
        # --- check for capital letters ---
        if contains_too_much_caps(content):
            await message.channel.send(
                f"ugh, {message.author.mention}, why are you shouting? it's rude. please use lowercase."
            )
            return

        # --- check for emojis ---
        if contains_emojis(content):
            await message.channel.send(
                f"i see those silly little pictures, {message.author.mention}. i find them deeply unserious. please desist."
            )
            return

        # --- simple response if rules are followed ---
        # orbis only responds if directly mentioned, to avoid spamming every message
        if self.user.mentioned_in(message):
            await message.channel.send(
                f"yes, {message.author.mention}. i'm here. and keep your voice down."
            )


if __name__ == "__main__":
    # Load the bot token from the environment, which was loaded by load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if not TOKEN or TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("error: 'discord_token' environment variable is not set or is using the placeholder value in .env.")
        print("please update the .env file with your bot's actual token.")
    else:
        # Initializing the client with the defined intents
        client = OrbisClient(intents=intents)
        # client.run() requires the token to be a string
        client.run(str(TOKEN))
