# levels.py - система уровней для Uni in a Row

# Типы целей:
# "score" - собрать N очков
# "color" - собрать N фишек определённого цвета

LEVELS = {
    1: {"target": 10, "moves": 15, "type": "score", "color": None},
    2: {"target": 15, "moves": 14, "type": "score", "color": None},
    3: {"target": 5, "moves": 12, "type": "color", "color": "blue"},
    4: {"target": 20, "moves": 12, "type": "score", "color": None},
    5: {"target": 5, "moves": 11, "type": "color", "color": "green"},
    6: {"target": 30, "moves": 10, "type": "score", "color": None},
    7: {"target": 5, "moves": 9, "type": "color", "color": "red"},
    8: {"target": 40, "moves": 8, "type": "score", "color": None},
    9: {"target": 5, "moves": 7, "type": "color", "color": "yellow"},
    10: {"target": 50, "moves": 6, "type": "score", "color": None}
}

TOTAL_LEVELS = len(LEVELS)

def get_level_data(level_num):
    """Возвращает данные уровня (цель, ходы, тип, цвет)"""
    return LEVELS.get(level_num, LEVELS[1])

def get_target(level_num):
    """Возвращает цель уровня (очки или количество фишек)"""
    return get_level_data(level_num)["target"]

def get_moves(level_num):
    """Возвращает количество ходов для уровня"""
    return get_level_data(level_num)["moves"]

def get_level_type(level_num):
    """Возвращает тип цели: 'score' или 'color'"""
    return get_level_data(level_num)["type"]

def get_target_color(level_num):
    """Возвращает цвет фишек для цели типа 'color'"""
    return get_level_data(level_num)["color"]

def is_last_level(level_num):
    """Проверяет, является ли уровень последним"""
    return level_num >= TOTAL_LEVELS

def next_level(level_num):
    """Возвращает номер следующего уровня"""
    return level_num + 1 if level_num < TOTAL_LEVELS else TOTAL_LEVELS

def get_level_description(level_num):
    """Возвращает текстовое описание цели для отображения"""
    data = get_level_data(level_num)
    if data["type"] == "score":
        return f"Собери {data['target']} очков"
    else:
        color_names = {
            "blue": "синих",
            "green": "зелёных",
            "red": "красных",
            "yellow": "жёлтых",
            "purple": "фиолетовых"
        }
        color_name = color_names.get(data["color"], data["color"])
        return f"Собери {data['target']} {color_name} фишек"