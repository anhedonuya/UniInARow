import pygame
import random
import os
import json
import math
import sys
import subprocess
import string
import urllib.request
import hashlib
import time

pygame.init()
pygame.mixer.init()

# --- ПАПКИ И ФАЙЛЫ ---
PLAYERS_FOLDER = "players_data"
PROFILE_FILE = "profile.json"
SETTINGS_FILE = "settings.json"
BAN_FILE = "bans.json"

# --- ПРОВЕРКА ОБНОВЛЕНИЙ ---
def check_updates():
    if not os.path.exists("version.txt"):
        return False, "0.0.0", "0.0.0"
    try:
        with open("version.txt", "r") as f:
            local_version = f.read().strip()
        url = "https://raw.githubusercontent.com/anhedonuya/UniInARow/main/version.txt"
        req = urllib.request.Request(url, headers={"Accept": "text/plain"})
        with urllib.request.urlopen(req, timeout=5) as response:
            remote_version = response.read().decode("utf-8").strip()
        return local_version != remote_version, local_version, remote_version
    except Exception:
        return False, "0.0.0", "0.0.0"

# --- НАСТРОЙКИ ---
DEFAULT_SETTINGS = {
    "fullscreen": False,
    "music_volume": 0.5,
    "sound_effects": True
}
DEFAULT_PROFILE = {
    "player_name": "Игрок",
    "player_id": "",
    "level": 1,
    "xp": 0,
    "total_games": 0,
    "total_score": 0,
    "best_score": 0
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except:
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def generate_player_id():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=6))

def ensure_players_folder():
    if not os.path.exists(PLAYERS_FOLDER):
        os.makedirs(PLAYERS_FOLDER)

def get_all_players():
    ensure_players_folder()
    players = []
    for filename in os.listdir(PLAYERS_FOLDER):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(PLAYERS_FOLDER, filename), "r") as f:
                    data = json.load(f)
                    players.append({
                        "name": data.get("player_name"),
                        "id": data.get("player_id")
                    })
            except:
                pass
    return players

def is_name_taken(name, exclude_id=None):
    players = get_all_players()
    for p in players:
        if p["name"] == name and p["id"] != exclude_id:
            return True
    return False

def save_player_data(data):
    ensure_players_folder()
    filename = os.path.join(PLAYERS_FOLDER, f"{data['player_id']}.json")
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def delete_player_data(player_id):
    filename = os.path.join(PLAYERS_FOLDER, f"{player_id}.json")
    if os.path.exists(filename):
        os.remove(filename)

def load_bans():
    if os.path.exists(BAN_FILE):
        try:
            with open(BAN_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_bans(bans):
    with open(BAN_FILE, "w") as f:
        json.dump(bans, f, indent=4)

def is_developer():
    if os.path.exists("developer.key"):
        try:
            with open("developer.key", "r") as f:
                content = f.read().strip()
                if hashlib.sha256(content.encode()).hexdigest() == "a9f8c3e2b1d4567890abcdef1234567890abcdef1234567890abcdef12345678":
                    return True
        except:
            pass
    return False

def load_profile():
    ensure_players_folder()
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r") as f:
                data = json.load(f)
                # Добавляем level и xp, если их нет
                if "level" not in data:
                    data["level"] = 1
                if "xp" not in data:
                    data["xp"] = 0
                if "player_id" not in data or not data["player_id"]:
                    data["player_id"] = generate_player_id()
                    if is_developer():
                        data["player_id"] = "DEVELOPER"
                save_profile(data)
                save_player_data(data)
                return data
        except:
            pass
    new_profile = DEFAULT_PROFILE.copy()
    new_profile["player_id"] = generate_player_id()
    if is_developer():
        new_profile["player_id"] = "DEVELOPER"
    
    if new_profile["player_id"] != "DEVELOPER":
        if is_name_taken(new_profile["player_name"]):
            new_profile["player_name"] = f"Игрок_{new_profile['player_id'][:4]}"
    
    save_profile(new_profile)
    save_player_data(new_profile)
    return new_profile

def save_profile(profile):
    with open(PROFILE_FILE, "w") as f:
        json.dump(profile, f, indent=4)
    save_player_data(profile)

settings = load_settings()
profile = load_profile()
bans = load_bans()

if profile["player_id"] in bans or profile["player_name"] in bans:
    print("❌ Вы забанены!")
    pygame.quit()
    sys.exit()

# --- РАЗМЕРЫ ОКНА ---
WINDOW_WIDTH, WINDOW_HEIGHT = 600, 700
fullscreen = settings.get("fullscreen", False)

if fullscreen:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()
else:
    WIDTH, HEIGHT = WINDOW_WIDTH, WINDOW_HEIGHT
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption("Uni in a Row")
clock = pygame.time.Clock()

# --- ЦВЕТА ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (40, 40, 40)
DARK_GRAY = (30, 30, 30)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)

# --- РАСЧЁТ РАЗМЕРОВ ЯЧЕЙКИ И ПОЛЯ ---
GRID_SIZE = 6

