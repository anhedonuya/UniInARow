import pygame
import random
import os

pygame.init()

# Размеры окна
WIDTH, HEIGHT = 600, 700
GRID_SIZE = 8
CELL_SIZE = 60
MARGIN = 10
TOP_OFFSET = 70

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Uni in a Row")
clock = pygame.time.Clock()

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (40, 40, 40)
DARK_GRAY = (30, 30, 30)

# Загрузка спрайтов
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
            # Заглушка, если спрайт не найден
            surf = pygame.Surface((CELL_SIZE - 10, CELL_SIZE - 10))
            surf.fill(pygame.Color(color))
            sprites[color] = surf
    return sprites

sprites = load_sprites()
colors_list = list(sprites.keys())

# Игровое поле
grid = [[random.choice(colors_list) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
selected = None
score = 0
font = pygame.font.Font(None, 36)

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

def find_matches():
    matches = set()
    # Горизонтальные
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE - 2):
            if grid[row][col] == grid[row][col+1] == grid[row][col+2]:
                matches.add((row, col))
                matches.add((row, col+1))
                matches.add((row, col+2))
    # Вертикальные
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
    for col in range(GRID_SIZE):
        for row in range(GRID_SIZE-1, -1, -1):
            if grid[row][col] is None:
                for r in range(row-1, -1, -1):
                    if grid[r][col] is not None:
                        grid[row][col] = grid[r][col]
                        grid[r][col] = None
                        break
    for col in range(GRID_SIZE):
        for row in range(GRID_SIZE):
            if grid[row][col] is None:
                grid[row][col] = random.choice(colors_list)

def get_cell(pos):
    x, y = pos
    if x < MARGIN or y < TOP_OFFSET:
        return None
    col = (x - MARGIN) // CELL_SIZE
    row = (y - TOP_OFFSET) // CELL_SIZE
    if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
        return (row, col)
    return None

def swap_cells(r1, c1, r2, c2):
    grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]
    if find_matches():
        return True
    grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]
    return False

# Основной цикл
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
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
                            score += 1
                        selected = None
                    else:
                        selected = cell

    matches = find_matches()
    if matches:
        remove_matches(matches)
        drop_down()
        score += 1

    screen.fill(BLACK)
    draw_grid()
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))
    pygame.display.flip()
    clock.tick(30)

pygame.quit()