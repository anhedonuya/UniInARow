import pygame
import random
import os
import json
import math
import sys

pygame.init()
pygame.mixer.init()

# --- НАСТРОЙКИ ПО УМОЛЧАНИЮ ---
SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
    "fullscreen": False,
    "music_volume": 0.5,
    "sound_effects": True
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

settings = load_settings()

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

# --- РАСЧЁТ РАЗМЕРОВ ЯЧЕЙКИ И ПОЛЯ ---
GRID_SIZE = 6

def recalculate_sizes():
    global CELL_SIZE, MARGIN, TOP_OFFSET
    if fullscreen:
        # Для полного экрана: максимально возможный размер ячейки
        max_cell_width = (WIDTH - 40) // GRID_SIZE
        max_cell_height = (HEIGHT - 160) // GRID_SIZE
        CELL_SIZE = min(max_cell_width, max_cell_height, 120)  # Не больше 120 для красоты
        CELL_SIZE = max(CELL_SIZE, 50)  # Минимум 50, чтобы было видно
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
music_paths = [
    "sprites/menu_music.ogg",
    "sprites/menu_music.wav",
    "sounds/menu_music.ogg",
    "sounds/menu_music.wav"
]
music_loaded = False
music_started = False

for path in music_paths:
    if os.path.exists(path):
        try:
            pygame.mixer.music.load(path)
            music_loaded = True
            print("🎵 Музыка загружена:", path)
            pygame.mixer.music.set_volume(settings.get("music_volume", 0.5))
            break
        except Exception as e:
            print("⚠️ Ошибка загрузки музыки:", e)

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

# --- ФУНКЦИИ СОХРАНЕНИЯ ---
def get_save_path():
    if not os.path.exists("saves"):
        os.makedirs("saves")
    return "saves/save.dat"

def save_game(grid_data, score_val):
    data = {
        "grid": grid_data,
        "score": score_val,
        "version": 1
    }
    with open(get_save_path(), "w") as f:
        json.dump(data, f)

def load_game():
    path = get_save_path()
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        data = json.load(f)
    return data

def has_save():
    return os.path.exists(get_save_path())

# --- ИГРОВОЕ ПОЛЕ ---
def create_grid():
    return [[random.choice(colors_list) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

grid = create_grid()
selected = None
score = 0
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 72)
small_font = pygame.font.Font(None, 24)

# --- СОСТОЯНИЯ ---
MENU = 0
PLAYING = 1
GAME_OVER = 2
SETTINGS_MENU = 3
game_state = MENU

# --- АНИМАЦИИ ---
animations = []
error_animations = []
drag_start_cell = None

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
    
    colors = [
        (255, 200, 50),
        (255, 180, 30),
        (200, 150, 50),
    ]
    
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
    
    for btn, color in [(new_btn, GREEN), 
                       (load_btn, BLUE if has_save_flag else GRAY),
                       (settings_btn, (100, 100, 200)),
                       (exit_btn, RED)]:
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
    back_btn = pygame.Rect(btn_x, y_start + 140, btn_width, btn_height)
    
    fs_color = GREEN if settings.get("fullscreen", False) else GRAY
    pygame.draw.rect(screen, fs_color, fs_btn, border_radius=12)
    fs_text = font.render(f"Полный экран: {'Вкл' if settings.get('fullscreen', False) else 'Выкл'}", True, WHITE)
    screen.blit(fs_text, (WIDTH//2 - fs_text.get_width()//2, y_start + 12))
    
    vol_color = (100, 100, 200)
    pygame.draw.rect(screen, vol_color, vol_btn, border_radius=12)
    vol_val = int(settings.get("music_volume", 0.5) * 100)
    vol_text = font.render(f"Громкость: {vol_val}% (← →)", True, WHITE)
    screen.blit(vol_text, (WIDTH//2 - vol_text.get_width()//2, y_start + 82))
    
    pygame.draw.rect(screen, RED, back_btn, border_radius=12)
    back_text = font.render("Назад", True, WHITE)
    screen.blit(back_text, (WIDTH//2 - back_text.get_width()//2, y_start + 152))
    
    return fs_btn, vol_btn, back_btn

def draw_game_over():
    screen.fill(BLACK)
    bg = get_current_background()
    if bg:
        screen.blit(bg, (0, 0))
    game_over_text = big_font.render("Игра окончена!", True, RED)
    screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, 150))
    
    score_text = font.render(f"Счёт: {score}", True, WHITE)
    screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 250))
    
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

# --- ОБНОВЛЕНИЕ ЭКРАНА ПРИ ИЗМЕНЕНИИ РАЗМЕРА ---
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

# --- ГЛАВНЫЙ ЦИКЛ ---
recalculate_sizes()
running = True

while running:
    if music_loaded and not music_started:
        pygame.mixer.music.play(-1)
        music_started = True
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                toggle_fullscreen()
            if event.key == pygame.K_ESCAPE:
                if game_state == SETTINGS_MENU:
                    game_state = MENU
                elif game_state == PLAYING:
                    game_state = MENU
                    selected = None
                    drag_start_cell = None
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            
            if game_state == MENU:
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
                fs_btn, vol_btn, back_btn = draw_settings_menu()
                if fs_btn.collidepoint(pos):
                    toggle_fullscreen()
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
                save_btn = pygame.Rect(10, HEIGHT - 40, 120, 30)
                if save_btn.collidepoint(pos):
                    save_game(grid, score)
                    running = False
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
                    else:
                        if selected is not None:
                            r1, c1 = selected
                            if current_cell:
                                r2, c2 = current_cell
                                if abs(r1-r2) + abs(c1-c2) == 1:
                                    if swap_cells(r1, c1, r2, c2):
                                        animations.append(SwapAnimation(r1, c1, r2, c2))
                                    else:
                                        add_error_animation_pair(r1, c1, r2, c2)
                                else:
                                    add_error_animation_pair(r1, c1, r2, c2)
                            selected = None
                    drag_start_cell = None
                else:
                    pos = pygame.mouse.get_pos()
                    cell = get_cell(pos)
                    if cell:
                        if selected is None:
                            selected = cell
                        else:
                            r1, c1 = selected
                            r2, c2 = cell
                            if abs(r1-r2) + abs(c1-c2) == 1:
                                if swap_cells(r1, c1, r2, c2):
                                    animations.append(SwapAnimation(r1, c1, r2, c2))
                                    selected = None
                                else:
                                    add_error_animation_pair(r1, c1, r2, c2)
                                    selected = None
                            else:
                                add_error_animation_pair(r1, c1, r2, c2)
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
        
        save_btn = pygame.Rect(10, HEIGHT - 40, 120, 30)
        pygame.draw.rect(screen, BLUE, save_btn, border_radius=8)
        save_text = small_font.render("Сохранить", True, WHITE)
        screen.blit(save_text, (15, HEIGHT - 35))
        
        hint_text = small_font.render("F11 — полный экран", True, (100,100,100))
        screen.blit(hint_text, (WIDTH - hint_text.get_width() - 10, HEIGHT - 30))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()