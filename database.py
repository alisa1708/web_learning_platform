import sqlite3
import bcrypt
import re

DB_PATH = 'instance/platform.db'


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            bio TEXT DEFAULT '',
            avatar TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            short_description TEXT,
            starter_code TEXT,
            expected_output TEXT,
            html_template TEXT,
            difficulty TEXT DEFAULT 'easy',
            points INTEGER DEFAULT 10,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS solutions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            status TEXT NOT NULL,
            error_message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (task_id) REFERENCES tasks (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS discussions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            creator_id INTEGER NOT NULL,
            theme TEXT DEFAULT 'classic',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (creator_id) REFERENCES users (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS discussion_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discussion_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (discussion_id) REFERENCES discussions (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(discussion_id, user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS discussion_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discussion_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (discussion_id) REFERENCES discussions (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS friends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            friend_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (friend_id) REFERENCES users (id),
            UNIQUE(user_id, friend_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS private_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (receiver_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")


def add_default_tasks():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    if count > 0:
        conn.close()
        return

    tasks = [
        # ЛЁГКИЕ ЗАДАНИЯ (easy)
        {
            'title': 'Привет, мир!',
            'description': 'Создайте HTML-страницу с заголовком <h1> "Привет, мир!" и параграфом <p> "Это моя первая веб-страница".',
            'short_description': 'Создание структуры веб-страницы',
            'difficulty': 'easy', 'points': 10, 'starter_code': '',
            'expected_output': 'Привет, мир!',
            'html_template': '<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="UTF-8">\n    <title>Результат</title>\n</head>\n<body>\n    {code}\n</body>\n</html>'
        },
        {
            'title': 'Таблица умножения',
            'description': 'Создайте HTML-таблицу 3x3 с числами таблицы умножения. Используйте <table>, <tr>, <td>.',
            'short_description': 'Работа с таблицами HTML',
            'difficulty': 'easy', 'points': 15, 'starter_code': '',
            'expected_output': 'Таблица умножения',
            'html_template': '<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="UTF-8">\n    <title>Результат</title>\n</head>\n<body>\n    {code}\n</body>\n</html>'
        },
        {
            'title': 'Список дел',
            'description': 'Создайте список дел с заголовком <h2> и <ul> с тремя пунктами: "Купить продукты", "Сделать домашнее задание", "Прочитать книгу".',
            'short_description': 'Списки и структура документа',
            'difficulty': 'easy', 'points': 10, 'starter_code': '',
            'expected_output': 'Список дел',
            'html_template': '<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="UTF-8">\n    <title>Результат</title>\n</head>\n<body>\n    {code}\n</body>\n</html>'
        },
        {
            'title': 'Стилизация страницы',
            'description': 'Добавьте <style>: h1 — синий, p — зелёный, body — светлый фон.',
            'short_description': 'Основы CSS стилизации',
            'difficulty': 'easy', 'points': 15, 'starter_code': '',
            'expected_output': 'Мой стильный заголовок',
            'html_template': '<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="UTF-8">\n    <title>Результат</title>\n</head>\n<body>\n    {code}\n</body>\n</html>'
        },

        # СРЕДНИЕ ЗАДАНИЯ (medium)
        {
            'title': 'Гибкий макет (Flexbox)',
            'description': 'Создайте .container с display: flex и тремя .box разных цветов. Каждый блок 100×100 пикселей, распределите их через justify-content.',
            'short_description': 'Работа с Flexbox',
            'difficulty': 'medium', 'points': 20, 'starter_code': '',
            'expected_output': 'Гибкий макет',
            'html_template': '<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="UTF-8">\n    <title>Результат</title>\n</head>\n<body>\n    {code}\n</body>\n</html>'
        },
        {
            'title': 'Форма обратной связи',
            'description': 'Создайте форму с полями: имя (input type="text"), email (input type="email"), сообщение (textarea) и кнопкой "Отправить". Используйте тег <form>, <label>, <input>, <textarea>, <button>.',
            'short_description': 'Работа с формами HTML',
            'difficulty': 'medium', 'points': 25, 'starter_code': '',
            'expected_output': 'Форма обратной связи',
            'html_template': '<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="UTF-8">\n    <title>Результат</title>\n</head>\n<body>\n    {code}\n</body>\n</html>'
        },
        {
            'title': 'Карточка товара',
            'description': 'Создайте карточку товара: изображение (используйте https://via.placeholder.com/200), название товара <h3>, описание <p> и кнопку "Купить". Оформите карточку через CSS: белый фон, скруглённые углы (border-radius), тень (box-shadow), отступы (padding).',
            'short_description': 'Стилизация карточки',
            'difficulty': 'medium', 'points': 25, 'starter_code': '',
            'expected_output': 'Карточка товара',
            'html_template': '<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="UTF-8">\n    <title>Результат</title>\n</head>\n<body>\n    {code}\n</body>\n</html>'
        },
        {
            'title': 'Навигационное меню',
            'description': 'Создайте горизонтальное меню навигации: используйте <nav> и <ul> с 4 пунктами (Главная, О нас, Услуги, Контакты). Через CSS уберите маркеры (list-style: none), сделайте пункты в одну строку (display: flex), добавьте отступы и hover-эффект.',
            'short_description': 'Меню навигации',
            'difficulty': 'medium', 'points': 25, 'starter_code': '',
            'expected_output': 'Меню навигации',
            'html_template': '<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="UTF-8">\n    <title>Результат</title>\n</head>\n<body>\n    {code}\n</body>\n</html>'
        },

        # СЛОЖНЫЕ ЗАДАНИЯ (hard)
        {
            'title': 'CSS Grid: сетка галереи',
            'description': 'Создайте галерею из 6 блоков через CSS Grid. Используйте .gallery с display: grid, grid-template-columns: repeat(3, 1fr), gap: 10px. Каждый блок — .item с фиксированной высотой (100px) и разными цветами.',
            'short_description': 'Работа с CSS Grid',
            'difficulty': 'hard', 'points': 35, 'starter_code': '',
            'expected_output': 'CSS Grid галерея',
            'html_template': '<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="UTF-8">\n    <title>Результат</title>\n</head>\n<body>\n    {code}\n</body>\n</html>'
        },
        {
            'title': 'Адаптивная страница',
            'description': 'Создайте страницу с медиа-запросом. Изначально .container имеет display: flex и 3 блока .box в ряд. При ширине экрана меньше 600px (@media (max-width: 600px)) — блоки должны идти в колонку (flex-direction: column).',
            'short_description': 'Адаптивная вёрстка',
            'difficulty': 'hard', 'points': 40, 'starter_code': '',
            'expected_output': 'Адаптивная страница',
            'html_template': '<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="UTF-8">\n    <title>Результат</title>\n</head>\n<body>\n    {code}\n</body>\n</html>'
        },
        {
            'title': 'CSS-анимация',
            'description': 'Создайте анимацию через @keyframes. Круг .circle (width: 100px, height: 100px, border-radius: 50%, background: #6366F1) должен плавно менять цвет и масштаб (transform: scale). Анимация длится 2 секунды и повторяется бесконечно (animation: name 2s infinite).',
            'short_description': 'CSS-анимации',
            'difficulty': 'hard', 'points': 35, 'starter_code': '',
            'expected_output': 'CSS-анимация',
            'html_template': '<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="UTF-8">\n    <title>Результат</title>\n</head>\n<body>\n    {code}\n</body>\n</html>'
        },
        {
            'title': 'Форма с валидацией',
            'description': 'Создайте форму регистрации с полями: имя, email, пароль. Используйте атрибуты required, minlength="6" для пароля, type="email" для email. Добавьте <label> к каждому полю и кнопку "Зарегистрироваться". Оформите форму через CSS.',
            'short_description': 'Форма с валидацией',
            'difficulty': 'hard', 'points': 40, 'starter_code': '',
            'expected_output': 'Форма с валидацией',
            'html_template': '<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="UTF-8">\n    <title>Результат</title>\n</head>\n<body>\n    {code}\n</body>\n</html>'
        }
    ]

    for task in tasks:
        cursor.execute('''
            INSERT INTO tasks (title, description, short_description, starter_code,
                              expected_output, html_template, difficulty, points)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (task['title'], task['description'], task['short_description'],
              task['starter_code'], task['expected_output'], task['html_template'],
              task['difficulty'], task['points']))

    conn.commit()
    conn.close()
    print(f"✅ Добавлено {len(tasks)} заданий")


# ПОЛЬЗОВАТЕЛИ

def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user


def create_user(username, password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                     (username, hashed.decode('utf-8')))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def verify_user(username, password):
    user = get_user_by_username(username)
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return user
    return None


def update_user_bio(user_id, bio):
    conn = get_db_connection()
    conn.execute('UPDATE users SET bio = ? WHERE id = ?', (bio, user_id))
    conn.commit()
    conn.close()


# ЗАДАНИЯ И РЕШЕНИЯ

def get_all_tasks():
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks ORDER BY id').fetchall()
    conn.close()
    return tasks


def get_task_by_id(task_id):
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    conn.close()
    return task


def save_solution(user_id, task_id, code, status, error_message=None):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO solutions (user_id, task_id, code, status, error_message)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, task_id, code, status, error_message))
    conn.commit()
    conn.close()


def get_user_task_solutions(user_id, task_id):
    conn = get_db_connection()
    solutions = conn.execute('''
        SELECT * FROM solutions
        WHERE user_id = ? AND task_id = ?
        ORDER BY timestamp DESC
    ''', (user_id, task_id)).fetchall()
    conn.close()
    return solutions


def get_task_progress(user_id, task_id):
    solutions = get_user_task_solutions(user_id, task_id)
    if not solutions:
        return {'status': 'Не начато', 'attempts': 0, 'last_date': None,
                'best_status': None, 'last_code': None}
    attempts = len(solutions)
    last = solutions[0]
    best = 'success' if any(s['status'] == 'success' for s in solutions) else 'failed'
    return {
        'status': 'Выполнено' if best == 'success' else 'Провалено',
        'attempts': attempts, 'last_date': last['timestamp'],
        'best_status': best, 'last_code': last['code']
    }


def get_user_progress(user_id):
    tasks = get_all_tasks()
    progress = []
    for task in tasks:
        prog = get_task_progress(user_id, task['id'])
        progress.append({'task': task, 'progress': prog})
    return progress


def get_user_stats(user_id):
    progress = get_user_progress(user_id)
    total = len(progress)
    completed = sum(1 for p in progress if p['progress']['status'] == 'Выполнено')
    in_progress = sum(1 for p in progress if p['progress']['status'] == 'Провалено')
    not_started = sum(1 for p in progress if p['progress']['status'] == 'Не начато')
    total_attempts = sum(p['progress']['attempts'] for p in progress)
    total_points = sum(p['task']['points'] for p in progress if p['progress']['status'] == 'Выполнено')
    max_points = sum(p['task']['points'] for p in progress)
    return {
        'total': total, 'completed': completed, 'in_progress': in_progress,
        'not_started': not_started, 'total_attempts': total_attempts,
        'total_points': total_points, 'max_points': max_points,
        'completion_percent': (completed / total * 100) if total > 0 else 0,
        'points_percent': (total_points / max_points * 100) if max_points > 0 else 0
    }


# ДРУЗЬЯ

def get_friends(user_id):
    conn = get_db_connection()
    friends = conn.execute('''
        SELECT u.id, u.username, u.avatar
        FROM friends f
        JOIN users u ON f.friend_id = u.id
        WHERE f.user_id = ?
    ''', (user_id,)).fetchall()
    conn.close()
    return friends


def add_friend(user_id, friend_id):
    if user_id == friend_id:
        return False
    conn = get_db_connection()
    try:
        conn.execute('INSERT OR IGNORE INTO friends (user_id, friend_id) VALUES (?, ?)',
                     (user_id, friend_id))
        conn.execute('INSERT OR IGNORE INTO friends (user_id, friend_id) VALUES (?, ?)',
                     (friend_id, user_id))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False


def get_friends_count(user_id):
    conn = get_db_connection()
    count = conn.execute('SELECT COUNT(*) FROM friends WHERE user_id = ?', (user_id,)).fetchone()[0]
    conn.close()
    return count


# ЛИЧНЫЕ СООБЩЕНИЯ

def get_chats(user_id):
    conn = get_db_connection()
    chats_raw = conn.execute('''
        SELECT
            CASE WHEN sender_id = ? THEN receiver_id ELSE sender_id END as other_user_id,
            MAX(created_at) as last_time
        FROM private_messages
        WHERE sender_id = ? OR receiver_id = ?
        GROUP BY other_user_id
        ORDER BY last_time DESC
    ''', (user_id, user_id, user_id)).fetchall()

    chats = []
    for chat in chats_raw:
        other_id = chat['other_user_id']
        other_user = conn.execute('SELECT id, username, avatar FROM users WHERE id = ?',
                                   (other_id,)).fetchone()
        if not other_user:
            continue

        last_msg = conn.execute('''
            SELECT content, created_at FROM private_messages
            WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
            ORDER BY created_at DESC LIMIT 1
        ''', (user_id, other_id, other_id, user_id)).fetchone()

        unread = conn.execute('''
            SELECT COUNT(*) FROM private_messages
            WHERE sender_id = ? AND receiver_id = ? AND is_read = 0
        ''', (other_id, user_id)).fetchone()[0]

        chats.append({
            'other_user_id': other_id,
            'other_username': other_user['username'],
            'other_avatar': other_user['avatar'],
            'last_message': last_msg['content'] if last_msg else '',
            'last_message_time': last_msg['created_at'] if last_msg else '',
            'unread_count': unread
        })

    conn.close()
    return chats


def get_messages_between(user_id, other_id):
    conn = get_db_connection()
    messages = conn.execute('''
        SELECT * FROM private_messages
        WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
        ORDER BY created_at ASC
    ''', (user_id, other_id, other_id, user_id)).fetchall()

    conn.execute('''
        UPDATE private_messages SET is_read = 1
        WHERE sender_id = ? AND receiver_id = ?
    ''', (other_id, user_id))
    conn.commit()
    conn.close()
    return messages


def send_private_message(sender_id, receiver_id, content):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO private_messages (sender_id, receiver_id, content)
        VALUES (?, ?, ?)
    ''', (sender_id, receiver_id, content))
    conn.commit()
    conn.close()


# ОБСУЖДЕНИЯ

def get_all_discussions():
    conn = get_db_connection()
    discussions = conn.execute('''
        SELECT d.*, u.username as creator_name,
               (SELECT COUNT(*) FROM discussion_messages WHERE discussion_id = d.id) as messages_count
        FROM discussions d
        JOIN users u ON d.creator_id = u.id
        ORDER BY d.created_at DESC
    ''').fetchall()
    conn.close()
    return discussions


def get_discussion(discussion_id):
    conn = get_db_connection()
    discussion = conn.execute('''
        SELECT d.*, u.username as creator_name
        FROM discussions d
        JOIN users u ON d.creator_id = u.id
        WHERE d.id = ?
    ''', (discussion_id,)).fetchone()
    conn.close()
    return discussion


def create_discussion(title, creator_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO discussions (title, creator_id) VALUES (?, ?)',
                   (title, creator_id))
    discussion_id = cursor.lastrowid
    cursor.execute('INSERT INTO discussion_members (discussion_id, user_id) VALUES (?, ?)',
                   (discussion_id, creator_id))
    conn.commit()
    conn.close()
    return discussion_id


def get_discussion_messages(discussion_id):
    conn = get_db_connection()
    messages = conn.execute('''
        SELECT dm.*, u.username, u.avatar
        FROM discussion_messages dm
        JOIN users u ON dm.user_id = u.id
        WHERE dm.discussion_id = ?
        ORDER BY dm.created_at ASC
    ''', (discussion_id,)).fetchall()
    conn.close()
    return messages


def send_discussion_message(discussion_id, user_id, content):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO discussion_messages (discussion_id, user_id, content)
        VALUES (?, ?, ?)
    ''', (discussion_id, user_id, content))
    conn.commit()
    conn.close()


def get_discussion_members(discussion_id):
    conn = get_db_connection()
    members = conn.execute('''
        SELECT u.id, u.username, u.avatar
        FROM discussion_members dm
        JOIN users u ON dm.user_id = u.id
        WHERE dm.discussion_id = ?
    ''', (discussion_id,)).fetchall()
    conn.close()
    return members


def add_discussion_member(discussion_id, user_id):
    conn = get_db_connection()
    try:
        conn.execute('INSERT OR IGNORE INTO discussion_members (discussion_id, user_id) VALUES (?, ?)',
                     (discussion_id, user_id))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False


def update_discussion_theme(discussion_id, theme):
    conn = get_db_connection()
    conn.execute('UPDATE discussions SET theme = ? WHERE id = ?', (theme, discussion_id))
    conn.commit()
    conn.close()


def get_all_users():
    conn = get_db_connection()
    users = conn.execute('SELECT id, username, avatar FROM users').fetchall()
    conn.close()
    return users


# РЕЙТИНГ

def get_ranking():
    conn = get_db_connection()
    users = conn.execute('SELECT id, username, avatar FROM users').fetchall()
    conn.close()

    ranking_data = []
    for u in users:
        stats = get_user_stats(u['id'])
        ranking_data.append({
            'id': u['id'],
            'username': u['username'],
            'avatar': u['avatar'],
            'total_points': stats['total_points'],
            'completed': stats['completed'],
            'total': stats['total']
        })
    ranking_data.sort(key=lambda x: x['total_points'], reverse=True)
    return ranking_data


def get_user_rank(user_id):
    ranking = get_ranking()
    for i, r in enumerate(ranking):
        if r['id'] == user_id:
            return i + 1
    return '—'


# ПРИМЕРЫ РЕШЕНИЙ

def get_solution_for_task(task_id):
    solutions = {
        1: {
            'code': '<!DOCTYPE html>\n<html>\n<head>\n    <title>Моя страница</title>\n</head>\n<body>\n    <h1>Привет, мир!</h1>\n    <p>Это моя первая веб-страница</p>\n</body>\n</html>',
            'steps': 'Шаг 1. Создайте структуру HTML\nШаг 2. Добавьте <h1>Привет, мир!</h1>\nШаг 3. Добавьте <p>Это моя первая веб-страница</p>'
        },
        2: {
            'code': '<!DOCTYPE html>\n<html>\n<head>\n    <title>Таблица</title>\n    <style>\n        table { border-collapse: collapse; }\n        td { border: 1px solid black; padding: 10px; }\n    </style>\n</head>\n<body>\n    <table>\n        <tr><td>1</td><td>2</td><td>3</td></tr>\n        <tr><td>2</td><td>4</td><td>6</td></tr>\n        <tr><td>3</td><td>6</td><td>9</td></tr>\n    </table>\n</body>\n</html>',
            'steps': 'Шаг 1. Создайте <table>\nШаг 2. Добавьте 3 строки <tr>\nШаг 3. В каждой строке по 3 <td>'
        },
        3: {
            'code': '<!DOCTYPE html>\n<html>\n<head><title>Дела</title></head>\n<body>\n    <h2>Список дел</h2>\n    <ul>\n        <li>Купить продукты</li>\n        <li>Сделать домашнее задание</li>\n        <li>Прочитать книгу</li>\n    </ul>\n</body>\n</html>',
            'steps': 'Шаг 1. Добавьте <h2>\nШаг 2. Создайте <ul>\nШаг 3. Добавьте 3 <li>'
        },
        4: {
            'code': '<!DOCTYPE html>\n<html>\n<head>\n    <title>Стили</title>\n    <style>\n        body { background: #f0f0f0; padding: 20px; }\n        h1 { color: blue; }\n        p { color: green; }\n    </style>\n</head>\n<body>\n    <h1>Мой стильный заголовок</h1>\n    <p>Этот параграф зелёного цвета</p>\n</body>\n</html>',
            'steps': 'Шаг 1. Добавьте <style>\nШаг 2. h1 { color: blue; }\nШаг 3. p { color: green; }'
        },
        5: {
            'code': '<!DOCTYPE html>\n<html>\n<head>\n    <title>Flexbox</title>\n    <style>\n        .container { display: flex; justify-content: space-around; padding: 20px; }\n        .box { width: 100px; height: 100px; border-radius: 8px; }\n        .box:nth-child(1) { background: #6C63FF; }\n        .box:nth-child(2) { background: #FF6584; }\n        .box:nth-child(3) { background: #00C9A7; }\n    </style>\n</head>\n<body>\n    <div class="container">\n        <div class="box"></div>\n        <div class="box"></div>\n        <div class="box"></div>\n    </div>\n</body>\n</html>',
            'steps': 'Шаг 1. Создайте .container\nШаг 2. display: flex, justify-content\nШаг 3. Создайте 3 .box с размерами и цветами'
        },
        6: {
            'code': '<!DOCTYPE html>\n<html>\n<head>\n    <title>Форма</title>\n    <style>\n        form { max-width: 400px; padding: 20px; }\n        label { display: block; margin: 10px 0 5px; font-weight: 600; }\n        input, textarea { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; }\n        button { margin-top: 12px; padding: 10px 20px; background: #6366F1; color: white; border: none; border-radius: 6px; cursor: pointer; }\n    </style>\n</head>\n<body>\n    <h1>Свяжитесь с нами</h1>\n    <form>\n        <label>Имя:</label>\n        <input type="text" placeholder="Введите имя">\n        <label>Email:</label>\n        <input type="email" placeholder="Ваш email">\n        <label>Сообщение:</label>\n        <textarea rows="4" placeholder="Ваше сообщение"></textarea>\n        <button type="submit">Отправить</button>\n    </form>\n</body>\n</html>',
            'steps': 'Шаг 1. Создайте <form>\nШаг 2. Добавьте поля: name, email, сообщение\nШаг 3. Добавьте кнопку submit\nШаг 4. Стилизуйте через CSS'
        },
        7: {
            'code': '<!DOCTYPE html>\n<html>\n<head>\n    <title>Карточка</title>\n    <style>\n        .card { width: 250px; background: white; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); padding: 20px; text-align: center; }\n        .card img { width: 100%; border-radius: 12px; }\n        .card h3 { margin: 16px 0 8px; }\n        .card p { color: #6B7280; font-size: 14px; }\n        .card button { background: #6366F1; color: white; border: none; padding: 10px 24px; border-radius: 8px; cursor: pointer; }\n    </style>\n</head>\n<body>\n    <div class="card">\n        <img src="https://via.placeholder.com/200" alt="Товар">\n        <h3>Название товара</h3>\n        <p>Краткое описание товара</p>\n        <button>Купить</button>\n    </div>\n</body>\n</html>',
            'steps': 'Шаг 1. Создайте .card\nШаг 2. Добавьте <img>, <h3>, <p>, <button>\nШаг 3. Стилизуйте: border-radius, box-shadow, padding'
        },
        8: {
            'code': '<!DOCTYPE html>\n<html>\n<head>\n    <title>Меню</title>\n    <style>\n        nav { background: #6366F1; padding: 12px; }\n        nav ul { list-style: none; display: flex; gap: 24px; margin: 0; padding: 0; }\n        nav a { color: white; text-decoration: none; font-weight: 600; padding: 8px 12px; border-radius: 6px; }\n        nav a:hover { background: rgba(255,255,255,0.2); }\n    </style>\n</head>\n<body>\n    <nav>\n        <ul>\n            <li><a href="#">Главная</a></li>\n            <li><a href="#">О нас</a></li>\n            <li><a href="#">Услуги</a></li>\n            <li><a href="#">Контакты</a></li>\n        </ul>\n    </nav>\n</body>\n</html>',
            'steps': 'Шаг 1. Создайте <nav> с <ul>\nШаг 2. Добавьте 4 пункта <li>\nШаг 3. list-style: none, display: flex\nШаг 4. Hover-эффект'
        },
        9: {
            'code': '<!DOCTYPE html>\n<html>\n<head>\n    <title>Галерея</title>\n    <style>\n        .gallery { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; padding: 20px; }\n        .item { height: 100px; border-radius: 8px; }\n        .item:nth-child(1) { background: #6C63FF; }\n        .item:nth-child(2) { background: #FF6584; }\n        .item:nth-child(3) { background: #00C9A7; }\n        .item:nth-child(4) { background: #F59E0B; }\n        .item:nth-child(5) { background: #3B82F6; }\n        .item:nth-child(6) { background: #8B5CF6; }\n    </style>\n</head>\n<body>\n    <div class="gallery">\n        <div class="item"></div>\n        <div class="item"></div>\n        <div class="item"></div>\n        <div class="item"></div>\n        <div class="item"></div>\n        <div class="item"></div>\n    </div>\n</body>\n</html>',
            'steps': 'Шаг 1. Создайте .gallery\nШаг 2. display: grid, grid-template-columns: repeat(3, 1fr)\nШаг 3. gap: 10px\nШаг 4. Добавьте 6 .item с цветами'
        },
        10: {
            'code': '<!DOCTYPE html>\n<html>\n<head>\n    <title>Адаптив</title>\n    <style>\n        .container { display: flex; gap: 16px; padding: 20px; }\n        .box { flex: 1; height: 100px; background: #6366F1; border-radius: 8px; }\n        @media (max-width: 600px) {\n            .container { flex-direction: column; }\n        }\n    </style>\n</head>\n<body>\n    <div class="container">\n        <div class="box"></div>\n        <div class="box"></div>\n        <div class="box"></div>\n    </div>\n</body>\n</html>',
            'steps': 'Шаг 1. Создайте .container с display: flex\nШаг 2. Добавьте 3 .box\nШаг 3. @media (max-width: 600px)\nШаг 4. flex-direction: column'
        },
        11: {
            'code': '<!DOCTYPE html>\n<html>\n<head>\n    <title>Анимация</title>\n    <style>\n        .circle {\n            width: 100px; height: 100px;\n            border-radius: 50%;\n            background: #6366F1;\n            margin: 50px auto;\n            animation: pulse 2s infinite;\n        }\n        @keyframes pulse {\n            0% { transform: scale(1); background: #6366F1; }\n            50% { transform: scale(1.3); background: #EC4899; }\n            100% { transform: scale(1); background: #6366F1; }\n        }\n    </style>\n</head>\n<body>\n    <div class="circle"></div>\n</body>\n</html>',
            'steps': 'Шаг 1. Создайте .circle (круг через border-radius)\nШаг 2. @keyframes — 3 состояния\nШаг 3. animation: name 2s infinite\nШаг 4. transform: scale и background'
        },
        12: {
            'code': '<!DOCTYPE html>\n<html>\n<head>\n    <title>Регистрация</title>\n    <style>\n        form { max-width: 400px; margin: 30px auto; padding: 24px; background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }\n        label { display: block; margin-bottom: 6px; font-weight: 600; color: #374151; }\n        input { width: 100%; padding: 10px; margin-bottom: 16px; border: 1px solid #D1D5DB; border-radius: 8px; box-sizing: border-box; }\n        input:focus { outline: none; border-color: #6366F1; box-shadow: 0 0 0 3px rgba(99,102,241,0.1); }\n        button { width: 100%; padding: 12px; background: #6366F1; color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; }\n    </style>\n</head>\n<body>\n    <form>\n        <label>Имя:</label>\n        <input type="text" required placeholder="Иван">\n        <label>Email:</label>\n        <input type="email" required placeholder="ivan@mail.ru">\n        <label>Пароль:</label>\n        <input type="password" required minlength="6" placeholder="Минимум 6 символов">\n        <button type="submit">Зарегистрироваться</button>\n    </form>\n</body>\n</html>',
            'steps': 'Шаг 1. Создайте <form>\nШаг 2. Добавьте 3 поля: text, email, password\nШаг 3. required, minlength="6", type="email"\nШаг 4. Стилизуйте через CSS'
        }
    }
    return solutions.get(task_id, None)


# ТЕСТЫ

def get_tests_config(task_id):
    configs = {
        1: [
            {'name': 'Наличие <html>', 'type': 'tag_exists', 'value': 'html'},
            {'name': 'Наличие <body>', 'type': 'tag_exists', 'value': 'body'},
            {'name': 'Наличие <h1>', 'type': 'tag_exists', 'value': 'h1'},
            {'name': 'Текст "Привет, мир!"', 'type': 'text_exists', 'value': 'Привет, мир!'},
            {'name': 'Наличие <p>', 'type': 'tag_exists', 'value': 'p'},
        ],
        2: [
            {'name': 'Наличие <table>', 'type': 'tag_exists', 'value': 'table'},
            {'name': '3+ строк <tr>', 'type': 'tag_count', 'tag': 'tr', 'min': 3},
            {'name': '9+ ячеек <td>', 'type': 'tag_count', 'tag': 'td', 'min': 9},
        ],
        3: [
            {'name': 'Наличие <ul>', 'type': 'tag_exists', 'value': 'ul'},
            {'name': '3+ пунктов <li>', 'type': 'tag_count', 'tag': 'li', 'min': 3},
            {'name': 'Текст "Купить продукты"', 'type': 'text_exists', 'value': 'Купить продукты'},
            {'name': 'Текст "Прочитать книгу"', 'type': 'text_exists', 'value': 'Прочитать книгу'},
        ],
        4: [
            {'name': 'Наличие <style>', 'type': 'tag_exists', 'value': 'style'},
            {'name': 'CSS-правило h1 { color }', 'type': 'css_rule', 'selector': 'h1', 'property': 'color'},
            {'name': 'CSS-правило p { color }', 'type': 'css_rule', 'selector': 'p', 'property': 'color'},
        ],
        5: [
            {'name': 'Класс "container"', 'type': 'class_exists', 'value': 'container'},
            {'name': '3+ классов "box"', 'type': 'class_count', 'value': 'box', 'min': 3},
            {'name': 'display: flex', 'type': 'css_property', 'value': 'display: flex'},
            {'name': 'justify-content', 'type': 'css_property', 'value': 'justify-content'},
        ],
        6: [
            {'name': 'Наличие <form>', 'type': 'tag_exists', 'value': 'form'},
            {'name': 'Наличие <input>', 'type': 'tag_exists', 'value': 'input'},
            {'name': '2+ поля <input>', 'type': 'tag_count', 'tag': 'input', 'min': 2},
            {'name': 'Наличие <textarea>', 'type': 'tag_exists', 'value': 'textarea'},
            {'name': 'Наличие <button>', 'type': 'tag_exists', 'value': 'button'},
        ],
        7: [
            {'name': 'Наличие <img>', 'type': 'tag_exists', 'value': 'img'},
            {'name': 'Наличие <h3>', 'type': 'tag_exists', 'value': 'h3'},
            {'name': 'Наличие <p>', 'type': 'tag_exists', 'value': 'p'},
            {'name': 'CSS border-radius', 'type': 'css_property', 'value': 'border-radius'},
            {'name': 'CSS box-shadow', 'type': 'css_property', 'value': 'box-shadow'},
        ],
        8: [
            {'name': 'Наличие <nav>', 'type': 'tag_exists', 'value': 'nav'},
            {'name': 'Наличие <ul>', 'type': 'tag_exists', 'value': 'ul'},
            {'name': '4+ пунктов <li>', 'type': 'tag_count', 'tag': 'li', 'min': 4},
            {'name': 'CSS list-style', 'type': 'css_property', 'value': 'list-style'},
            {'name': 'CSS display', 'type': 'css_property', 'value': 'display'},
        ],
        9: [
            {'name': 'Наличие <style>', 'type': 'tag_exists', 'value': 'style'},
            {'name': 'CSS display: grid', 'type': 'css_property', 'value': 'display: grid'},
            {'name': 'CSS grid-template-columns', 'type': 'css_property', 'value': 'grid-template-columns'},
            {'name': 'CSS gap', 'type': 'css_property', 'value': 'gap'},
        ],
        10: [
            {'name': 'CSS display: flex', 'type': 'css_property', 'value': 'display: flex'},
            {'name': 'CSS @media', 'type': 'css_property', 'value': '@media'},
            {'name': 'CSS max-width', 'type': 'css_property', 'value': 'max-width'},
            {'name': 'CSS flex-direction', 'type': 'css_property', 'value': 'flex-direction'},
        ],
        11: [
            {'name': 'CSS @keyframes', 'type': 'css_property', 'value': '@keyframes'},
            {'name': 'CSS animation', 'type': 'css_property', 'value': 'animation'},
            {'name': 'CSS border-radius', 'type': 'css_property', 'value': 'border-radius'},
            {'name': 'CSS transform', 'type': 'css_property', 'value': 'transform'},
        ],
        12: [
            {'name': 'Наличие <form>', 'type': 'tag_exists', 'value': 'form'},
            {'name': '3+ поля <input>', 'type': 'tag_count', 'tag': 'input', 'min': 3},
            {'name': 'Атрибут required', 'type': 'text_exists', 'value': 'required'},
            {'name': 'type="email"', 'type': 'text_exists', 'value': 'type="email"'},
            {'name': 'Атрибут minlength', 'type': 'text_exists', 'value': 'minlength'},
        ]
    }
    return configs.get(task_id, [])


def check_html_tests(code, tests_config):
    results = []
    for test in tests_config:
        test_type = test.get('type')
        passed = False
        detail = ''

        try:
            if test_type == 'tag_exists':
                tag = test['value']
                passed = bool(re.search(rf'<{tag}[\s>/]', code, re.IGNORECASE))
                detail = f'Тег <{tag}> {"найден" if passed else "не найден"}'
            elif test_type == 'tag_count':
                tag = test['tag']
                min_count = test.get('min', 1)
                count = len(re.findall(rf'<{tag}[\s>/]', code, re.IGNORECASE))
                passed = count >= min_count
                detail = f'Найдено {count} <{tag}> (минимум {min_count})'
            elif test_type == 'text_exists':
                text = test['value']
                passed = text.lower() in code.lower()
                detail = f'Текст "{text}" {"найден" if passed else "не найден"}'
            elif test_type == 'class_exists':
                class_name = test['value']
                pattern = rf'class\s*=\s*["\'][^"\']*\b{re.escape(class_name)}\b[^"\']*["\']'
                passed = bool(re.search(pattern, code, re.IGNORECASE))
                detail = f'Класс "{class_name}" {"найден" if passed else "не найден"}'
            elif test_type == 'class_count':
                class_name = test['value']
                min_count = test.get('min', 1)
                pattern = rf'class\s*=\s*["\'][^"\']*\b{re.escape(class_name)}\b[^"\']*["\']'
                count = len(re.findall(pattern, code, re.IGNORECASE))
                passed = count >= min_count
                detail = f'Найдено {count} "{class_name}" (минимум {min_count})'
            elif test_type == 'css_rule':
                selector = test.get('selector', '')
                prop = test.get('property', '')
                pattern = rf'{selector}\s*\{{[^}}]*{prop}\s*:'
                passed = bool(re.search(pattern, code, re.IGNORECASE | re.DOTALL))
                detail = f'CSS {selector} {{ {prop} }} {"найдено" if passed else "не найдено"}'
            elif test_type == 'css_property':
                value = test['value']
                normalized_code = re.sub(r'\s+', ' ', code.lower())
                normalized_value = re.sub(r'\s+', ' ', value.lower())
                passed = normalized_value in normalized_code
                detail = f'Свойство "{value}" {"найдено" if passed else "не найдено"}'
        except Exception as e:
            detail = f'Ошибка: {str(e)}'

        results.append({'name': test['name'], 'passed': passed, 'detail': detail})
    return results