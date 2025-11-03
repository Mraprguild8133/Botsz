# config.py
import os
import logging
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot Configuration
    TOKEN = os.getenv('TOKEN')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 3000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Scraper Configuration
    TAMILMV_URL = os.getenv('TAMILMV_URL', 'https://www.1tamilmv.boo')
    MAX_MOVIES = int(os.getenv('MAX_MOVIES', 15))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    CACHE_DURATION_MINUTES = int(os.getenv('CACHE_DURATION_MINUTES', 10))
    SCRAPER_DELAY = float(os.getenv('SCRAPER_DELAY', 1.0))
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 5))
    
    # Logging Configuration
    LOG_LEVEL = getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.getenv('LOG_FILE', 'bot.log')
    
    # Request Headers
    REQUEST_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # Scraper Selectors
    SCRAPER_SELECTORS = {
        'movie_container': 'ipsType_break ipsContained',
    }
    
    # Messages
    START_MESSAGE = """<b>Hello 👋</b>

<blockquote><b>🎬 Get latest Movies from 1Tamilmv</b></blockquote>

⚙️ <b>How to use me??</b> 🤔

✯ Please enter /view command and you'll get magnet link as well as link to torrent file 😌

<blockquote><b>🔗 Share and Support 💝</b></blockquote>"""
    
    START_IMAGE_URL = 'https://envs.sh/gcg.jpg'
    MOVIE_LIST_IMAGE_URL = 'https://envs.sh/gcg.jpg'
    
    START_BUTTONS = [
        {'text': '🔗 GitHub 🔗', 'url': 'https://github.com/Mraprguild'},
        {'text': '⚡ Powered By', 'url': 'https://t.me/Sathishkumar33'}
    ]
    
    MOVIE_LIST_CAPTION = """<b><blockquote>🔗 Select a Movie from the list 🎬</blockquote></b>\n\n🔘 Please select a movie:"""
    
    LOADING_MESSAGES = {
        'fetching_movies': '<b>🎬 Fetching latest movies... Please wait ⏰</b>',
        'refreshing': '🔄 Refreshing...'
    }
    
    ERROR_MESSAGES = {
        'general': '❌ Sorry, I encountered an error. Please try again later.',
        'no_movies': '❌ Sorry, couldn\'t fetch movies at the moment. Please try again later.',
        'fetch_error': '❌ Sorry, I encountered an error while fetching movies.',
        'no_details': '❌ No details available for this movie',
        'invalid_selection': '❌ Invalid selection',
        'invalid_data': '❌ Invalid callback data',
        'network_error': '❌ Network error fetching details for this movie.',
        'details_error': '❌ Error fetching details for this movie.'
    }
    
    RATE_LIMIT_MESSAGE = '⏳ Please wait a moment before making another request.'
    
    HELP_MESSAGE = """
<b>🤖 Bot Commands:</b>

/start - Start the bot
/view - View latest movies
/help - Show this help message
/about - About this bot
/status - Check bot status

<b>⚠️ Note:</b>
- Please use the bot responsibly
- Don't spam commands
- Movies are fetched from 1TamilMV
"""
    
    STATUS_MESSAGE = """
<b>🤖 Bot Status:</b>

✅ <b>Online</b>
🕒 <b>Last Update:</b> {last_update}
💾 <b>Movies Cached:</b> {movies_cached}
🔗 <b>Webhook:</b> {webhook_status}
"""
    
    BUTTON_TEXTS = {
        'refresh': '🔄 Refresh List',
        'refresh_list': '🔄 Refresh'
    }
    
    REFRESH_PROMPT = '🔄 Want to see the latest movies again?'
    
    # Movie Details Templates
    MOVIE_DETAIL_TEMPLATE = """
<b>📂 Movie Title:</b>
<blockquote>{movie_title}</blockquote>

🧲 <b>Magnet Link:</b>
<pre>{magnet_link}</pre>

{torrent_available}

⚠️ <i>{disclaimer}</i>
"""
    
    TORRENT_AVAILABLE_MESSAGE = '📥 <b>Download Torrent:</b>\n<a href="{torrent_link}">🔗 Click Here to Download Torrent File</a>'
    TORRENT_UNAVAILABLE_MESSAGE = '📥 <b>Torrent File:</b> Not Available'
    DISCLAIMER_MESSAGE = 'Use with caution and respect copyright laws'
    
    NO_LINKS_TEMPLATE = """
<b>📂 Movie Title:</b>
<blockquote>{movie_title}</blockquote>

❌ <b>No download links available for this movie.</b>

<i>Try visiting the website directly:</i>
<a href="{movie_url}">🌐 Visit Movie Page</a>
"""
    
    # Version
    VERSION = '1.0.0'

# Create config instance
config = Config()