def recalculate_sizes():
    global CELL_SIZE, MARGIN, TOP_OFFSET
    if fullscreen:
        max_cell_width = (WIDTH - 40) // GRID_SIZE
        max_cell_height = (HEIGHT - 160) // GRID_SIZE
        CELL_SIZE = min(max_cell_width, max_cell_height, 120)
        CELL_SIZE = max(CELL_SIZE, 50)
        MARGIN = (WIDTH - (GRID_SIZE * CELL_SIZE)) // 2
        TOP_OFFSET = (HEIGHT - (GRID_SIZE * CELL_SIZE)) // 2 - 30
    else:
        CELL_SIZE = 70
        MARGIN = (WIDTH - (GRID_SIZE * CELL_SIZE)) // 2
        TOP_OFFSET = 80

recalculate_sizes()

# --- ЗАГРУЗКА ФОНОВ ---
def load_backgrounds():
    bg = {}
    bg_path = "sprites/background.png"
    if os.path.exists(bg_path):
        try:
            bg["normal"] = pygame.image.load(bg_path).convert()
            bg["normal"] = pygame.transform.scale(bg["normal"], (WIDTH, HEIGHT))
        except:
            bg["normal"] = None
    else:
        bg["normal"] = None
    
    bg_full_path = "sprites/background_fullscreen.png"
    if os.path.exists(bg_full_path):
        try:
            bg["fullscreen"] = pygame.image.load(bg_full_path).convert()
            bg["fullscreen"] = pygame.transform.scale(bg["fullscreen"], (WIDTH, HEIGHT))
        except:
            bg["fullscreen"] = None
    else:
        bg["fullscreen"] = None
    
    return bg

backgrounds = load_backgrounds()

def get_current_background():
    if fullscreen and backgrounds["fullscreen"]:
        return backgrounds["fullscreen"]
    elif backgrounds["normal"]:
        return backgrounds["normal"]
    return None

# --- ЗАГРУЗКА МУЗЫКИ ---
music_paths = ["sprites/menu_music.ogg", "sprites/menu_music.wav", "sounds/menu_music.ogg", "sounds/menu_music.wav"]
music_loaded = False
music_started = False

for path in music_paths:
    if os.path.exists(path):
        try:
            pygame.mixer.music.load(path)
            music_loaded = True
            pygame.mixer.music.set_volume(settings.get("music_volume", 0.5))
            break
        except:
            pass

# --- ЗАГРУЗКА СПРАЙТОВ ---
def load_sprites():
    sprites = {}
    colors = ["blue", "green", "red", "yellow", "purple"]
    for color in colors:
        path = f"sprites/uni_{color}.png"
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (CELL_SIZE - 10, CELL_SIZE - 10))
            sprites[color] = img
        else:
            surf = pygame.Surface((CELL_SIZE - 10, CELL_SIZE - 10))
            surf.fill(pygame.Color(color))
            sprites[color] = surf
    return sprites

sprites = load_sprites()
colors_list = list(sprites.keys())

# --- ФУНКЦИИ СОХРАНЕНИЯ ИГРЫ ---
def get_save_path():
    if not os.path.exists("saves"):
        os.makedirs("saves")
    return "saves/save.dat"

def save_game(grid_data, score_val):
    data = {
        "grid": grid_data,
        "score": score_val,
        "version": 1,
        "player_id": profile["player_id"],
        "player_name": profile["player_name"]
    }
    with open(get_save_path(), "w") as f:
        json.dump(data, f)
    update_profile(score_val)

def load_game():
    path = get_save_path()
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        data = json.load(f)
    return data

def has_save():
    return os.path.exists(get_save_path())

# --- ПРОФИЛЬ И УРОВНИ ---
def calculate_xp(score):
    """Рассчитывает XP за игру."""
    return score * 2 + 10

def check_level_up():
    """Проверяет повышение уровня."""
    global profile
    xp_needed = profile['level'] * 50 + 20
    while profile['xp'] >= xp_needed:
        profile['xp'] -= xp_needed
        profile['level'] += 1
        xp_needed = profile['level'] * 50 + 20
        print(f"🎉 Уровень повышен до {profile['level']}!")

def update_profile(score):
    global profile
    if score > 0:
        xp_gain = calculate_xp(score)
        profile['xp'] += xp_gain
        profile['total_games'] += 1
        profile['total_score'] += score
        if score > profile['best_score']:
            profile['best_score'] = score
        
        check_level_up()
        save_profile(profile)
        save_player_data(profile)

def draw_profile_on_menu():
    bg_surf = pygame.Surface((280, 140), pygame.SRCALPHA)
    bg_surf.fill((0, 0, 0, 180))
    screen.blit(bg_surf, (WIDTH - 300, 10))
    
    name_text = font.render(profile["player_name"], True, WHITE)
    screen.blit(name_text, (WIDTH - 290, 15))
    
    id_text = small_font.render(f"ID: {profile['player_id']}", True, (200, 200, 200))
    screen.blit(id_text, (WIDTH - 290, 40))
    
    level_text = small_font.render(f"Уровень: {profile['level']}  XP: {profile['xp']}", True, (255, 255, 100))
    screen.blit(level_text, (WIDTH - 290, 60))
    
    stats = f"Игр: {profile['total_games']}  Рекорд: {profile['best_score']}"
    stats_text = small_font.render(stats, True, (180, 180, 180))
    screen.blit(stats_text, (WIDTH - 290, 80))
    
    total_text = small_font.render(f"Всего очков: {profile['total_score']}", True, (150, 150, 150))
    screen.blit(total_text, (WIDTH - 290, 100))
    
    draw_xp_bar()

