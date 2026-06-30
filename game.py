import pygame
import random
import os
import json
import math

pygame.init()
pygame.mixer.init()

# Размеры окна
WIDTH, HEIGHT = 600, 700
GRID_SIZE = 6
CELL_SIZE = 70
MARGIN = (WIDTH - (GRID_SIZE * CELL_SIZE)) // 2
TOP_OFFSET = 80

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Uni in a Row")
clock = pygame.time.Clock()

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (40, 40, 40)
DARK_GRAY = (30, 30, 30)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLUE = (0, 100, 255)

# --- ЗАГРУЗКА ФОНА ---
background = None
bg_path = "sprites/background.png"
if os.path.exists(bg_path):
    try:
        bg = pygame.image.load(bg_path).convert()
        background = pygame.transform.scale(bg, (WIDTH, HEIGHT))
    except:
        background = None

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
game_state = MENU

# --- АНИМАЦИИ ---
animations = []

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
    """Рисует оформленный заголовок с тенью и градиентом"""
    font_big = pygame.font.Font(None, size)
    
    # Создаём поверхность для текста
    text_surf = font_big.render(text, True, WHITE)
    text_rect = text_surf.get_rect(center=(x, y))
    
    # Рисуем тень (смещение вправо-вниз)
    shadow_surf = font_big.render(text, True, (30, 30, 30))
    shadow_rect = text_rect.copy()
    shadow_rect.x += 4
    shadow_rect.y += 4
    screen.blit(shadow_surf, shadow_rect)
    
    # Рисуем второй слой тени (для объёма)
    shadow2_surf = font_big.render(text, True, (60, 60, 60))
    shadow2_rect = text_rect.copy()
    shadow2_rect.x += 2
    shadow2_rect.y += 2
    screen.blit(shadow2_surf, shadow2_rect)
    
    # Создаём градиентный эффект: рисуем текст несколько раз разными цветами
    colors = [
        (255, 200, 50),   # золотой
        (255, 180, 30),   # тёмно-золотой
        (200, 150, 50),   # бронзовый
    ]
    
    # Основной текст с небольшими смещениями для градиента
    for i, col in enumerate(colors):
        surf = font_big.render(text, True, col)
        rect = text_rect.copy()
        rect.x += i * 1
        rect.y += i * 1
        screen.blit(surf, rect)
    
    # Яркий верхний слой (блик)
    highlight_surf = font_big.render(text, True, (255, 240, 200))
    screen.blit(highlight_surf, text_rect)
    
    # Рамка вокруг текста
    border_rect = text_rect.inflate(30, 20)
    pygame.draw.rect(screen, (100, 80, 30), border_rect, 2, border_radius=10)
    
    # Внешняя тонкая рамка
    outer_rect = border_rect.inflate(10, 10)
    pygame.draw.rect(screen, (60, 50, 20), outer_rect, 1, border_radius=12)

def draw_menu():
    screen.fill(BLACK)
    if background:
        screen.blit(background, (0, 0))
    
    # Оформленное название игры
    draw_title("Uni in a Row", WIDTH//2, 120, 72)
    
    btn_width, btn_height = 200, 50
    btn_x = WIDTH//2 - btn_width//2
    
    new_btn = pygame.Rect(btn_x, 250, btn_width, btn_height)
    load_btn = pygame.Rect(btn_x, 330, btn_width, btn_height)
    exit_btn = pygame.Rect(btn_x, 410, btn_width, btn_height)
    
    has_save_flag = has_save()
    
    # Кнопки с закруглёнными углами
    for btn, color in [(new_btn, GREEN), (load_btn, BLUE if has_save_flag else GRAY), (exit_btn, RED)]:
        pygame.draw.rect(screen, color, btn, border_radius=12)
        # Тень для кнопок
        shadow_btn = btn.copy()
        shadow_btn.y += 4
        pygame.draw.rect(screen, (0,0,0), shadow_btn, border_radius=12)
        # Основная кнопка поверх тени
        pygame.draw.rect(screen, color, btn, border_radius=12)
    
    new_text = font.render("Новая игра", True, WHITE)
    load_text = font.render("Загрузить", True, WHITE)
    exit_text = font.render("Выход", True, WHITE)
    
    screen.blit(new_text, (WIDTH//2 - new_text.get_width()//2, 260))
    screen.blit(load_text, (WIDTH//2 - load_text.get_width()//2, 340))
    screen.blit(exit_text, (WIDTH//2 - exit_text.get_width()//2, 420))
    
    if not has_save_flag:
        no_save_text = small_font.render("(нет сохранения)", True, (150,150,150))
        screen.blit(no_save_text, (WIDTH//2 - no_save_text.get_width()//2, 385))
    
    return new_btn, load_btn, exit_btn

def draw_game_over():
    screen.fill(BLACK)
    if background:
        screen.blit(background, (0, 0))
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

# --- УПРАВЛЕНИЕ МУЗЫКОЙ ---
def play_menu_music():
    if music_loaded and not pygame.mixer.music.get_busy():
        pygame.mixer.music.play(-1)

# --- ГЛАВНЫЙ ЦИКЛ ---
running = True
while running:
    if music_loaded and not music_started:
        pygame.mixer.music.play(-1)
        music_started = True
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            
            if game_state == MENU:
                new_btn, load_btn, exit_btn = draw_menu()
                if new_btn.collidepoint(pos):
                    grid = create_grid()
                    score = 0
                    selected = None
                    animations = []
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
                        game_state = PLAYING
                elif exit_btn.collidepoint(pos):
                    running = False
            
            elif game_state == GAME_OVER:
                restart_btn, exit_btn = draw_game_over()
                if restart_btn.collidepoint(pos):
                    grid = create_grid()
                    score = 0
                    selected = None
                    animations = []
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
                            selected = cell

    if game_state == PLAYING:
        if not animations:
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

    if game_state == MENU:
        draw_menu()
    elif game_state == GAME_OVER:
        draw_game_over()
    else:
        screen.fill(BLACK)
        if background:
            screen.blit(background, (0, 0))
        
        draw_grid()
        
        for anim in animations:
            anim.draw(screen)
        
        score_text = font.render(f"Счёт: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        save_btn = pygame.Rect(10, HEIGHT - 40, 120, 30)
        pygame.draw.rect(screen, BLUE, save_btn, border_radius=8)
        save_text = small_font.render("Сохранить", True, WHITE)
        screen.blit(save_text, (15, HEIGHT - 35))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()