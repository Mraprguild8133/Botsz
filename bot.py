import os
import time
import re
from urllib.parse import urljoin
from dotenv import load_dotenv
import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
import logging
import threading
from datetime import datetime, timedelta

# Import configuration
from config import config

# Configure logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ] if config.LOG_FILE else [logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

load_dotenv()

bot = telebot.TeleBot(config.TOKEN, parse_mode='HTML')
app = Flask(__name__)

# Global variables with thread safety
movie_list = []
real_dict = {}
data_lock = threading.Lock()
last_update = None
CACHE_DURATION = timedelta(minutes=config.CACHE_DURATION_MINUTES)

# Rate limiting
user_requests = {}

def is_rate_limited(user_id):
    """Check if user has exceeded rate limit"""
    now = time.time()
    if user_id in user_requests:
        user_requests[user_id] = [req_time for req_time in user_requests[user_id] if now - req_time < 60]
        if len(user_requests[user_id]) >= config.RATE_LIMIT_PER_MINUTE:
            return True
    else:
        user_requests[user_id] = []
    
    user_requests[user_id].append(now)
    return False

def sanitize_text(text):
    """Sanitize text for safe display"""
    if not text:
        return "Unknown"
    # Remove excessive whitespace and potentially harmful characters
    text = re.sub(r'[^\w\s\-\.\(\)\[\] ]', '', text)
    return ' '.join(text.split())

def should_refresh_data():
    """Check if data should be refreshed"""
    global last_update
    if last_update is None:
        return True
    return datetime.now() - last_update > CACHE_DURATION