def draw_xp_bar():
    """Рисует полоску прогресса XP в профиле."""
    xp_needed = profile['level'] * 50 + 20
    progress = min(profile['xp'] / xp_needed, 1.0)
    bar_width = 200
    bar_height = 10
    bar_x = WIDTH - 290
    bar_y = 115
    
    pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height), border_radius=4)
    pygame.draw.rect(screen, (100, 200, 100), (bar_x, bar_y, int(bar_width * progress), bar_height), border_radius=4)
    
    percent_text = small_font.render(f"{int(progress * 100)}%", True, (200, 200, 200))
    screen.blit(percent_text, (bar_x + bar_width + 10, bar_y - 2))

# --- ИГРОВОЕ ПОЛЕ ---
def create_grid():
    return [[random.choice(colors_list) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

grid = create_grid()
selected = None
score = 0
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 72)
small_font = pygame.font.Font(None, 20)

# --- СОСТОЯНИЯ ---
MENU = 0
PLAYING = 1
GAME_OVER = 2
SETTINGS_MENU = 3
UPDATE_AVAILABLE = 4
game_state = MENU

# --- АНИМАЦИИ ---
animations = []
error_animations = []
drag_start_cell = None
gear_rotation = 0
gear_open = False
gear_animating = False
gear_target_rotation = 0

class SwapAnimation:
    def __init__(self, r1, c1, r2, c2, duration=200):
        self.r1, self.c1 = r1, c1
        self.r2, self.c2 = r2, c2
        self.start_time = pygame.time.get_ticks()
        self.duration = duration
        self.finished = False

    def update(self):
        if self.finished:
            return
        t = (pygame.time.get_ticks() - self.start_time) / self.duration
        if t >= 1:
            t = 1
            self.finished = True
        x1 = MARGIN + self.c1 * CELL_SIZE + CELL_SIZE // 2
        y1 = TOP_OFFSET + self.r1 * CELL_SIZE + CELL_SIZE // 2
        x2 = MARGIN + self.c2 * CELL_SIZE + CELL_SIZE // 2
        y2 = TOP_OFFSET + self.r2 * CELL_SIZE + CELL_SIZE // 2
        dx = (x2 - x1) * t
        dy = (y2 - y1) * t
        self.pos = (x1 + dx, y1 + dy)

    def draw(self, screen):
        if self.finished:
            return
        x, y = self.pos
        color1 = grid[self.r1][self.c1]
        color2 = grid[self.r2][self.c2]
        if color1 in sprites:
            sprite = sprites[color1]
            sx = x - CELL_SIZE//2 + (CELL_SIZE - sprite.get_width()) // 2
            sy = y - CELL_SIZE//2 + (CELL_SIZE - sprite.get_height()) // 2
            screen.blit(sprite, (sx, sy))
        x2 = 2*MARGIN + self.c1*CELL_SIZE + self.c2*CELL_SIZE + CELL_SIZE - x
        y2 = 2*TOP_OFFSET + self.r1*CELL_SIZE + self.r2*CELL_SIZE + CELL_SIZE - y
        if color2 in sprites:
            sprite = sprites[color2]
            sx = x2 - CELL_SIZE//2 + (CELL_SIZE - sprite.get_width()) // 2
            sy = y2 - CELL_SIZE//2 + (CELL_SIZE - sprite.get_height()) // 2
            screen.blit(sprite, (sx, sy))

class RemoveAnimation:
    def __init__(self, matches, duration=300):
        self.matches = list(matches)
        self.start_time = pygame.time.get_ticks()
        self.duration = duration
        self.finished = False

    def update(self):
        if self.finished:
            return
        t = (pygame.time.get_ticks() - self.start_time) / self.duration
        if t >= 1:
            t = 1
            self.finished = True

    def draw(self, screen):
        if self.finished:
            return
        t = (pygame.time.get_ticks() - self.start_time) / self.duration
        if t >= 1:
            t = 1
        alpha = int(255 * (1 - t))
        for row, col in self.matches:
            color = grid[row][col]
            if color in sprites:
                sprite = sprites[color].copy()
                sprite.set_alpha(alpha)
                x = MARGIN + col * CELL_SIZE + (CELL_SIZE - sprite.get_width()) // 2
                y = TOP_OFFSET + row * CELL_SIZE + (CELL_SIZE - sprite.get_height()) // 2
                screen.blit(sprite, (x, y))

class DropAnimation:
    def __init__(self, drop_info, duration=300):
        self.drop_info = drop_info
        self.start_time = pygame.time.get_ticks()
        self.duration = duration
        self.finished = False

    def update(self):
        if self.finished:
            return
        t = (pygame.time.get_ticks() - self.start_time) / self.duration
        if t >= 1:
            t = 1
            self.finished = True

    def draw(self, screen):
        if self.finished:
            return
        t = (pygame.time.get_ticks() - self.start_time) / self.duration
        if t >= 1:
            t = 1
        for row, col, color, start_row in self.drop_info:
            if color in sprites:
                sprite = sprites[color]
                y_offset = (start_row - row) * CELL_SIZE * (1 - t)
                x = MARGIN + col * CELL_SIZE + (CELL_SIZE - sprite.get_width()) // 2
                y = TOP_OFFSET + row * CELL_SIZE + (CELL_SIZE - sprite.get_height()) // 2 + y_offset
                screen.blit(sprite, (x, y))

class ErrorAnimation:
    def __init__(self, row, col, duration=300):
        self.row = row
        self.col = col
        self.start_time = pygame.time.get_ticks()
        self.duration = duration
        self.finished = False
        self.shake_offset = (0, 0)
        self.phase = 0

    def update(self):
        if self.finished:
            return
        t = (pygame.time.get_ticks() - self.start_time) / self.duration
        if t >= 1:
            t = 1
            self.finished = True
        intensity = max(0, (1 - t) * 8)
        self.shake_offset = (intensity * math.sin(t * 30), intensity * math.cos(t * 20))
        self.phase = t

    def draw(self, screen):
        if self.finished:
            return
        x = MARGIN + self.col * CELL_SIZE
        y = TOP_OFFSET + self.row * CELL_SIZE
        t = (pygame.time.get_ticks() - self.start_time) / self.duration
        if t >= 1:
            t = 1
        alpha = int(150 * (1 - t))
        flash_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        flash_surf.fill((255, 0, 0, alpha))
        screen.blit(flash_surf, (x + self.shake_offset[0], y + self.shake_offset[1]))

def add_error_animation(row, col):
    error_animations.append(ErrorAnimation(row, col))

def add_error_animation_pair(r1, c1, r2, c2):
    add_error_animation(r1, c1)
    add_error_animation(r2, c2)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_cell(pos):
    x, y = pos
    if x < MARGIN or y < TOP_OFFSET:
        return None
    col = (x - MARGIN) // CELL_SIZE
    row = (y - TOP_OFFSET) // CELL_SIZE
    if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
        return (row, col)
    return None

def find_matches():
    matches = set()
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE - 2):
            if grid[row][col] == grid[row][col+1] == grid[row][col+2]:
                matches.add((row, col))
                matches.add((row, col+1))
                matches.add((row, col+2))
    for row in range(GRID_SIZE - 2):
        for col in range(GRID_SIZE):
            if grid[row][col] == grid[row+1][col] == grid[row+2][col]:
                matches.add((row, col))
                matches.add((row+1, col))
                matches.add((row+2, col))
    return matches

