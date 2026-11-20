from flask import Flask, render_template, jsonify
import sqlite3
import random
import os

app = Flask(__name__)

# Определяем путь к БД относительно текущего файла скрипта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "khl_dashboard.db")

def get_db_connection():
    """Вспомогательная функция для подключения к БД"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    print(f"\n--- ИНИЦИАЛИЗАЦИЯ БД ---")
    print(f"Путь к БД: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Создаем таблицы
    cursor.execute('''CREATE TABLE IF NOT EXISTS players 
                      (id INTEGER PRIMARY KEY, name TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS shots 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, player_id INTEGER, match_id INTEGER, x INTEGER, y INTEGER, shot_type INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS matches 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)''')
    
    # Проверяем, есть ли данные
    cursor.execute("SELECT COUNT(*) FROM players")
    count = cursor.fetchone()[0]
    print(f"Количество игроков в БД: {count}")
    
    if count == 0:
        print("База пуста. Заполняем тестовыми данными...")
        
        # Игроки
        players = [
            (1, 'Никита Гусев'), 
            (2, 'Сергей Мозякин'), 
            (3, 'Александр Радулов')
        ]
        cursor.executemany("INSERT INTO players VALUES (?, ?)", players)
        
        # Добавляем матчи
        matches = [(1, 'Матч 1 (ЦСКА)'), (2, 'Матч 2 (СКА)'), (3, 'Матч 3 (Динамо)'), 
                   (4, 'Матч 4 (Ак Барс)'), (5, 'Матч 5 (Авангард)')]
        cursor.executemany("INSERT INTO matches VALUES (?, ?)", matches)
        
        print("Генерируем броски...")
        for player_id in [1, 2, 3]:
            for match_id in range(1, 6):
                shots_count = random.randint(3, 10)
                for _ in range(shots_count):
                    # Координаты КХЛ (примерные зоны атаки)
                    x = random.randint(200, 800) 
                    y = random.randint(50, 450)
                    # 1 - гол, 2 - сейв/промах
                    shot_type = 1 if random.random() > 0.8 else 2 
                    
                    cursor.execute(
                        "INSERT INTO shots (player_id, match_id, x, y, shot_type) VALUES (?, ?, ?, ?, ?)", 
                        (player_id, match_id, x, y, shot_type)
                    )
        conn.commit()
        print("Тестовые данные добавлены.")
    else:
        print(f"В базе уже есть {count} игроков.")
        
    conn.close()

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Ошибка шаблона: {e}. Убедитесь, что index.html лежит в папке templates/", 500

@app.route('/api/players')
def api_players():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    players = conn.execute('SELECT * FROM players').fetchall()
    conn.close()
    return jsonify([dict(p) for p in players])

@app.route('/api/shots/<int:player_id>')
def api_shots(player_id):
    conn = get_db_connection()
    shots = conn.execute('SELECT x, y, shot_type FROM shots WHERE player_id = ?', (player_id,)).fetchall()
    conn.close()
    return jsonify([dict(s) for s in shots])

# НОВЫЙ МАРШРУТ: История бросков по матчам для линейного графика
@app.route('/api/player/<int:player_id>/history')
def api_player_history(player_id):
    conn = get_db_connection()
    query = """
        SELECT m.name as match_name, COUNT(s.id) as shot_count
        FROM matches m
        LEFT JOIN shots s ON m.id = s.match_id AND s.player_id = ?
        GROUP BY m.id
        ORDER BY m.id
    """
    history = conn.execute(query, (player_id,)).fetchall()
    conn.close()
    
    # Возвращаем два списка: названия матчей и количество бросков
    labels = [row['match_name'] for row in history]
    data = [row['shot_count'] for row in history]
    
    return jsonify({"labels": labels, "data": data})

if __name__ == '__main__':
    # Если хотите сбрасывать БД при каждом запуске, раскомментируйте строку ниже:
    # if os.path.exists(DB_PATH): os.remove(DB_PATH)
    
    init_db() 
    print("Сервер запущен! Откройте http://127.0.0.1:5000/ в браузере.")
    app.run(debug=True)