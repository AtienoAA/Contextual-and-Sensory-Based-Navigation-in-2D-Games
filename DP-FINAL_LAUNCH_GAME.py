import random
import math  
import pygame
from pygame.locals import *
from pygame import mixer
import pickle
import os
import sys
from os import path
import ctypes
import sqlite3

def init_database():
    """Initialize the SQLite database and create tables if they don't exist"""
    try:
        conn = sqlite3.connect(resource_path('game_data.db'))
        cursor = conn.cursor()
        
        # Create table for player progress
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT DEFAULT 'Player',
                level INTEGER DEFAULT 1,
                score INTEGER DEFAULT 0,
                play_time INTEGER DEFAULT 0, 
                last_saved TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create table for high scores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS high_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT,
                score INTEGER,
                level INTEGER,
                date_achieved TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create table for game settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                music_enabled INTEGER DEFAULT 1,
                sfx_enabled INTEGER DEFAULT 1,
                volume REAL DEFAULT 0.5,
                controls_shown INTEGER DEFAULT 1
            )
        ''')
        
        # Insert default settings if none exist
        cursor.execute('SELECT COUNT(*) FROM game_settings')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO game_settings DEFAULT VALUES')
        
        conn.commit()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".") # Or os.path.dirname(__file__) for dev
    
    return os.path.join(base_path, relative_path)

# PYGAME INITIALIZATION 
if os.name == 'nt':  # Windows only
    try:
        # Set DPI awareness to handle 150% scaling
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        try:
            # Fallback for older Windows versions
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass

# Initialize pygame and mixer
pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()

# Initialize database
init_database()

# UI Layout Constants (Add these)
UI_LEFT_MARGIN = 100    # Increased from 70 to push level further right
UI_RIGHT_MARGIN = 100   # Increased from 70 to push settings further left 
UI_TOP_MARGIN = 50
LEVEL_TO_MONEY_SPACE = 40  # Increased spacing between level and money

# Screen setup
screen_width = 800 # 70% of 1920
screen_height = 856  # 70% of 1080
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('GAME PROJECT-ANNE 2025')

def save_game_progress(level, score, play_time, player_name="Player"):
    """Save the current game progress to the database"""
    try:
        conn = sqlite3.connect(resource_path('game_data.db'))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO player_progress (player_name, level, score, play_time)
            VALUES (?, ?, ?, ?)
        ''', (player_name, level, score, play_time))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving game progress: {e}")
        return False

def load_game_progress():
    """Load the latest game progress from the database"""
    try:
        conn = sqlite3.connect(resource_path('game_data.db'))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT player_name, level, score, play_time 
            FROM player_progress 
            ORDER BY last_saved DESC 
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'player_name': result[0],
                'level': result[1],
                'score': result[2],
                'play_time': result[3]
            }
        else:
            return None
    except Exception as e:
        print(f"Error loading game progress: {e}")
        return None

def save_high_score(player_name, score, level):
    """Save a high score to the database only if it's a new personal best"""
    try:
        conn = sqlite3.connect(resource_path('game_data.db'))
        cursor = conn.cursor()
        
        # --- NEW: Check if this is a new high score for the player ---
        cursor.execute('''
            SELECT MAX(score) FROM high_scores WHERE player_name = ?
        ''', (player_name,))
        
        result = cursor.fetchone()
        # If the player has no high scores, result will be (None,)
        current_high_score = result[0] if result[0] is not None else 0
        
        # Only save if the new score is higher than the current record
        if score > current_high_score:
            cursor.execute('''
                INSERT INTO high_scores (player_name, score, level)
                VALUES (?, ?, ?)
            ''', (player_name, score, level))
            print(f"New high score saved for {player_name}: {score}")
            conn.commit()
            conn.close()
            return True
        else:
            print(f"Score {score} not higher than {player_name}'s best of {current_high_score}. Not saved.")
            conn.close()
            return False
        # --- END OF NEW CODE ---
            
    except Exception as e:
        print(f"Error saving high score: {e}")
        return False

def get_high_scores(limit=10):
    """Retrieve the top high scores from the database"""
    try:
        conn = sqlite3.connect(resource_path('game_data.db'))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT player_name, score, level, date_achieved 
            FROM high_scores 
            ORDER BY score DESC, level DESC 
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        high_scores = []
        for result in results:
            high_scores.append({
                'player_name': result[0],
                'score': result[1],
                'level': result[2],
                'date': result[3]
            })
            
        return high_scores
    except Exception as e:
        print(f"Error retrieving high scores: {e}")
        return []