def remove_matches(matches):
    for row, col in matches:
        grid[row][col] = None

def drop_down():
    drop_info = []
    for col in range(GRID_SIZE):
        for row in range(GRID_SIZE-1, -1, -1):
            if grid[row][col] is None:
                for r in range(row-1, -1, -1):
                    if grid[r][col] is not None:
                        grid[row][col] = grid[r][col]
                        grid[r][col] = None
                        drop_info.append((row, col, grid[row][col], r))
                        break
    for col in range(GRID_SIZE):
        for row in range(GRID_SIZE):
            if grid[row][col] is None:
                new_color = random.choice(colors_list)
                grid[row][col] = new_color
                drop_info.append((row, col, new_color, -1))
    return drop_info

def swap_cells(r1, c1, r2, c2):
    grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]
    if find_matches():
        return True
    grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]
    return False

def draw_grid():
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            x = MARGIN + col * CELL_SIZE
            y = TOP_OFFSET + row * CELL_SIZE
            pygame.draw.rect(screen, DARK_GRAY, (x-2, y-2, CELL_SIZE+4, CELL_SIZE+4))
            pygame.draw.rect(screen, GRAY, (x, y, CELL_SIZE, CELL_SIZE))
            color = grid[row][col]
            if color in sprites:
                sprite = sprites[color]
                sx = x + (CELL_SIZE - sprite.get_width()) // 2
                sy = y + (CELL_SIZE - sprite.get_height()) // 2
                screen.blit(sprite, (sx, sy))
            if selected and selected == (row, col):
                pygame.draw.rect(screen, WHITE, (x-3, y-3, CELL_SIZE+6, CELL_SIZE+6), 3)

def draw_title(text, x, y, size=72):
    font_big = pygame.font.Font(None, size)
    text_surf = font_big.render(text, True, WHITE)
    text_rect = text_surf.get_rect(center=(x, y))
    shadow_surf = font_big.render(text, True, (30, 30, 30))
    shadow_rect = text_rect.copy()
    shadow_rect.x += 4
    shadow_rect.y += 4
    screen.blit(shadow_surf, shadow_rect)
    shadow2_surf = font_big.render(text, True, (60, 60, 60))
    shadow2_rect = text_rect.copy()
    shadow2_rect.x += 2
    shadow2_rect.y += 2
    screen.blit(shadow2_surf, shadow2_rect)
    colors = [(255, 200, 50), (255, 180, 30), (200, 150, 50)]
    for i, col in enumerate(colors):
        surf = font_big.render(text, True, col)
        rect = text_rect.copy()
        rect.x += i * 1
        rect.y += i * 1
        screen.blit(surf, rect)
    highlight_surf = font_big.render(text, True, (255, 240, 200))
    screen.blit(highlight_surf, text_rect)
    border_rect = text_rect.inflate(30, 20)
    pygame.draw.rect(screen, (100, 80, 30), border_rect, 2, border_radius=10)
    outer_rect = border_rect.inflate(10, 10)
    pygame.draw.rect(screen, (60, 50, 20), outer_rect, 1, border_radius=12)

