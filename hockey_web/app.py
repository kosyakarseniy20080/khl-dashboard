from flask import Flask, render_template, jsonify
import sqlite3
import random
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "khl_dashboard.db")

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
    
    cursor.execute("SELECT COUNT(*) FROM players")
    count = cursor.fetchone()[0]
    print(f"Количество игроков в БД: {count}")
    
    if count == 0:
        print("Добавляем тестовых игроков и матчи...")
        players = [(1, 'Никита Гусев'), (2, 'Сергей Мозякин'), (3, 'Александр Радулов')]
        cursor.executemany("INSERT INTO players VALUES (?, ?)", players)
        
        # Добавляем матчи
        matches = [(1, 'Матч 1 (ЦСКА)'), (2, 'Матч 2 (СКА)'), (3, 'Матч 3 (Динамо)'), 
                   (4, 'Матч 4 (Ак Барс)'), (5, 'Матч 5 (Авангард)')]
        cursor.executemany("INSERT INTO matches VALUES (?, ?)", matches)
        
        print("Генерируем броски...")
        for player_id in [1, 2, 3]:
            for match_id in [1, 2, 3, 4, 5]:
                # Для каждого матча генерируем от 2 до 8 бросков
                shots_in_match = random.randint(2, 8)
                for _ in range(shots_in_match): 
                    x = random.randint(200, 800) 
                    y = random.randint(100, 400)
                    shot_type = 1 if random.random() > 0.7 else 2 
                    cursor.execute("INSERT INTO shots (player_id, match_id, x, y, shot_type) VALUES (?, ?, ?, ?, ?)", 
                                   (player_id, match_id, x, y, shot_type))
    
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM players")
    print(f"Игроков после инициализации: {cursor.fetchone()[0]}")
    print(f"--- ИНИЦИАЛИЗАЦИЯ ЗАВЕРШЕНА ---\n")
    conn.close()

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/players')
def api_players():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    players = conn.execute('SELECT * FROM players').fetchall()
    conn.close()
    return jsonify([dict(p) for p in players])

@app.route('/api/shots/<int:player_id>')
def api_shots(player_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    shots = conn.execute('SELECT x, y, shot_type FROM shots WHERE player_id = ?', (player_id,)).fetchall()
    conn.close()
    return jsonify([dict(s) for s in shots])

# НОВЫЙ МАРШРУТ: История бросков по матчам для линейного графика
@app.route('/api/player/<int:player_id>/history')
def api_player_history(player_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Группируем броски по матчам и считаем их количество
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
    if os.path.exists(DB_PATH):
        print(f"Удаляем старую БД: {DB_PATH}")
        os.remove(DB_PATH)
        
    init_db() 
    print("Сервер запущен! Откройте http://127.0.0.1:5000/ в браузере.")
    app.run(debug=True)