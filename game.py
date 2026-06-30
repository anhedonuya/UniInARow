import pygame
import random
import os
import math

pygame.init()

# Размеры окна
WIDTH, HEIGHT = 600, 700
GRID_SIZE = 6  # Изменено с 8 на 6
CELL_SIZE = 70  # Можно увеличить ячейки для лучшего вида

# Автоматический расчёт отступа, чтобы поле было по центру
MARGIN = (WIDTH - (GRID_SIZE * CELL_SIZE)) // 2
TOP_OFFSET = 80  # Отступ сверху, чтобы поле не было прижато к верху

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

# --- ЗАГРУЗКА ФОНА ---
background = None
bg_path = "sprites/background.png"
if os.path.exists(bg_path):
    try:
        bg = pygame.image.load(bg_path).convert()
        background = pygame.transform.scale(bg, (WIDTH, HEIGHT))
    except:
        background = None

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

# --- ИГРОВОЕ ПОЛЕ ---
def create_grid():
    return [[random.choice(colors_list) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

grid = create_grid()
selected = None
score = 0
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 72)

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

def draw_menu():
    screen.fill(BLACK)
    if background:
        screen.blit(background, (0, 0))
    title = big_font.render("Uni in a Row", True, WHITE)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))
    
    start_btn = pygame.Rect(WIDTH//2 - 80, 300, 160, 50)
    exit_btn = pygame.Rect(WIDTH//2 - 80, 400, 160, 50)
    
    pygame.draw.rect(screen, GREEN, start_btn)
    pygame.draw.rect(screen, RED, exit_btn)
    
    start_text = font.render("Старт", True, WHITE)
    exit_text = font.render("Выход", True, WHITE)
    screen.blit(start_text, (WIDTH//2 - start_text.get_width()//2, 310))
    screen.blit(exit_text, (WIDTH//2 - exit_text.get_width()//2, 410))
    
    return start_btn, exit_btn

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
    
    pygame.draw.rect(screen, GREEN, restart_btn)
    pygame.draw.rect(screen, RED, exit_btn)
    
    restart_text = font.render("Старт", True, WHITE)
    exit_text = font.render("Выход", True, WHITE)
    screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, 360))
    screen.blit(exit_text, (WIDTH//2 - exit_text.get_width()//2, 460))
    
    return restart_btn, exit_btn

# --- ГЛАВНЫЙ ЦИКЛ ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            if game_state == MENU:
                start_btn, exit_btn = draw_menu()
                if start_btn.collidepoint(pos):
                    game_state = PLAYING
                    grid = create_grid()
                    score = 0
                    selected = None
                    animations = []
                elif exit_btn.collidepoint(pos):
                    running = False
            elif game_state == GAME_OVER:
                restart_btn, exit_btn = draw_game_over()
                if restart_btn.collidepoint(pos):
                    game_state = PLAYING
                    grid = create_grid()
                    score = 0
                    selected = None
                    animations = []
                elif exit_btn.collidepoint(pos):
                    running = False
            elif game_state == PLAYING:
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

    # --- ИГРОВАЯ ЛОГИКА (только в PLAYING) ---
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

    # --- ОТРИСОВКА ---
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

    pygame.display.flip()
    clock.tick(60)

pygame.quit()