def draw_update_notification():
    screen.fill(BLACK)
    bg = get_current_background()
    if bg:
        screen.blit(bg, (0, 0))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))
    box_width, box_height = 400, 200
    box_x = (WIDTH - box_width) // 2
    box_y = (HEIGHT - box_height) // 2
    pygame.draw.rect(screen, (30, 30, 30), (box_x, box_y, box_width, box_height), border_radius=15)
    pygame.draw.rect(screen, WHITE, (box_x, box_y, box_width, box_height), 2, border_radius=15)
    title = big_font.render("Обновление!", True, YELLOW)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, box_y + 20))
    info_text = font.render("Доступна новая версия игры", True, WHITE)
    screen.blit(info_text, (WIDTH//2 - info_text.get_width()//2, box_y + 70))
    update_btn = pygame.Rect(box_x + 100, box_y + 130, 200, 50)
    pygame.draw.rect(screen, GREEN, update_btn, border_radius=10)
    update_text = font.render("Обновить", True, WHITE)
    screen.blit(update_text, (update_btn.x + 55, update_btn.y + 12))
    return update_btn

def draw_gear_button():
    """Рисует кнопку-шестерёнку в правом нижнем углу"""
    global gear_rotation, gear_open, gear_animating, gear_target_rotation
    
    btn_size = 50
    btn_x = WIDTH - btn_size - 15
    btn_y = HEIGHT - btn_size - 15
    
    if gear_animating:
        if gear_rotation < gear_target_rotation:
            gear_rotation += 6
            if gear_rotation >= gear_target_rotation:
                gear_rotation = gear_target_rotation
                gear_animating = False
        elif gear_rotation > gear_target_rotation:
            gear_rotation -= 6
            if gear_rotation <= gear_target_rotation:
                gear_rotation = gear_target_rotation
                gear_animating = False
    
    pygame.draw.circle(screen, (60, 60, 60), (btn_x + btn_size//2, btn_y + btn_size//2), btn_size//2 + 4)
    pygame.draw.circle(screen, (40, 40, 40), (btn_x + btn_size//2, btn_y + btn_size//2), btn_size//2 + 2)
    pygame.draw.circle(screen, (80, 80, 80), (btn_x + btn_size//2, btn_y + btn_size//2), btn_size//2)
    
    center_x = btn_x + btn_size//2
    center_y = btn_y + btn_size//2
    radius = 18
    tooth_count = 8
    tooth_size = 6
    
    for i in range(tooth_count):
        angle = math.radians(i * 360 / tooth_count + gear_rotation)
        x1 = center_x + radius * math.cos(angle)
        y1 = center_y + radius * math.sin(angle)
        x2 = center_x + (radius + tooth_size) * math.cos(angle)
        y2 = center_y + (radius + tooth_size) * math.sin(angle)
        pygame.draw.line(screen, (180, 180, 180), (x1, y1), (x2, y2), 4)
    
    pygame.draw.circle(screen, (180, 180, 180), (center_x, center_y), radius - 4)
    pygame.draw.circle(screen, (100, 100, 100), (center_x, center_y), radius - 8)
    pygame.draw.circle(screen, (60, 60, 60), (center_x, center_y), 6)
    
    if gear_open:
        menu_bg = pygame.Surface((180, 100), pygame.SRCALPHA)
        menu_bg.fill((0, 0, 0, 220))
        screen.blit(menu_bg, (btn_x - 140, btn_y - 110))
        pygame.draw.rect(screen, WHITE, (btn_x - 140, btn_y - 110, 180, 100), 1, border_radius=8)
        
        save_btn = pygame.Rect(btn_x - 130, btn_y - 100, 160, 35)
        pygame.draw.rect(screen, (0, 150, 0), save_btn, border_radius=6)
        save_text = small_font.render("Сохранить и выйти", True, WHITE)
        screen.blit(save_text, (save_btn.x + 10, save_btn.y + 8))
        
        menu_btn = pygame.Rect(btn_x - 130, btn_y - 55, 160, 35)
        pygame.draw.rect(screen, (150, 150, 0), menu_btn, border_radius=6)
        menu_text = small_font.render("Выйти в меню", True, WHITE)
        screen.blit(menu_text, (menu_btn.x + 25, menu_btn.y + 8))
        
        return save_btn, menu_btn
    
    return None, None

def draw_menu():
    screen.fill(BLACK)
    bg = get_current_background()
    if bg:
        screen.blit(bg, (0, 0))
    draw_title("Uni in a Row", WIDTH//2, 120, 72 if not fullscreen else 96)
    btn_width, btn_height = 200, 50
    btn_x = WIDTH//2 - btn_width//2
    has_save_flag = has_save()
    y_start = 250 if not fullscreen else 300
    new_btn = pygame.Rect(btn_x, y_start, btn_width, btn_height)
    load_btn = pygame.Rect(btn_x, y_start + 80, btn_width, btn_height)
    settings_btn = pygame.Rect(btn_x, y_start + 160, btn_width, btn_height)
    exit_btn = pygame.Rect(btn_x, y_start + 240, btn_width, btn_height)
    for btn, color in [(new_btn, GREEN), (load_btn, BLUE if has_save_flag else GRAY), (settings_btn, (100, 100, 200)), (exit_btn, RED)]:
        shadow_btn = btn.copy()
        shadow_btn.y += 4
        pygame.draw.rect(screen, (0,0,0), shadow_btn, border_radius=12)
        pygame.draw.rect(screen, color, btn, border_radius=12)
    new_text = font.render("Новая игра", True, WHITE)
    load_text = font.render("Загрузить", True, WHITE)
    settings_text = font.render("Настройки", True, WHITE)
    exit_text = font.render("Выход", True, WHITE)
    screen.blit(new_text, (WIDTH//2 - new_text.get_width()//2, y_start + 12))
    screen.blit(load_text, (WIDTH//2 - load_text.get_width()//2, y_start + 92))
    screen.blit(settings_text, (WIDTH//2 - settings_text.get_width()//2, y_start + 172))
    screen.blit(exit_text, (WIDTH//2 - exit_text.get_width()//2, y_start + 252))
    if not has_save_flag:
        no_save_text = small_font.render("(нет сохранения)", True, (150,150,150))
        screen.blit(no_save_text, (WIDTH//2 - no_save_text.get_width()//2, y_start + 50))
    draw_profile_on_menu()
    if profile["player_id"] == "DEVELOPER":
        admin_btn = pygame.Rect(WIDTH - 170, 130, 150, 30)
        pygame.draw.rect(screen, (100, 0, 100), admin_btn, border_radius=8)
        admin_text = font.render("Админ панель", True, WHITE)
        screen.blit(admin_text, (WIDTH - 160, 135))
        return new_btn, load_btn, settings_btn, exit_btn, admin_btn
    return new_btn, load_btn, settings_btn, exit_btn

def draw_settings_menu():
    screen.fill(BLACK)
    bg = get_current_background()
    if bg:
        screen.blit(bg, (0, 0))
    draw_title("Настройки", WIDTH//2, 120, 60)
    btn_width, btn_height = 250, 50
    btn_x = WIDTH//2 - btn_width//2
    y_start = 230 if not fullscreen else 280
    fs_btn = pygame.Rect(btn_x, y_start, btn_width, btn_height)
    vol_btn = pygame.Rect(btn_x, y_start + 70, btn_width, btn_height)
    name_btn = pygame.Rect(btn_x, y_start + 140, btn_width, btn_height)
    back_btn = pygame.Rect(btn_x, y_start + 210, btn_width, btn_height)
    fs_color = GREEN if settings.get("fullscreen", False) else GRAY
    pygame.draw.rect(screen, fs_color, fs_btn, border_radius=12)
    fs_text = font.render(f"Полный экран: {'Вкл' if settings.get('fullscreen', False) else 'Выкл'}", True, WHITE)
    screen.blit(fs_text, (WIDTH//2 - fs_text.get_width()//2, y_start + 12))
    vol_color = (100, 100, 200)
    pygame.draw.rect(screen, vol_color, vol_btn, border_radius=12)
    vol_val = int(settings.get("music_volume", 0.5) * 100)
    vol_text = font.render(f"Громкость: {vol_val}% (← →)", True, WHITE)
    screen.blit(vol_text, (WIDTH//2 - vol_text.get_width()//2, y_start + 82))
    name_color = (100, 200, 100)
    pygame.draw.rect(screen, name_color, name_btn, border_radius=12)
    name_text = font.render(f"Имя: {profile['player_name']}", True, WHITE)
    screen.blit(name_text, (WIDTH//2 - name_text.get_width()//2, y_start + 152))
    pygame.draw.rect(screen, RED, back_btn, border_radius=12)
    back_text = font.render("Назад", True, WHITE)
    screen.blit(back_text, (WIDTH//2 - back_text.get_width()//2, y_start + 222))
    return fs_btn, vol_btn, name_btn, back_btn

def draw_game_over():
    screen.fill(BLACK)
    bg = get_current_background()
    if bg:
        screen.blit(bg, (0, 0))
    game_over_text = big_font.render("Игра окончена!", True, RED)
    screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, 150))
    score_text = font.render(f"Счёт: {score}", True, WHITE)
    screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 250))
    best_text = small_font.render(f"Рекорд: {profile['best_score']}  Всего очков: {profile['total_score']}", True, (200,200,200))
    screen.blit(best_text, (WIDTH//2 - best_text.get_width()//2, 290))
    restart_btn = pygame.Rect(WIDTH//2 - 80, 350, 160, 50)
    exit_btn = pygame.Rect(WIDTH//2 - 80, 450, 160, 50)
    for btn, color in [(restart_btn, GREEN), (exit_btn, RED)]:
        shadow_btn = btn.copy()
        shadow_btn.y += 4
        pygame.draw.rect(screen, (0,0,0), shadow_btn, border_radius=12)
        pygame.draw.rect(screen, color, btn, border_radius=12)
    restart_text = font.render("Новая игра", True, WHITE)
    exit_text = font.render("Выход", True, WHITE)
    screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, 360))
    screen.blit(exit_text, (WIDTH//2 - exit_text.get_width()//2, 460))
    return restart_btn, exit_btn

def toggle_fullscreen():
    global fullscreen, screen, WIDTH, HEIGHT, backgrounds
    fullscreen = not fullscreen
    settings["fullscreen"] = fullscreen
    save_settings(settings)
    if fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        WIDTH, HEIGHT = screen.get_width(), screen.get_height()
    else:
        WIDTH, HEIGHT = WINDOW_WIDTH, WINDOW_HEIGHT
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
    backgrounds = load_backgrounds()
    recalculate_sizes()
    pygame.display.flip()

def run_updater():
    try:
        subprocess.Popen([sys.executable, "updater.py"])
        pygame.quit()
        sys.exit(0)
    except:
        pass

def open_admin_panel():
    try:
        import admin_panel
        admin_panel.show_admin_panel(screen, font, small_font, WIDTH, HEIGHT, profile)
    except ImportError:
        print("admin_panel.py не найден")
    except Exception as e:
        print(f"Ошибка: {e}")

# --- ГЛАВНЫЙ ЦИКЛ ---
recalculate_sizes()
has_update, local_ver, remote_ver = check_updates()
if has_update:
    game_state = UPDATE_AVAILABLE

running = True
input_active = False
input_text = ""
error_message = ""
error_timer = 0

while running:
    if music_loaded and not music_started:
        pygame.mixer.music.play(-1)
        music_started = True
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if game_state == PLAYING and score > 0:
                update_profile(score)
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                toggle_fullscreen()
            if event.key == pygame.K_ESCAPE:
                if game_state == SETTINGS_MENU:
                    game_state = MENU
                elif game_state == PLAYING:
                    if score > 0:
                        update_profile(score)
                    game_state = MENU
                    selected = None
                    drag_start_cell = None
                    gear_open = False
                    gear_target_rotation = 0
                    gear_rotation = 0
                    gear_animating = False
                elif game_state == UPDATE_AVAILABLE:
                    running = False
            if game_state == SETTINGS_MENU:
                if event.key == pygame.K_LEFT:
                    new_vol = settings.get("music_volume", 0.5) - 0.05
                    settings["music_volume"] = max(0.0, new_vol)
                    pygame.mixer.music.set_volume(settings["music_volume"])
                    save_settings(settings)
                elif event.key == pygame.K_RIGHT:
                    new_vol = settings.get("music_volume", 0.5) + 0.05
                    settings["music_volume"] = min(1.0, new_vol)
                    pygame.mixer.music.set_volume(settings["music_volume"])
                    save_settings(settings)
            if input_active:
                if event.key == pygame.K_RETURN:
                    new_name = input_text.strip()
                    if new_name:
                        if is_name_taken(new_name, exclude_id=profile["player_id"]):
                            error_message = "❌ Это имя уже занято!"
                            error_timer = 90
                        else:
                            delete_player_data(profile["player_id"])
                            profile["player_name"] = new_name
                            save_profile(profile)
                            save_player_data(profile)
                            input_active = False
                            input_text = ""
                    else:
                        input_active = False
                        input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            
            if game_state == UPDATE_AVAILABLE:
                update_btn = draw_update_notification()
                if update_btn.collidepoint(pos):
                    run_updater()
            
            elif game_state == MENU:
                if profile["player_id"] == "DEVELOPER":
                    new_btn, load_btn, settings_btn, exit_btn, admin_btn = draw_menu()
                    if admin_btn.collidepoint(pos):
                        open_admin_panel()
                else:
                    new_btn, load_btn, settings_btn, exit_btn = draw_menu()
                if new_btn.collidepoint(pos):
                    grid = create_grid()
                    score = 0
                    selected = None
                    animations = []
                    error_animations = []
                    game_state = PLAYING
                    if os.path.exists(get_save_path()):
                        os.remove(get_save_path())
                elif load_btn.collidepoint(pos) and has_save():
                    data = load_game()
                    if data:
                        grid = data["grid"]
                        score = data["score"]
                        selected = None
                        animations = []
                        error_animations = []
                        game_state = PLAYING
                elif settings_btn.collidepoint(pos):
                    game_state = SETTINGS_MENU
                elif exit_btn.collidepoint(pos):
                    running = False
            
            elif game_state == SETTINGS_MENU:
                fs_btn, vol_btn, name_btn, back_btn = draw_settings_menu()
                if fs_btn.collidepoint(pos):
                    toggle_fullscreen()
                elif name_btn.collidepoint(pos):
                    input_active = True
                    input_text = ""
                elif back_btn.collidepoint(pos):
                    game_state = MENU
            
            elif game_state == GAME_OVER:
                restart_btn, exit_btn = draw_game_over()
                if restart_btn.collidepoint(pos):
                    grid = create_grid()
                    score = 0
                    selected = None
                    animations = []
                    error_animations = []
                    game_state = PLAYING
                    if os.path.exists(get_save_path()):
                        os.remove(get_save_path())
                elif exit_btn.collidepoint(pos):
                    running = False
            
            elif game_state == PLAYING:
                btn_size = 50
                btn_x = WIDTH - btn_size - 15
                btn_y = HEIGHT - btn_size - 15
                gear_rect = pygame.Rect(btn_x, btn_y, btn_size, btn_size)
                if gear_rect.collidepoint(pos):
                    if gear_open:
                        gear_open = False
                        gear_target_rotation = 0
                        gear_animating = True
                    else:
                        gear_open = True
                        gear_target_rotation = 360
                        gear_animating = True
                    continue
                
                if gear_open:
                    save_btn, menu_btn = draw_gear_button()
                    if save_btn and save_btn.collidepoint(pos):
                        save_game(grid, score)
                        running = False
                        continue
                    if menu_btn and menu_btn.collidepoint(pos):
                        if score > 0:
                            update_profile(score)
                        game_state = MENU
                        selected = None
                        drag_start_cell = None
                        gear_open = False
                        gear_target_rotation = 0
                        gear_rotation = 0
                        gear_animating = False
                        continue
                
                cell = get_cell(pos)
                if cell:
                    drag_start_cell = cell
                    selected = cell
        
        if event.type == pygame.MOUSEMOTION and game_state == PLAYING and drag_start_cell is not None:
            pos = pygame.mouse.get_pos()
            current_cell = get_cell(pos)
            if current_cell and current_cell != drag_start_cell:
                r1, c1 = drag_start_cell
                r2, c2 = current_cell
                if abs(r1-r2) + abs(c1-c2) == 1:
                    if swap_cells(r1, c1, r2, c2):
                        animations.append(SwapAnimation(r1, c1, r2, c2))
                        selected = None
                        drag_start_cell = None
                    else:
                        add_error_animation_pair(r1, c1, r2, c2)
                        selected = None
                        drag_start_cell = None
                else:
                    add_error_animation_pair(r1, c1, r2, c2)
                    selected = None
                    drag_start_cell = None
        
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if game_state == PLAYING:
                if drag_start_cell is not None:
                    pos = pygame.mouse.get_pos()
                    current_cell = get_cell(pos)
                    if current_cell and current_cell != drag_start_cell:
                        r1, c1 = drag_start_cell
                        r2, c2 = current_cell
                        if abs(r1-r2) + abs(c1-c2) == 1:
                            if not swap_cells(r1, c1, r2, c2):
                                add_error_animation_pair(r1, c1, r2, c2)
                            else:
                                animations.append(SwapAnimation(r1, c1, r2, c2))
                        else:
                            add_error_animation_pair(r1, c1, r2, c2)
                    drag_start_cell = None
                    selected = None

    if game_state == PLAYING:
        if not animations and not error_animations:
            matches = find_matches()
            if matches:
                animations.append(RemoveAnimation(matches))
                remove_matches(matches)
                drop_info = drop_down()
                if drop_info:
                    animations.append(DropAnimation(drop_info))
                score += 1
            elif not any(cell is not None for row in grid for cell in row):
                game_state = GAME_OVER
                update_profile(score)

        for anim in animations:
            anim.update()
        animations = [a for a in animations if not a.finished]
        
        for anim in error_animations:
            anim.update()
        error_animations = [a for a in error_animations if not a.finished]

    if game_state == MENU:
        draw_menu()
    elif game_state == SETTINGS_MENU:
        draw_settings_menu()
    elif game_state == GAME_OVER:
        draw_game_over()
    elif game_state == UPDATE_AVAILABLE:
        draw_update_notification()
    else:
        screen.fill(BLACK)
        bg = get_current_background()
        if bg:
            screen.blit(bg, (0, 0))
        draw_grid()
        for anim in error_animations:
            anim.draw(screen)
        for anim in animations:
            anim.draw(screen)
        
        score_text = font.render(f"Счёт: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        level_text = small_font.render(f"Ур. {profile['level']}", True, (200, 200, 100))
        screen.blit(level_text, (WIDTH - 80, 10))
        
        draw_gear_button()
        
        hint_text = small_font.render("F11 — полный экран", True, (100,100,100))
        screen.blit(hint_text, (WIDTH - hint_text.get_width() - 10, HEIGHT - 30))

    if input_active:
        input_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        input_surf.fill((0, 0, 0, 200))
        screen.blit(input_surf, (0, 0))
        prompt = font.render("Введите имя:", True, WHITE)
        screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2 - 60))
        input_box = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 20, 300, 40)
        pygame.draw.rect(screen, WHITE, input_box, 2)
        text_surf = font.render(input_text + "|", True, WHITE)
        screen.blit(text_surf, (input_box.x + 10, input_box.y + 5))
        if error_message and error_timer > 0:
            err_surf = font.render(error_message, True, RED)
            screen.blit(err_surf, (WIDTH//2 - err_surf.get_width()//2, HEIGHT//2 + 40))
            error_timer -= 1
        else:
            error_message = ""
        pygame.display.flip()
        continue

    pygame.display.flip()
    clock.tick(60)

pygame.quit()