@bot.message_handler(commands=['start'])
def start_command(message):
    """Handle /start command"""
    if is_rate_limited(message.from_user.id):
        bot.reply_to(message, config.RATE_LIMIT_MESSAGE)
        return

    text_message = config.START_MESSAGE

    keyboard = types.InlineKeyboardMarkup()
    for button in config.START_BUTTONS:
        keyboard.add(
            types.InlineKeyboardButton(
                text=button['text'],
                url=button['url']
            )
        )

    try:
        bot.send_photo(
            chat_id=message.chat.id,
            photo=config.START_IMAGE_URL,
            caption=text_message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        logger.info(f"Start command handled for user {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error sending start message: {e}")
        bot.reply_to(message, config.ERROR_MESSAGES['general'])

@bot.message_handler(commands=['view'])
def view_command(message):
    """Handle /view command"""
    if is_rate_limited(message.from_user.id):
        bot.reply_to(message, config.RATE_LIMIT_MESSAGE)
        return

    try:
        bot.send_message(message.chat.id, config.LOADING_MESSAGES['fetching_movies'])
        
        global movie_list, real_dict, last_update
        
        with data_lock:
            if should_refresh_data():
                movie_list, real_dict = tamilmv_scraper()
                last_update = datetime.now()
                logger.info("Data refreshed from website")
            else:
                logger.info("Using cached data")

        if not movie_list:
            bot.send_message(message.chat.id, config.ERROR_MESSAGES['no_movies'])
            return

        keyboard = make_keyboard(movie_list)

        bot.send_photo(
            chat_id=message.chat.id,
            photo=config.MOVIE_LIST_IMAGE_URL,
            caption=config.MOVIE_LIST_CAPTION,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        logger.info(f"View command handled for user {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error in view command: {e}")
        bot.reply_to(message, config.ERROR_MESSAGES['fetch_error'])

@bot.message_handler(commands=['help', 'about'])
def help_command(message):
    """Handle help and about commands"""
    bot.reply_to(message, config.HELP_MESSAGE, parse_mode='HTML')

@bot.message_handler(commands=['status'])
def status_command(message):
    """Check bot status"""
    global last_update
    status_text = config.STATUS_MESSAGE.format(
        last_update=last_update.strftime('%Y-%m-%d %H:%M:%S') if last_update else 'Never',
        movies_cached=len(movie_list),
        webhook_status='✅ Active' if config.WEBHOOK_URL else '❌ Inactive'
    )
    bot.reply_to(message, status_text, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """Handle inline keyboard callbacks"""
    try:
        global real_dict
        
        callback_data = call.data
        if callback_data == "refresh":
            bot.answer_callback_query(call.id, config.LOADING_MESSAGES['refreshing'])
            view_command(call.message)
            return
        
        index = int(callback_data)
        if 0 <= index < len(movie_list):
            movie_title = movie_list[index]
            if movie_title in real_dict and real_dict[movie_title]:
                for i, detail in enumerate(real_dict[movie_title]):
                    if i == 0:
                        bot.send_message(call.message.chat.id, detail)
                    else:
                        time.sleep(0.5)
                        bot.send_message(call.message.chat.id, detail)
                
                # Add refresh button
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton(
                    config.BUTTON_TEXTS['refresh'], 
                    callback_data="refresh"
                ))
                
                bot.send_message(
                    call.message.chat.id,
                    config.REFRESH_PROMPT,
                    reply_markup=keyboard
                )
            else:
                bot.answer_callback_query(call.id, config.ERROR_MESSAGES['no_details'])
        else:
            bot.answer_callback_query(call.id, config.ERROR_MESSAGES['invalid_selection'])
            
        logger.info(f"Callback handled for user {call.from_user.id}: {callback_data}")
        
    except ValueError:
        bot.answer_callback_query(call.id, config.ERROR_MESSAGES['invalid_data'])
    except Exception as e:
        logger.error(f"Error in callback: {e}")
        bot.answer_callback_query(call.id, config.ERROR_MESSAGES['general'])

def make_keyboard(movie_list):
    """Create inline keyboard for movie selection"""
    markup = types.InlineKeyboardMarkup()
    
    for key, value in enumerate(movie_list):
        display_text = value[:50] + "..." if len(value) > 50 else value
        markup.add(
            types.InlineKeyboardButton(
                text=f"🎬 {display_text}",
                callback_data=f"{key}"
            )
        )
    
    # Add refresh button at the bottom
    markup.add(types.InlineKeyboardButton(
        config.BUTTON_TEXTS['refresh_list'], 
        callback_data="refresh"
    ))
    
    return markup

def tamilmv_scraper():
    """Scrape movie data from TamilMV website"""
    headers = config.REQUEST_HEADERS

    movie_list = []
    real_dict = {}

    try:
        logger.info(f"Scraping data from {config.TAMILMV_URL}")
        response = requests.get(
            config.TAMILMV_URL, 
            headers=headers, 
            timeout=config.REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        temps = soup.find_all('div', {'class': config.SCRAPER_SELECTORS['movie_container']})

        if not temps:
            logger.warning("No movie elements found on the page")
            return [], {}

        for i in range(min(config.MAX_MOVIES, len(temps))):
            try:
                link_element = temps[i].find('a')
                if not link_element:
                    continue
                    
                title = sanitize_text(link_element.text)
                link = link_element.get('href')
                
                if not title or not link:
                    continue
                    
                # Make sure link is absolute
                if not link.startswith('http'):
                    link = urljoin(config.TAMILMV_URL, link)
                
                movie_list.append(title)
                logger.info(f"Found movie: {title}")

                # Get movie details with timeout
                movie_details = get_movie_details(link)
                real_dict[title] = movie_details
                
                # Small delay to be respectful to the server
                time.sleep(config.SCRAPER_DELAY)
                
            except Exception as e:
                logger.error(f"Error processing movie {i}: {e}")
                continue

        logger.info(f"Successfully scraped {len(movie_list)} movies")
        return movie_list, real_dict
        
    except requests.RequestException as e:
        logger.error(f"Network error while scraping: {e}")
        return [], {}
    except Exception as e:
        logger.error(f"Unexpected error in scraper: {e}")
        return [], {}

def get_movie_details(url):
    """Get detailed information for a specific movie"""
    try:
        response = requests.get(url, headers=config.REQUEST_HEADERS, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get movie title
        movie_title_element = soup.find('h1')
        movie_title = sanitize_text(movie_title_element.text if movie_title_element else "Unknown Title")

        # Find magnet links
        magnet_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('magnet:'):
                magnet_links.append(href)

        # Find torrent file links
        torrent_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.endswith('.torrent'):
                if not href.startswith('http'):
                    href = urljoin(config.TAMILMV_URL, href)
                torrent_links.append(href)

        movie_details = []
        
        # Create messages for each magnet-torrent pair
        for i, magnet in enumerate(magnet_links):
            torrent_link = torrent_links[i] if i < len(torrent_links) else None
            
            message = config.MOVIE_DETAIL_TEMPLATE.format(
                movie_title=movie_title,
                magnet_link=magnet,
                torrent_link=torrent_link,
                torrent_available=config.TORRENT_AVAILABLE_MESSAGE if torrent_link else config.TORRENT_UNAVAILABLE_MESSAGE,
                disclaimer=config.DISCLAIMER_MESSAGE
            )
            movie_details.append(message)

        # If no magnet links found, create a generic message
        if not movie_details:
            message = config.NO_LINKS_TEMPLATE.format(
                movie_title=movie_title,
                movie_url=url
            )
            movie_details.append(message)

        return movie_details
        
    except requests.RequestException as e:
        logger.error(f"Network error getting movie details: {e}")
        return [config.ERROR_MESSAGES['network_error']]
    except Exception as e:
        logger.error(f"Error getting movie details: {e}")
        return [config.ERROR_MESSAGES['details_error']]

@app.route('/')
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "telegram-bot",
        "timestamp": datetime.now().isoformat(),
        "movies_cached": len(movie_list),
        "last_update": last_update.isoformat() if last_update else None,
        "version": config.VERSION
    }, 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint for Telegram"""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Invalid content type', 415

@app.errorhandler(404)
def not_found(error):
    return {"error": "Endpoint not found"}, 404

@app.errorhandler(500)
def internal_error(error):
    return {"error": "Internal server error"}, 500

def main():
    """Main application entry point"""
    try:
        # Validate required environment variables
        if not config.TOKEN:
            raise ValueError("TOKEN environment variable is required")
        if not config.WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL environment variable is required")

        logger.info(f"Starting Telegram Bot v{config.VERSION}...")
        
        # Remove any previous webhook
        bot.remove_webhook()
        time.sleep(1)

        # Set webhook
        webhook_url = f"{config.WEBHOOK_URL}/webhook"
        bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")

        # Pre-load data
        logger.info("Pre-loading movie data...")
        global movie_list, real_dict, last_update
        movie_list, real_dict = tamilmv_scraper()
        last_update = datetime.now()

        # Start Flask app
        logger.info(f"Starting Flask server on port {config.PORT}")
        app.run(
            host=config.HOST, 
            port=config.PORT, 
            debug=config.DEBUG
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

if __name__ == "__main__":
    main()