def save_settings(music_enabled, sfx_enabled, volume, controls_shown):
    """Save game settings to the database"""
    try:
        conn = sqlite3.connect(resource_path('game_data.db'))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE game_settings 
            SET music_enabled = ?, sfx_enabled = ?, volume = ?, controls_shown = ?
            WHERE id = 1
        ''', (1 if music_enabled else 0, 1 if sfx_enabled else 0, volume, 1 if controls_shown else 0))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

def load_settings():
    """Load game settings from the database"""
    try:
        conn = sqlite3.connect(resource_path('game_data.db'))
        cursor = conn.cursor()
        
        cursor.execute('SELECT music_enabled, sfx_enabled, volume, controls_shown FROM game_settings WHERE id = 1')
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'music_enabled': bool(result[0]),
                'sfx_enabled': bool(result[1]),
                'volume': result[2],
                'controls_shown': bool(result[3])
            }
        else:
            return None
    except Exception as e:
        print(f"Error loading settings: {e}")
        return None

def draw_debug_info():
    # Create level text surface just for debug
    debug_level_text = font.render(f"Level: {level}", True, white)
    level_rect = debug_level_text.get_rect(topleft=(40, 30))
    
    # Settings button rect
    settings_rect = pygame.Rect(screen_width-120, 20, 100, 60)
    
    # Debug text
    debug_info = [
        f"Screen: {screen_width}x{screen_height}",
        f"Level Pos: {level_rect}",
        f"Settings Pos: {settings_rect}"
    ]
# Draw debug text
    debug_font = pygame.font.SysFont('Arial', 20)
    for i, text in enumerate(debug_info):
        text_surf = debug_font.render(text, True, (255,255,255))
        screen.blit(text_surf, (10, screen_height - 80 + i*25))
    
    # Visual markers (optional)
    pygame.draw.rect(screen, (0,255,0), level_rect, 1)  # Green outline for level
    pygame.draw.rect(screen, (255,0,0), settings_rect, 1)  # Red outline for settings
    pygame.draw.line(screen, (255,0,0), (screen_width//2, 0), (screen_width//2, screen_height), 1)  # Center line

# Game clock
clock = pygame.time.Clock()
fps = 60

#define font
font = pygame.font.SysFont('Bauhaus 93', int(70 * 0.7))  # Scaled from original 70px
font_score = pygame.font.SysFont('Bauhaus 93', int(50 * 0.7))  # Scaled from 50px
font_menu = pygame.font.SysFont('Bauhaus 93', int(40 * 0.7))  # Scaled from 40px
font_timer = pygame.font.SysFont('Bauhaus 93', int(70 * 0.7))  # Scaled from 70px

#define colors
white = (255, 255, 255)
blue = (0, 0, 255)
black = (0, 0, 0)
gray = (150, 150, 150)
navy_blue = (0, 0, 128)
bright_orange = (255, 165, 0)

#colors for every level defined
level_colors = {
    1: (255, 100, 100),
    2: (100, 255, 100),
    3: (100, 100, 255),
    4: (255, 255, 100),
    5: (255, 100, 255),
    6: (100, 255, 255),
    7: (255, 165, 100)
}

#define the level timers
level_start_time = 0
last_coin_time = 0

#duration for coin collection alerts
COIN_ALERT_DURATION = 1.0

countdown_time = 3 # 3 second countdown
game_started = False # To track if countdown is complete

#for key press alerts
alert_font = pygame.font.SysFont('Arial', 20)
alerts = []
ALERT_DURATION = 1.5

# Control hints variables
show_controls = True
controls_timer = 0
CONTROLS_DISPLAY_TIME = 5000  # Show controls for 5 seconds at start
IDLE_TIME_FOR_CONTROLS = 10000  # Show controls again after 10 seconds of inactivity
last_player_action_time = 0

# Exit instructions variables
show_exit_instructions = True
exit_instructions_timer = 0
EXIT_INSTRUCTIONS_DURATION = 5000  # Show for 5 seconds
    
def draw_controls_hint():
    # Create a semi-transparent background with more height
    bg = pygame.Surface((350, 110), pygame.SRCALPHA)  # Increased width and height
    bg.fill((0, 0, 0, 180))  # Darker background for better contrast
    bg_rect = bg.get_rect(center=(screen_width // 2, screen_height - 100))
    screen.blit(bg, bg_rect)
    
    # Use a more readable font
    controls_font = pygame.font.SysFont('Arial', 30, bold=True)  # Increased size
    
    # Space to jump (with proper spacing)
    space_text = controls_font.render("PRESS", True, (255, 255, 255))
    space_key = controls_font.render("[SPACE]", True, (255, 255, 0))  # Yellow for key
    action_text = controls_font.render("TO JUMP", True, (255, 255, 255))
    
    # Draw them horizontally centered with spacing
    total_width = space_text.get_width() + 10 + space_key.get_width() + 10 + action_text.get_width()
    start_x = screen_width // 2 - total_width // 2
    
    screen.blit(space_text, (start_x, screen_height - 130))
    screen.blit(space_key, (start_x + space_text.get_width() + 10, screen_height - 130))
    screen.blit(action_text, (start_x + space_text.get_width() + space_key.get_width() + 20, screen_height - 130))
    
    # Arrow keys instruction (with proper spacing)
    use_text = controls_font.render("USE", True, (255, 255, 255))
    arrow_key = controls_font.render("[←][→]", True, (255, 255, 0))  # Yellow for keys
    move_text = controls_font.render("TO MOVE", True, (255, 255, 255))
    
    # Calculate positions
    total_width = use_text.get_width() + 10 + arrow_key.get_width() + 10 + move_text.get_width()
    start_x = screen_width // 2 - total_width // 2
    
    screen.blit(use_text, (start_x, screen_height - 90))
    screen.blit(arrow_key, (start_x + use_text.get_width() + 10, screen_height - 90))
    screen.blit(move_text, (start_x + use_text.get_width() + arrow_key.get_width() + 20, screen_height - 90))
    # Draw small keyboard icons
    key_font = pygame.font.SysFont('Arial', 20, bold=True)
    
    
    # Arrow keys instruction (with proper spacing)
    use_text = controls_font.render("USE", True, (255, 255, 255))
    arrow_key = controls_font.render("[←][→]", True, (255, 255, 0))  # Yellow for keys
    move_text = controls_font.render("TO MOVE", True, (255, 255, 255))
    
    # Calculate positions
    total_width = use_text.get_width() + 10 + arrow_key.get_width() + 10 + move_text.get_width()
    start_x = screen_width // 2 - total_width // 2
    
    screen.blit(use_text, (start_x, screen_height - 90))
    screen.blit(arrow_key, (start_x + use_text.get_width() + 10, screen_height - 90))
    screen.blit(move_text, (start_x + use_text.get_width() + arrow_key.get_width() + 20, screen_height - 90))
def draw_name_input_screen():
    global player_name, name_input_active, name_input_text, name_input_screen
    
    # Dark background
    screen.fill((30, 30, 50))
    
    # Title
    draw_text('ENTER YOUR NAME', font, white, (screen_width // 2) - 200, screen_height // 2 - 150)
    
    # Input box
    pygame.draw.rect(screen, (50, 50, 80), name_input_rect, border_radius=10)
    pygame.draw.rect(screen, (100, 100, 200) if name_input_active else (70, 70, 120), name_input_rect, 3, border_radius=10)
    
    # Input text
    input_font = pygame.font.SysFont('Arial', 40)
    text_surface = input_font.render(name_input_text, True, white)
    screen.blit(text_surface, (name_input_rect.x + 10, name_input_rect.y + 10))
    
    # Cursor blink
    if name_input_active and pygame.time.get_ticks() % 1000 < 500:
        cursor_x = name_input_rect.x + 10 + text_surface.get_width() + 2
        pygame.draw.line(screen, white, (cursor_x, name_input_rect.y + 10), 
                        (cursor_x, name_input_rect.y + name_input_rect.height - 10), 2)
    
    # Start button
    start_button_rect = pygame.Rect(screen_width // 2 - 100, screen_height // 2 + 50, 200, 60)
    pygame.draw.rect(screen, (0, 100, 200), start_button_rect, border_radius=10)
    pygame.draw.rect(screen, white, start_button_rect, 2, border_radius=10)
    
    start_text = font_menu.render("START GAME", True, white)
    screen.blit(start_text, (start_button_rect.centerx - start_text.get_width() // 2, 
                           start_button_rect.centery - start_text.get_height() // 2))
    
    # Instructions
    instruction_font = pygame.font.SysFont('Arial', 20)
    instructions = instruction_font.render("Click on the box to enter your name, then press START", True, (180, 180, 180))
    screen.blit(instructions, (screen_width // 2 - instructions.get_width() // 2, screen_height // 2 + 120))
    
    return start_button_rect

def add_alert(text, is_coin=False):
    alert = {
        'text': text,
        'time': pygame.time.get_ticks(),
        'shake_offset': 8 if is_coin else 3,  # More shake for coins
        'color': (255, 215, 0) if is_coin else (255, 255, 255),
        'size': 36 if is_coin else 24,  # Larger text for coins
        'duration': 3.0 if is_coin else 1.5,  # Longer display for coins
        'bg_color': (100, 50, 0, 200) if is_coin else (50, 50, 50, 150),  # Gold background for coins
        'border_color': (255, 215, 0, 200) if is_coin else (255, 255, 255, 150),
        'pulse': is_coin  # Whether to pulse the alert
    }
    alerts.append(alert)
        
#define game variables
tile_size = 40
game_over = 0
main_menu = True
level = 1 # Start at level 1
max_levels = 7
score = 0
# Player name variables
player_name = "Player"  # Default name
name_input_active = False
name_input_text = ""
name_input_screen = False
name_input_rect = pygame.Rect(screen_width // 2 - 150, screen_height // 2 - 50, 300, 60)
paused = False # New variable for pause state
settings_menu = False # New variable for settings menu state
music_on = True # Initial state for music
sfx_on = True   # Initial state for sound effects
volume = 0.5  # New: Initial volume level (0.0 to 1.0)1
slider_active = False # New: State for volume slider interaction
level_select_menu = False
title_animation_start_time = 0 # NEW: To track when animation starts
title_animation_duration = 2000 # NEW: Animation duration in milliseconds (2 seconds)
show_main_menu_buttons = False # NEW: Controls when buttons are visible
# New variables for warning sounds
PLATFORM_PROXIMITY_THRESHOLD = 70 # Distance in pixels to trigger platform warning
BLOB_PROXIMITY_THRESHOLD = 100 # Distance in pixels to trigger blob warning
last_platform_warning_time = 0 #
last_blob_warning_time = 0 #
WARNING_COOLDOWN = 1000 # Cooldown in milliseconds (1 second)

#define colours
white = (255, 255, 255)
blue = (0, 0, 255)
black = (0, 0, 0) # New color for menu background
gray = (150, 150, 150) # New color for slider

#load images
sun_img = pygame.image.load(resource_path ('img/sun.png'))
bg_img = pygame.image.load(resource_path('img/sky.png'))
restart_img = pygame.image.load(resource_path('img/restart_btn.png'))
start_img = pygame.image.load(resource_path('img/start_btn.png'))
exit_img = pygame.image.load(resource_path('img/exit_btn.png'))
settings_img = pygame.image.load(resource_path('img/settings_btn.png'))
pause_img = pygame.image.load(resource_path('img/pause_btn.png'))
back_img = pygame.image.load(resource_path('img/back_button.png'))
music_on_img = pygame.image.load(resource_path('img/music_on.png')) 
music_off_img = pygame.image.load(resource_path('img/music_off.png')) 
sfx_on_img = pygame.image.load(resource_path('img/sfx_on.png')) 
sfx_off_img = pygame.image.load(resource_path('img/sfx_off.png')) 

# Simplified Hardcoded Levels (rest of your level data remains the same)
def get_level_data(level):
    if level == 1:
        return [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        ] 
    elif level == 2:
        return [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        ]
    elif level == 3:
        return [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        ]
    elif level == 4:
        return [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        ]
    elif level == 5:
        return [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        ]
    elif level == 6:
        return [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        ]
    elif level == 7:
        return [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        ]
    else:
        return [[0 for _ in range(20)] for _ in range(20)]

#load sounds
pygame.mixer.music.load(resource_path('img/music.wav'))
pygame.mixer.music.set_volume(volume) # Set initial volume based on the 'volume' variable
pygame.mixer.music.play(-1)
jump_fx = pygame.mixer.Sound(resource_path('img/jump.wav'))
jump_fx.set_volume(0.5)
coin_fx = pygame.mixer.Sound(resource_path('img/coin.wav'))
coin_fx.set_volume(0.5)
game_over_fx = pygame.mixer.Sound(resource_path('img/game_over.wav'))
game_over_fx.set_volume(0.5)
# Load new warning sounds
platform_warning_fx = pygame.mixer.Sound(resource_path('img/platform_warning.wav')) #
platform_warning_fx.set_volume(0.3) # Adjust volume as needed
blob_warning_fx = pygame.mixer.Sound(resource_path('img/blob_warning.wav')) #
blob_warning_fx.set_volume(0.3) # Adjust volume as needed

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

# New function to draw hover text with a bubble background
def draw_hover_text(text, x, y):
    hover_font = pygame.font.SysFont('Arial', 18)
    text_surf = hover_font.render(text, True, black) # Black text
    
    # Create background rectangle for the bubble
    # Add padding around the text
    padding_x = 10
    padding_y = 5
    bg_rect = text_surf.get_rect(center=(x, y - 20)).inflate(padding_x * 2, padding_y * 2) # Inflate for padding
    
    # Draw the white background rectangle with rounded corners
    pygame.draw.rect(screen, white, bg_rect, border_radius=5)
    # Draw a thin black border around the bubble
    pygame.draw.rect(screen, black, bg_rect, 1, border_radius=5)
    
    # Blit the text onto the screen, centered within the background rect
    text_rect = text_surf.get_rect(center=bg_rect.center)
    screen.blit(text_surf, text_rect)
    
    
def draw_level_label(level, font, text_col, bg_col, x, y):
    text = f'LEVEL: {level}'
    #get color
    level_color = level_colors.get(level, white)
    img = font.render(f'Level: {level}', True, level_color)
    
    #background rectangle
    bg_rect = pygame.Rect(x - 5, y - 2, img.get_width() + 10, img.get_height() + 4)
    pygame.draw.rect(screen, bg_col, bg_rect, border_radius =3)
    pygame.draw.rect(screen, white, bg_rect, 2, border_radius=3)
    screen.blit(img, (x, y))

#function to reset level
def reset_level(level):   
    global level_start_time, game_started, level_duration, show_controls, controls_timer, last_player_action_time

    level_duration = {
        1: 15,
        2: 25,
        3: 35,
        4: 45,
        5: 55,
        6: 65,
        7: 75,
        8: 85
    }.get(level, 60)
 
    player.reset(100, screen_height - 130)
    blob_group.empty()
    platform_group.empty()
    coin_group.empty()
    lava_group.empty()
    exit_group.empty()
 
    level_start_time = pygame.time.get_ticks()
    game_started = False
    show_controls = True
    controls_timer = pygame.time.get_ticks()
    last_player_action_time = pygame.time.get_ticks()
 
    # Get the hardcoded level data
    world_data = get_level_data(level)
    world = World(world_data)

    #load in level data and create world
    if path.exists(f'level{level}_data'):
        pickle_in = open(f'level{level}_data', 'rb')
        world_data = pickle.load(pickle_in)
    world = World(world_data)
 
    #create dummy coin for showing the score
    score_coin = Coin(tile_size // 2, tile_size // 2)
    coin_group.add(score_coin)
    return world

class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False
        self.hover_text = ""  # Text to show on hover
        self.hover_font = pygame.font.SysFont('Arial', 18)
        self.hover_visible = False

    def draw(self):
        action = False
        pos = pygame.mouse.get_pos()
        
        # Reset hover state
        self.hover_visible = False
        
        # Check for hover and click
        if self.rect.collidepoint(pos):
            self.hover_visible = True
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                action = True
                self.clicked = True
        
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False
            
        # Draw the button
        screen.blit(self.image, self.rect)
        
        # Draw hover text if needed
        if self.hover_visible and self.hover_text:
            self.draw_hover_text()
            
        return action

    def set_hover_text(self, text):
        self.hover_text = text

    def draw_hover_text(self):
        try:
            # Render text
            text_surf = self.hover_font.render(self.hover_text, True, (0, 0, 0))
            
            # Calculate background rectangle (10px above button)
            bg_rect = text_surf.get_rect(center=(self.rect.centerx, self.rect.top - 15))
            bg_rect = bg_rect.inflate(20, 10)  # Add padding
            
            # Draw background (semi-transparent white)
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(bg_surface, (255, 255, 255, 220), (0, 0, bg_rect.width, bg_rect.height), border_radius=5)
            pygame.draw.rect(bg_surface, (0, 0, 0, 220), (0, 0, bg_rect.width, bg_rect.height), 1, border_radius=5)
            
            # Draw everything
            screen.blit(bg_surface, bg_rect)
            text_rect = text_surf.get_rect(center=bg_rect.center)
            screen.blit(text_surf, text_rect)
            
        except Exception as e:
            print(f"Error drawing hover text: {e}")

        #draw button
        screen.blit(self.image, self.rect)

        return action

    def check_hover(self):
        pos = pygame.mouse.get_pos()
        return self.rect.collidepoint(pos)


    def draw_hover_text(text, x, y):
        font = pygame.font.SysFont('Arial', 20)
        text_surf = font.render(text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(x, y))
    # Optional background
        pygame.draw.rect(screen, (0, 0, 0), text_rect.inflate(10, 5))
        screen.blit(text_surf, text_rect)

class Player():
    def __init__(self, x, y):
        self.reset(x, y)

    def update(self, game_over):
        global show_controls, controls_timer, last_player_action_time
        
        dx = 0
        dy = 0
        walk_cooldown = 5
        col_thresh = 20
        
        player_moved = False  # Track if player took any action
        
        if  level >= 5:
            gravity = 1.2
            jump_power = -14
        else:
            gravity = 1.0
            jump_power = -15

        if game_over == 0 and game_started:
            #get keypresses
            key = pygame.key.get_pressed()
            #pygame doesn't access physical vibrations but can simulate a shake effect on key press
            global shake_frames
            if key[pygame.K_SPACE] and self.jumped == False and self.in_air == False:
                player_moved = True
                if sfx_on: # Only play jump sound if SFX is on
                    jump_fx.play()
                self.vel_y = jump_power
                self.jumped = True
                add_alert("jumped!")
                shake_frames = 10
                
            if key[pygame.K_SPACE] == False:
                self.jumped = False
            
            if key[pygame.K_LEFT]:
                player_moved = True
                dx -= 5
                self.counter += 1
                self.direction = -1
                add_alert("Move Left")
                shake_frames = 6
            
            if key[pygame.K_RIGHT]:
                player_moved = True
                dx += 5
                self.counter += 1
                self.direction = 1
                add_alert("Move Right")
                shake_frames = 6
            
            if key[pygame.K_LEFT] == False and key[pygame.K_RIGHT] == False:
                self.counter = 0
                self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            #handle animation
            if self.counter > walk_cooldown:
                self.counter = 0    
                self.index += 1
                if self.index >= len(self.images_right):
                    self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            #add gravity
            self.vel_y += 1
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y

            #check for collision
            self.in_air = True
            for tile in world.tile_list:
                #check for collision in x direction
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                #check for collision in y direction
                if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    #check if below the ground i.e. jumping
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0
                    #check if above the ground i.e. falling
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.in_air = False

            #check for collision with enemies
            if pygame.sprite.spritecollide(self, blob_group, False):
                game_over = -1
                if sfx_on: # Only play game over sound if SFX is on
                    game_over_fx.play()
                #ENEMY DEATH ALERT:
                add_alert("HIT BY ENEMY! YOU DIED!", False)

            #check for collision with lava
            if pygame.sprite.spritecollide(self, lava_group, False):
                game_over = -1
                if sfx_on: # Only play game over sound if SFX is on
                    game_over_fx.play()
                # LAVA DEATH ALERT:
                add_alert("FELL IN LAVA! YOU DIED!", False)

            #check for collision with lava
            if pygame.sprite.spritecollide(self, lava_group, False):
                game_over = -1
                if sfx_on: # Only play game over sound if SFX is on
                    game_over_fx.play()

            #check for collision with exit
            if pygame.sprite.spritecollide(self, exit_group, False):
                game_over = 1

            #check for collision with platforms
            for platform in platform_group:
                #collision in the x direction
                if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                #collision in the y direction
                if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    #check if below platform
                    if abs((self.rect.top + dy) - platform.rect.bottom) < col_thresh:
                        self.vel_y = 0
                        dy = platform.rect.bottom - self.rect.top
                    #check if above platform
                    elif abs((self.rect.bottom + dy) - platform.rect.top) < col_thresh:
                        self.rect.bottom = platform.rect.top - 1
                        self.in_air = False
                        dy = 0
                    #move sideways with the platform
                    if platform.move_x != 0:
                        self.rect.x += platform.move_direction

            #update player coordinates
            self.rect.x += dx
            self.rect.y += dy

        elif game_over == -1:
            self.image = self.dead_image
            draw_text('GAME OVER!', font, blue, (screen_width // 2) - 200, screen_height // 2)
            if self.rect.y > 200:
                self.rect.y -= 5

        # Update controls display timer based on player activity
        current_time = pygame.time.get_ticks()
        if player_moved:
            last_player_action_time = current_time
            show_controls = False
        elif current_time - last_player_action_time > IDLE_TIME_FOR_CONTROLS:
            show_controls = True
            controls_timer = current_time
        
        # Hide controls after display time expires
        if show_controls and current_time - controls_timer > CONTROLS_DISPLAY_TIME:
            show_controls = False

        #draw player onto screen
        screen.blit(self.image, self.rect)

        return game_over

    def reset(self, x, y):
        self.images_right = []
        self.images_left = []
        self.index = 0
        self.counter = 0
        for num in range(1, 5):
            img_right = pygame.image.load(resource_path(f'img/guy{num}.png'))
            img_right = pygame.transform.scale(img_right, (40, 80))
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_right.append(img_right)
            self.images_left.append(img_left)
        self.dead_image = pygame.image.load(resource_path('img/ghost.png'))
        self.image = self.images_right[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        self.in_air = True

class World():
    def __init__(self, data):
        self.tile_list = []

        #load images
        dirt_img = pygame.image.load(resource_path('img/dirt.png'))
        grass_img = pygame.image.load(resource_path('img/grass.png'))

        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1:
                    img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 2:
                    img = pygame.transform.scale(grass_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 3:
                    blob = Enemy(col_count * tile_size, row_count * tile_size + 15)
                    blob_group.add(blob)
                if tile == 4:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 1, 0)
                    platform_group.add(platform)
                if tile == 5:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 0, 1)
                    platform_group.add(platform)
                if tile == 6:
                    lava = Lava(col_count * tile_size, row_count * tile_size + (tile_size // 2))
                    lava_group.add(lava)
                if tile == 7:
                    coin = Coin(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
                    coin_group.add(coin)
                if tile == 8:
                    exit = Exit(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    exit_group.add(exit)
                col_count += 1
            row_count += 1

    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(resource_path('img/blob1.png'))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, move_x, move_y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load(resource_path('img/platform.png'))
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_counter = 0
        self.move_direction = 1
        self.move_x = move_x
        self.move_y = move_y

    def update(self):
        self.rect.x += self.move_direction * self.move_x
        self.rect.y += self.move_direction * self.move_y
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1

class Lava(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load(resource_path('img/lava.png'))
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load(resource_path('img/coin.png'))
        self.image = pygame.transform.scale(img, (tile_size // 2, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        # Create a highly visible exit marker
        self.image = pygame.Surface((tile_size, int(tile_size * 1.5)), pygame.SRCALPHA)
        self.image.fill((255, 0, 0, 200))  # Semi-transparent red background
        
        # Add giant white X
        pygame.draw.line(self.image, (255, 255, 255), (0, 0), 
                        (tile_size, int(tile_size*1.5)), 4)
        pygame.draw.line(self.image, (255, 255, 255), 
                        (tile_size, 0), (0, int(tile_size*1.5)), 4)
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.pulse_time = 0
        
    def update(self):
        # Create pulsing effect
        self.pulse_time += 0.05
        pulse = abs(math.sin(self.pulse_time)) * 0.2 + 0.8  # 0.8 to 1.0 scale
        
        # Recreate the image with current pulse size
        size = int(tile_size * pulse)
        self.image = pygame.Surface((size, int(size * 1.5)), pygame.SRCALPHA)
        self.image.fill((255, 0, 0, 200))
        
        # Redraw X
        pygame.draw.line(self.image, (255, 255, 255), (0, 0), 
                        (size, int(size*1.5)), 4)
        pygame.draw.line(self.image, (255, 255, 255), 
                        (size, 0), (0, int(size*1.5)), 4)
        
    def draw_instruction(self, screen):
        # Create a pulsing instruction above the exit
        pulse = int(pygame.time.get_ticks()/100) % 10
        size = 30 + pulse * 2  # Pulsing size
        
        # Create instruction text
        font = pygame.font.SysFont('impact', size)
        text = font.render("EXIT!", True, (255, 255, 0))  # Yellow text
        outline = font.render("EXIT!", True, (0, 0, 0))   # Black outline
        
        text_rect = text.get_rect(center=(self.rect.centerx, self.rect.top - 25))
        
        # Draw multiple outlines for visibility
        for offset in [(1,1), (-1,1), (1,-1), (-1,-1)]:
            screen.blit(outline, (text_rect.x+offset[0], text_rect.y+offset[1]))
        
        # Draw main text
        screen.blit(text, text_rect)
        
        # Draw arrow pointing down to exit
        arrow_size = 10
        points = [
            (self.rect.centerx, text_rect.bottom + 5),
            (self.rect.centerx - arrow_size, text_rect.bottom + 5 + arrow_size),
            (self.rect.centerx + arrow_size, text_rect.bottom + 5 + arrow_size)
        ]
        pygame.draw.polygon(screen, (255, 255, 0), points)
		
# --- New UI Elements ---
class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.grabbed = False

    def draw(self, screen):
        # Draw background bar
        pygame.draw.rect(screen, gray, self.rect, border_radius=5)
        # Draw slider knob
        knob_x = self.rect.x + int((self.value - self.min_val) / (self.max_val - self.min_val) * (self.rect.width - self.rect.height))
        knob_rect = pygame.Rect(knob_x, self.rect.y, self.rect.height, self.rect.height)
        pygame.draw.ellipse(screen, white, knob_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.grabbed = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.grabbed = False
        elif event.type == pygame.MOUSEMOTION and self.grabbed:
            pos_x, _ = event.pos
            # Clamp the knob position within the slider
            self.value = self.min_val + (pos_x - self.rect.x) / (self.rect.width - self.rect.height) * (self.max_val - self.min_val)
            self.value = max(self.min_val, min(self.max_val, self.value))
            return True # Indicate that the slider was interacted with
        return False

player = Player(100, screen_height - 130)

blob_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

#create dummy coin for showing the score
score_coin = Coin(tile_size // 2, tile_size // 2)
coin_group.add(score_coin)

#load in level data and create world
if path.exists(f'level{level}_data'):
    pickle_in = open(f'level{level}_data', 'rb')
    world_data = pickle.load(pickle_in)
world = World(world_data)

#create buttons
restart_button = Button(screen_width // 2 - 50, screen_height // 2 + 100, restart_img)
start_button = Button(screen_width // 2 - 340, screen_height // 2, start_img)
exit_button = Button(screen_width // 2 + 70, screen_height // 2, exit_img)
settings_button = Button(screen_width - settings_img.get_width() - 35, 45, settings_img) # Top-right corner
pause_button = Button(screen_width - pause_img.get_width() - 90, 35, pause_img)

# Settings menu buttons and elements
volume_slider = Slider(screen_width // 2 - 100, screen_height // 2 - 50, 200, 20, 0.0, 1.0, pygame.mixer.music.get_volume())
# New buttons for settings menu
back_button = Button(0, 0, back_img) # Initial position will be set in draw_settings_menu
music_toggle_button = Button(0, 0, music_on_img) # Initial image, will change based on state
sfx_toggle_button = Button(0, 0, sfx_on_img)

play_count = 0
def draw_pause_menu():
    global play_count
    # Darken the background
    overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))

    draw_text('PAUSED', font, white, (screen_width // 2) - 120, screen_height // 2 - 150)
    
    action = None
    button_y = screen_height // 2 - 20 

    # Create Save Game button
    save_text = font_menu.render("SAVE GAME", True, white)
    save_button_rect = pygame.Rect(screen_width // 2 - 100, button_y - 80, 200, 50)
    
    # Draw button background
    pygame.draw.rect(screen, navy_blue, save_button_rect, border_radius=5)
    pygame.draw.rect(screen, white, save_button_rect, 2, border_radius=5)
    
    # Draw text
    screen.blit(save_text, (save_button_rect.centerx - save_text.get_width() // 2, 
                           save_button_rect.centery - save_text.get_height() // 2))
    
    # Check if save button is clicked
    mouse_pos = pygame.mouse.get_pos()
    mouse_clicked = pygame.mouse.get_pressed()[0]
    
    # Initialize play_time variable
    play_time = 0
    
    if save_button_rect.collidepoint(mouse_pos):
        # Draw hover effect
        pygame.draw.rect(screen, blue, save_button_rect, border_radius=5)
        draw_hover_text("Save current progress", save_button_rect.centerx, save_button_rect.top - 20)
        
        if mouse_clicked:
            # Calculate play time in seconds (only when button is clicked)
            current_time = pygame.time.get_ticks()
            play_time = (current_time - level_start_time) // 1000
            
            print(f"Attempting to save: Level={level}, Score={score}, Time={play_time}")
            
            # Save game progress to database
            if save_game_progress(level, score, play_time, player_name): 
                print("Game saved successfully!")
                add_alert("Game saved successfully!", True)
            else:
                print("Failed to save game!")
                add_alert("Failed to save game", False)
            
            # Add a small delay to prevent multiple rapid clicks
            pygame.time.delay(300)
    
    # Draw Restart button
    restart_button.rect.x = screen_width // 2 - restart_button.image.get_width() - 30 
    restart_button.rect.y = button_y
    if restart_button.draw():
        action = 'restart_level'

    # Draw Exit button
    exit_button.rect.x = screen_width // 2 + 30 
    exit_button.rect.y = button_y
    
    # Store the button action first
    exit_button_action = exit_button.draw()
    
    # Then check hover and draw text
    if exit_button.check_hover():
        draw_hover_text("Click to return to Main Menu",
                      exit_button.rect.centerx,
                      exit_button.rect.centery - 30)
    
    if exit_button_action:
        action = 'main_menu'

    return action

	# DEBUG: Always show test text to verify drawing works
    test_font = pygame.font.SysFont('Arial', 30)
    test_text = test_font.render("DEBUG TEXT", True, (255, 0, 0))  # Red text
    screen.blit(test_text, (50, 50))

    # DEBUG: Visual button bounds
    pygame.draw.rect(screen, (0, 255, 0), exit_button.rect, 2)  # Green outline

    
    # Hover check
    if exit_button.check_hover():
       print("HOVER DETECTED - CHECK CONSOLE")  # Verify in console
       hover_font = pygame.font.SysFont('Arial', 30)
       hover_text = hover_font.render("HOVERING!", True, (0, 255, 0))  # Green text
       screen.blit(hover_text, (exit_button.rect.x, exit_button.rect.y - 40))
    
    draw_hover_text("Click to return to Main Menu",
                   exit_button.rect.centerx,
                   exit_button.rect.centery - 30)

    if button_action:
       action = 'main_menu'

def draw_settings_menu():
    global music_on, sfx_on, volume, slider_active # Declare global to modify the variables

    # Darken the background
    overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150)) # Black with 150 alpha (out of 255)
    screen.blit(overlay, (0, 0))

    draw_text('SETTINGS', font, white, (screen_width // 2) - 140, screen_height // 2 - 150) #

    action = None # Initialize action

    # Back Button (top-left corner)
    # Store original positions before temporarily changing them for drawing
    original_back_x = back_button.rect.x
    original_back_y = back_button.rect.y
    back_button.rect.x = 20 # A small offset from the left edge
    back_button.rect.y = 20 # A small offset from the top edge
    if back_button.draw():
        action = 'back_to_game' # Custom action for returning to game
    # Restore original positions after drawing to prevent affecting other uses
    back_button.rect.x = original_back_x
    back_button.rect.y = original_back_y

    # Toggle Icons (example: Music and SFX)
    icon_y_pos = screen_height // 2 - 50 # Y position for the first icon
    icon_x_offset = 100 # X offset from center for icons

    # Music Toggle
    # Set the correct image based on current music state
    music_toggle_button.image = music_on_img if music_on else music_off_img
    # Store original positions
    original_music_toggle_x = music_toggle_button.rect.x
    original_music_toggle_y = music_toggle_button.rect.y
    # Reposition for drawing
    music_toggle_button.rect.x = screen_width // 2 - music_toggle_button.image.get_width() // 2 - icon_x_offset
    music_toggle_button.rect.y = icon_y_pos
    # Draw label above the button
    draw_text("Music", font_score, white, music_toggle_button.rect.centerx - (font_score.render("Music", True, white).get_width() // 2), music_toggle_button.rect.y - 30)
    if music_toggle_button.draw():
        music_on = not music_on # Toggle music state
        if music_on:
            mixer.music.play(-1) # Start music if turned on
        else:
            mixer.music.stop() # Stop music if turned off
    # Restore original positions
    music_toggle_button.rect.x = original_music_toggle_x
    music_toggle_button.rect.y = original_music_toggle_y

    # SFX Toggle
    # Set the correct image based on current SFX state
    sfx_toggle_button.image = sfx_on_img if sfx_on else sfx_off_img
    # Store original positions
    original_sfx_toggle_x = sfx_toggle_button.rect.x
    original_sfx_toggle_y = sfx_toggle_button.rect.y
    # Reposition for drawing
    sfx_toggle_button.rect.x = screen_width // 2 - sfx_toggle_button.image.get_width() // 2 + icon_x_offset
    sfx_toggle_button.rect.y = icon_y_pos
    # Draw label above the button
    draw_text("SFX", font_score, white, sfx_toggle_button.rect.centerx - (font_score.render("SFX", True, white).get_width() // 2), sfx_toggle_button.rect.y - 30)
    if sfx_toggle_button.draw():
        sfx_on = not sfx_on # Toggle SFX state
    # Restore original positions
    sfx_toggle_button.rect.x = original_sfx_toggle_x
    sfx_toggle_button.rect.y = original_sfx_toggle_y

    # Volume Slider Bar dimensions and position
    slider_bar_width = 300
    slider_bar_height = 10
    # Position below the icons, adjust as needed
    slider_y_pos = screen_height // 2 - 50 + 100 
    slider_x_start = screen_width // 2 - slider_bar_width // 2
    slider_x_end = slider_x_start + slider_bar_width

    # Draw slider bar (white background with black border)
    pygame.draw.rect(screen, white, (slider_x_start, slider_y_pos, slider_bar_width, slider_bar_height), border_radius=5)
    pygame.draw.rect(screen, black, (slider_x_start, slider_y_pos, slider_bar_width, slider_bar_height), 2, border_radius=5) # Border

    # Calculate handle position based on current volume
    handle_x = slider_x_start + int(volume * slider_bar_width)
    handle_radius = 15
    # Create a rectangle for the slider handle for collision detection
    handle_rect = pygame.Rect(handle_x - handle_radius, slider_y_pos + slider_bar_height // 2 - handle_radius, handle_radius * 2, handle_radius * 2)

    # Draw slider handle (black outline with blue inner circle)
    pygame.draw.circle(screen, black, (handle_x, slider_y_pos + slider_bar_height // 2), handle_radius)
    pygame.draw.circle(screen, (0, 0, 255), (handle_x, slider_y_pos + slider_bar_height // 2), handle_radius - 2) # Use a specific color for blue

    # Display volume percentage text next to the slider
    volume_percent_text = f"{int(volume * 100)}%"
    draw_text(volume_percent_text, font_score, white, slider_x_start + slider_bar_width + 40, slider_y_pos) 

    # Handle slider interaction (mouse clicks and drags)
    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()
    
    # Check if left mouse button is down
    if mouse_pressed[0]: 
        # If the mouse is colliding with the handle or the slider is already active (being dragged)
        if handle_rect.collidepoint(mouse_pos) or slider_active: 
            slider_active = True # Set slider to active
            
            # Clamp the mouse's X position within the slider bar's boundaries
            new_handle_x = max(slider_x_start, min(mouse_pos[0], slider_x_end))
            
            # Calculate the new volume based on the handle's position relative to the bar
            new_volume = (new_handle_x - slider_x_start) / slider_bar_width
            volume = new_volume # Update the global volume variable

            # Apply the new volume to the music mixer
            pygame.mixer.music.set_volume(volume)
    else:
        slider_active = False # Reset slider active state when mouse button is released

    return action # Will return 'back_to_game' or None

def draw_countdown_timer():
    current_time = pygame.time.get_ticks()
    elapsed = (current_time - level_start_time) / 1000 # Convert to seconds
    remaining_countdown = max(0, countdown_time - elapsed)
    
    if remaining_countdown > 0:
        
        #create dark overlay
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        countdown_number = int(remaining_countdown) + 1 # Show 3, 2, 1
        countdown_text = str(countdown_number)
        
        #make countdown numbers bigger and more dramatic
        if countdown_number == 3:
            text_color = bright_orange
            outline_color = navy_blue
            text_size = 120
        elif countdown_number == 2:
            text_color = (255, 255, 255)
            outline_color = bright_orange
            text_size = 150
        else:
            text_color = (255, 255, 0)
            outline_color = (255, 100, 0)
            text_size = 180
            
        countdown_font = pygame.font.SysFont('Impact', text_size)
        
        text_surf = countdown_font.render(countdown_text, True, text_color)
        outline_surf = countdown_font.render(countdown_text, True, outline_color)
        
        text_rect = text_surf.get_rect(center=(screen_width // 2, screen_height // 2))
        outline_rect = outline_surf.get_rect(center=(screen_width // 2 + 3, screen_height // 2 + 3))
        
        screen.blit(outline_surf, outline_rect)
        screen.blit(text_surf, text_rect)
        
        #add pulsing effect
        pulse = abs(pygame.time.get_ticks() % 1000 - 500) / 500
        scaled_text = pygame.transform.scale(text_surf, 
                                           (int(text_surf.get_width() * (1 + pulse * 0.2)), 
                                        int(text_surf.get_height() * (1 + pulse * 0.2))))
        
        scaled_rect = scaled_text.get_rect(center=(screen_width // 2, screen_height // 2))
        screen.blit(scaled_text, scaled_rect)
       
        # Create a semi-transparent background
        bg_surf = pygame.Surface((text_surf.get_width() + 40, text_surf.get_height() + 40), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 150))
        bg_rect = bg_surf.get_rect(center=(screen_width // 2, screen_height // 2))
        
        screen.blit(bg_surf, bg_rect)
        screen.blit(text_surf, text_rect)
        
        return False # Countdown not complete
    return True # Countdown complete

def draw_level_timer():
    if not game_started:
        return
    
    current_time = pygame.time.get_ticks()
    elapsed = (current_time - level_start_time - (countdown_time * 1000)) / 1000 # Subtract countdown time
    remaining_time = max(0, level_duration - elapsed)
    
    # Convert to minutes:seconds format
    minutes = int(remaining_time // 60)
    seconds = int(remaining_time % 60)
    timer_text = f"{minutes:02d}:{seconds:02d}"
    
    # Draw timer at top of screen
    text_surf = font_score.render(timer_text, True, bright_orange)
    
    bg_width = max(150, text_surf.get_width() + 20)
    bg_rect = pygame.Rect(screen_width // 2 - 75, 35, 150, 50)
    
    pygame.draw.rect(screen, navy_blue, bg_rect, border_radius=8)
    pygame.draw.rect(screen, white, bg_rect, 2, border_radius=8)
    
    text_x = screen_width // 2 - text_surf.get_width() // 2
    text_y = 35 + (50 - text_surf.get_height()) // 2
    screen.blit(text_surf, (text_x, text_y))
    
    if remaining_time < 10:
        pulse = abs(pygame.time.get_ticks() % 1000 - 500) / 500
        bg_rect.inflate_ip(int(10 * pulse), int(10 * pulse))
        pygame.draw.rect(screen, (200, 0, 0), bg_rect, border_radius=8)
    
    # Check if time has run out
    if remaining_time <= 0:
        return True # Time's up
    return False

def draw_level_select_menu():
    # Darken the background
    overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180)) # Darker black for menu
    screen.blit(overlay, (0, 0))

    draw_text('SELECT LEVEL', font, white, (screen_width // 2) - 220, screen_height // 2 - 200)

    action = None

    # Back Button (top-left corner)
    # Store original positions before temporarily changing them for drawing
    original_back_x = back_button.rect.x
    original_back_y = back_button.rect.y
    back_button.rect.x = 20 # A small offset from the left edge
    back_button.rect.y = 20 # A small offset from the top edge
    if back_button.draw():
        action = 'back_to_main' # Action to return to main menu
    # Restore original positions after drawing to prevent affecting other uses
    back_button.rect.x = original_back_x
    back_button.rect.y = original_back_y

    # Level selection buttons in a 4x4 grid layout
    columns_per_row = 4 # Defines how many columns will be in each row
    button_width = 100
    button_height = 80 # Made buttons slightly taller for better appearance
    gap = 20 # Gap between buttons

    # Calculate number of rows needed for the levels
    num_rows = (max_levels + columns_per_row - 1) // columns_per_row # Ceiling division

    # Calculate total grid dimensions for centering
    grid_width = columns_per_row * button_width + (columns_per_row - 1) * gap
    grid_height = num_rows * button_height + (num_rows - 1) * gap

    # Calculate starting position to center the grid on the screen
    start_x = (screen_width - grid_width) // 2
    # Adjust Y position to be visually appealing relative to the "SELECT LEVEL" title
    start_y = screen_height // 2 - grid_height // 2 + 50 

    level_buttons = []
    for i in range(1, max_levels + 1):
        row = (i - 1) // columns_per_row
        col = (i - 1) % columns_per_row

        btn_x = start_x + col * (button_width + gap)
        btn_y = start_y + row * (button_height + gap)

        # Create a temporary Surface for each button to draw custom graphics
        temp_button_img = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
        
        # Draw button background (a semi-transparent blue with rounded corners)
        button_color = (60, 120, 180, 200) # RGBA (blue with some transparency)
        pygame.draw.rect(temp_button_img, button_color, (0, 0, button_width, button_height), border_radius=10) 
        # Draw a white border around the button
        pygame.draw.rect(temp_button_img, white, (0, 0, button_width, button_height), 3, border_radius=10) 

        # Render the level number text using 'font_menu'
        level_text_surf = font_menu.render(str(i), True, (255, 255, 255)) # White text
        # Center the text on the button image
        text_rect = level_text_surf.get_rect(center=(button_width // 2, button_height // 2))
        temp_button_img.blit(level_text_surf, text_rect)
        
        # Create the Button instance with the custom-rendered image
        btn = Button(btn_x, btn_y, temp_button_img)
        level_buttons.append((btn, i))

    for btn, lvl in level_buttons:
        if btn.draw():
            action = lvl # Return the selected level number

    return action

run = True
while run:
    clock.tick(fps)
    screen.blit(bg_img, (0, 0))
    screen.blit(sun_img, (100, 100))

    # Handle name input screen - THIS MUST BE INSIDE THE while run: LOOP
    if name_input_screen:
        start_button_rect = draw_name_input_screen()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if name_input_rect.collidepoint(event.pos):
                    name_input_active = True
                else:
                    name_input_active = False
                    
                if start_button_rect.collidepoint(event.pos) and name_input_text.strip():
                    player_name = name_input_text.strip()
                    name_input_screen = False
                    level_select_menu = True
                    print(f"Player name set to: {player_name}")
            
            if event.type == pygame.KEYDOWN and name_input_active:
                if event.key == pygame.K_RETURN:
                    if name_input_text.strip():
                        player_name = name_input_text.strip()
                        name_input_screen = False
                        level_select_menu = True
                elif event.key == pygame.K_BACKSPACE:
                    name_input_text = name_input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    name_input_active = False
                else:
                    if len(name_input_text) < 15:
                        name_input_text += event.unicode
        
        pygame.display.update()
        continue  # This continue is now properly inside the while loop
    
    # ... rest of your game code (main_menu, settings_menu, level_select_menu, etc.) ...

    if main_menu or settings_menu or level_select_menu:
        current_time = pygame.time.get_ticks()

    if main_menu:
        current_time = pygame.time.get_ticks()
  
        # Initialize animation timer on the first frame main_menu is active
        if title_animation_start_time == 0: 
            title_animation_start_time = current_time
            show_main_menu_buttons = False # Hide buttons initially
        
        elapsed_time = current_time - title_animation_start_time

        # Draw the main menu background
        screen.blit(bg_img, (0, 0))
        screen.blit(sun_img, (100, 100))

        # Animation logic for the game title label
        alpha = 255 # Default to fully opaque
        if elapsed_time < title_animation_duration:
            # Calculate alpha for a fade-in effect
            alpha = min(255, int((elapsed_time / title_animation_duration) * 255))
        
        # Render and display the main game title ("GAME PROJECT")
        game_title_surf = font.render('A 2D GAME PROJECT', True, blue)
        game_title_surf.set_alpha(alpha) # Apply transparency
        game_title_rect = game_title_surf.get_rect(center=(screen_width // 2, screen_height // 2 - 150))
        screen.blit(game_title_surf, game_title_rect)

        # Render and display the subtitle/year ("ANNE 2025")
        game_year_surf = font_score.render('ANNE 2025', True, blue) # Using font_score for smaller text
        game_year_surf.set_alpha(alpha)
        game_year_rect = game_year_surf.get_rect(center=(screen_width // 2, screen_height // 2 - 80)) # Positioned below main title
        screen.blit(game_year_surf, game_year_rect)

        # Show start and exit buttons only after the animation duration has passed
        if elapsed_time >= title_animation_duration:
            show_main_menu_buttons = True
        
        if show_main_menu_buttons:
           if exit_button.draw():
              run = False
           if start_button.draw():
              name_input_screen = True  # Go to name input first
              main_menu = False
              # Reset name input fields
              name_input_text = ""
              name_input_active = False
               

    elif settings_menu == True:
        action = draw_settings_menu()
        if action == 'back_to_game':
            settings_menu = False

    elif level_select_menu == True:
        selected_level = draw_level_select_menu()
        if selected_level == 'back_to_main':
            level_select_menu = False
            main_menu = True # Go back to the main menu
            title_animation_start_time = 0 # NEW: Reset animation timer
            show_main_menu_buttons = False 
        elif selected_level is not None: # A level was selected
            level = selected_level # Set the chosen level
            
            # FIX: Correctly initialize the world for the selected level
            world = reset_level(level) # Call reset_level with the chosen level number
            player.reset(100, screen_height - 130) # Reset player for the new game
            game_over = 0 # Ensure game is not in game_over state
            score = 0 # Reset score
            level_select_menu = False # Exit level selection menu
            main_menu = False # Start the game (exit main menu state)
            paused = False # Ensure game is not paused when starting
            
        # Handle volume slider events within the settings menu loop
        for event in pygame.event.get(): # Process settings menu specific events
            if event.type == pygame.QUIT:
                run = False
            if volume_slider.handle_event(event):
                pygame.mixer.music.set_volume(volume_slider.value)
            
            # Handle level selection key presses
            if event.type == pygame.K_ESCAPE: # Allow ESC to exit settings
                settings_menu = False
            if event.type == pygame.KEYDOWN:
                # This section is fine, as it's within the settings_menu state
                if event.key == pygame.K_1:
                    level = 1
                    settings_menu = False # Exit settings after selecting level
                    main_menu = False # Go to game directly, not back to main menu
                    world_data = [] # Clear old world data
                    world = reset_level(level)
                    game_over = 0
                    score = 0
                elif event.key == pygame.K_2 and max_levels >= 2:
                    level = 2
                    settings_menu = False
                    main_menu = False
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    score = 0
                elif event.key == pygame.K_3 and max_levels >= 3:
                    level = 3
                    settings_menu = False
                    main_menu = False
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    score = 0
                elif event.key == pygame.K_4 and max_levels >= 4:
                    level = 4
                    settings_menu = False
                    main_menu = False
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    score = 0
                elif event.key == pygame.K_5 and max_levels >= 5:
                    level = 5
                    settings_menu = False
                    main_menu = False
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    score = 0
                elif event.key == pygame.K_6 and max_levels >= 6:
                    level = 6
                    settings_menu = False
                    main_menu = False
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    score = 0
                elif event.key == pygame.K_7 and max_levels >= 7:
                    level = 7
                    settings_menu = False
                    main_menu = False
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    score = 0
        pass
    else:
        # Game is running or paused (including when exiting settings to game)
        if settings_button.draw():
            settings_menu = True
        # Add hover message for settings button
        if settings_button.check_hover():
            draw_hover_text("Settings", settings_button.rect.centerx, settings_button.rect.centery)

        if pause_button.draw():
            paused = not paused # This line toggles the paused state
        # Add hover message for pause button
        if pause_button.check_hover():
            draw_hover_text("Pause/Resume", pause_button.rect.centerx, pause_button.rect.centery)

        world.draw() # This line should be at the same indentation level as the button drawing
        
        if not game_started:
            game_started = draw_countdown_timer()
            if game_started:  # Just finished countdown
                show_controls = True
                controls_timer = pygame.time.get_ticks()
                last_player_action_time = pygame.time.get_ticks()
  
        if paused == False and game_over == 0 and game_started:
            # Check level timer
            time_up = draw_level_timer()
            if time_up:
                game_over = -1
                if sfx_on:
                    game_over_fx.play()
                    draw_text('TIME\'S UP! TRY AGAIN', font, gray, (screen_width //2) - 150, screen_height // 2 - 20)
            blob_group.update()
            platform_group.update()
            #update score
            #check if a coin has been collected
            if pygame.sprite.spritecollide(player, coin_group, True):
                
                score += 1
                if sfx_on: # Only play coin sound if SFX is on
                        coin_fx.play()
                add_alert(f"+1 Coin! (Total: {score})", is_coin=True)
                
                last_coin_time = pygame.time.get_ticks()
    
            coin_time = pygame.time.get_ticks() - last_coin_time if 'last_coin_time' in globals() else 10000
            flash_duration = 1000
   
            if coin_time < flash_duration:
                fade_progress = coin_time / flash_duration
                r = int(255 + (0 - 255) * fade_progress)
                g = int(215 + (0 - 215) * fade_progress)
                b = int(0 + (128 - 0) * fade_progress)
                score_color = (r, g, b)
            else:
                score_color = navy_blue
    
            score_text = font_score.render('X ' + str(score), True, score_color)
            outline_text = font_score.render('X ' + str(score), True, white)
            screen.blit(outline_text, (tile_size - 12, 12))
            screen.blit(score_text, (tile_size - 10, 10))
   
            #draw_text('X ' + str(score), font_score, black, tile_size - 10, 10)
            #draw the level label
            draw_level_label(level, font_menu, white, (50, 50, 150), screen_width -120, 5)
        
        blob_group.draw(screen)
        platform_group.draw(screen)
        lava_group.draw(screen)
        coin_group.draw(screen)
        exit_group.draw(screen)

		# In your main game loop, after drawing other elements:
        for exit in exit_group:
            exit.draw_instruction(screen)
            exit.update()  # For the pulsing effect

        if game_over == 0 and not paused: # Only update player if not game over or paused
            game_over = player.update(game_over)
        
        elif paused:
            action = draw_pause_menu()
            # Handle actions from the pause menu
            if action == 'resume_game': # New condition for the back button
                paused = False # Unpause the game
            if action == 'restart_level':
                # Restart the current level
                world_data = [] # Clear old world data
                world = reset_level(level) # Reset using the current 'level' variable
                game_over = 0
                score = 0
                paused = False
            elif action == 'main_menu':
                # Return to the main menu
                main_menu = True
                paused = False
                level = 0 # Reset level to 0 (or a value that main menu's start button understands as new game)
                world_data = []
                world = World(world_data) # Reinitialize world for main menu state (e.g., empty world)
                game_over = 0
                score = 0
                player.reset(100, screen_height - 130)
                title_animation_start_time = 0 # NEW: Reset animation timer
                show_main_menu_buttons = False
        
        # Show controls hint if needed
        if show_controls and game_started and not paused and game_over == 0:
            draw_controls_hint()
        
        #if player has died
        if game_over == -1:
            # NEW: Draw a semi-transparent black overlay
            overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150)) 
            screen.blit(overlay, (0, 0))
            # Add "Time's Up!" message if that was the cause
            current_time = pygame.time.get_ticks()
            elapsed = (current_time - level_start_time - (countdown_time * 1000)) / 1000
            if elapsed >= level_duration:
                draw_text('TIME\'S UP!, TRY AGAIN', font, white, (screen_width // 2) - 270, screen_height // 4)
    
            # Calculate the centered position for the restart button on the overlay
            restart_button.rect.x = (screen_width - restart_button.image.get_width()) // 2
            restart_button.rect.y = (screen_height - restart_button.image.get_height()) // 2 # Vertically centered
            
            if restart_button.draw():
                # FIX: Restart to the current level
                world_data = [] # Clear any existing world data
                world = reset_level(level) # Call reset_level with the current 'level'
                game_over = 0 # Reset game_over state
                score = 0  # Reset score for the current level
                
        #if player has completed the level
        if game_over == 1:
           # Save high score when level is completed
            save_high_score(player_name, score, level)
            
            #reset game and go to next level
            level += 1
            if level <= max_levels:
                #reset level
                world_data = []
                world = reset_level(level)
                game_over = 0
                game_started = False
            else:
                screen.fill(black) # NEW: Black out the entire screen
                
                # Render and center "YOU WIN!" text on the black screen
                you_win_text_surf = font.render('YOU WIN!', True, blue)
                you_win_text_rect = you_win_text_surf.get_rect(center=(screen_width // 2, screen_height // 2 - 50)) # Slightly above vertical center
                screen.blit(you_win_text_surf, you_win_text_rect)
                
                # Calculate centered position for the restart button, below the text
                restart_button.rect.x = (screen_width - restart_button.image.get_width()) // 2
                restart_button.rect.y = screen_height // 2 + 50 # Placed 50 pixels below the center
                
                if restart_button.draw():
                    level = 1 # Reset to level 1 to start over
                    #reset level
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    score = 0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        # Only toggle pause if not in settings menu
        if event.type == pygame.KEYDOWN and not settings_menu: # Ensure 'P' doesn't toggle pause if settings is open
            if event.key == pygame.K_p: # Toggle pause with 'P' key
                paused = not paused
   
    #draw my alerts above the player character
    now = pygame.time.get_ticks()
    for alert in alerts[:]:
        elapsed = (now - alert['time']) / 1000
        if elapsed > alert.get('duration', ALERT_DURATION):
            alerts.remove(alert)
            continue
        
        alpha = max(0, 255 - int((elapsed / alert.get('duration', ALERT_DURATION)) * 255))
        shake = alert.get('shake_offset', 0)
        offset_x = random.randint(-shake, shake)
        offset_y = random.randint(-shake, shake)

        alert_font = pygame.font.SysFont('Arial', alert.get('size', 20))
        text_color = alert.get('color', (255, 255, 255))
        text_surf = alert_font.render(alert['text'], True, text_color)
        text_surf.set_alpha(alpha)
        
        #create background box with same alpha
        bg_surf = pygame.Surface((text_surf.get_width() + 20, text_surf.get_height() + 10), pygame.SRCALPHA)
        bg_color = (50, 50, 50, alpha) if not alert.get('is_coin', False) else (100, 50, 0, alpha)
        bg_surf.fill(bg_color)
        pygame.draw.rect(bg_surf, (text_color[0], text_color[1], text_color[2], alpha), (0, 0, bg_surf.get_width(), bg_surf.get_height()), 2)

        #position of alert
        x = player.rect.centerx - bg_surf.get_width() // 2 + offset_x
        y = player.rect.top - 40 + offset_y #pixels above the head of character 
        
        screen.blit(bg_surf, (x, y))
        screen.blit(text_surf, (x + 10, y + 5))

    pygame.display.update()

pygame.quit()