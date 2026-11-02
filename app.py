from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import database as db


app = Flask(__name__)
app.secret_key = 'supersecretkey123456789'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.role = user_data['role']

    @staticmethod
    def get(user_id):
        conn = db.get_db_connection()
        user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        if user_data:
            return User(user_data)
        return None


@login_manager.user_loader
def load_user(user_id):
    return User.get(int(user_id))


# ОСНОВНЫЕ

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    return redirect(url_for('login'))


@app.route('/about')
def about():
    return render_template('about.html',
                           user=current_user if current_user.is_authenticated else None)


# АУТЕНТИФИКАЦИЯ

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            return render_template('register.html', error='Заполните все поля!')
        if len(username) < 3:
            return render_template('register.html', error='Имя минимум 3 символа')
        if len(password) < 4:
            return render_template('register.html', error='Пароль минимум 4 символа')
        if db.create_user(username, password):
            return redirect(url_for('login'))
        return render_template('register.html', error='Пользователь уже существует!')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_data = db.verify_user(username, password)
        if user_data:
            login_user(User(user_data))
            return redirect(url_for('profile'))
        return render_template('login.html', error='Неверное имя или пароль!')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ПРОФИЛЬ

@app.route('/profile')
@login_required
def profile():
    progress = db.get_user_progress(current_user.id)
    stats = db.get_user_stats(current_user.id)
    return render_template('profile.html',
        progress=progress, user=current_user,
        total=stats['total'], completed=stats['completed'],
        in_progress=stats['in_progress'], not_started=stats['not_started'],
        total_attempts=stats['total_attempts'],
        completion_percent=stats['completion_percent'],
        total_points=stats['total_points'], max_points=stats['max_points'])


@app.route('/profile-info', methods=['GET', 'POST'])
@login_required
def profile_info():
    if request.method == 'POST':
        bio = request.form.get('bio', '').strip()
        db.update_user_bio(current_user.id, bio)
        return redirect(url_for('profile_info'))

    stats = db.get_user_stats(current_user.id)
    user_data = db.get_user_by_id(current_user.id)
    rank = db.get_user_rank(current_user.id)
    return render_template('profile_info.html',
                           user=current_user,
                           user_data=user_data,
                           total_points=stats['total_points'],
                           completed_tasks=stats['completed'],
                           friends_count=db.get_friends_count(current_user.id),
                           user_rank=rank)


@app.route('/user/<int:user_id>')
@login_required
def view_user_profile(user_id):
    user_data = db.get_user_by_id(user_id)
    if not user_data:
        return redirect(url_for('friends'))

    stats = db.get_user_stats(user_id)
    rank = db.get_user_rank(user_id)

    return render_template('view_profile.html',
                           user=current_user,
                           profile_user=user_data,
                           total_points=stats['total_points'],
                           completed_tasks=stats['completed'],
                           friends_count=db.get_friends_count(user_id),
                           user_rank=rank)


# ДРУЗЬЯ

@app.route('/friends', methods=['GET', 'POST'])
@login_required
def friends():
    if request.method == 'POST':
        friend_id = request.form.get('friend_id')
        if friend_id:
            db.add_friend(current_user.id, int(friend_id))
        return redirect(url_for('friends'))

    friends_list = db.get_friends(current_user.id)
    return render_template('friends.html', user=current_user, friends=friends_list)


@app.route('/search-users')
@login_required
def search_users():
    query = request.args.get('q', '').strip()
    users = []
    if query:
        conn = db.get_db_connection()
        users = conn.execute(
            'SELECT id, username, avatar FROM users WHERE username LIKE ? AND id != ? LIMIT 20',
            (f'%{query}%', current_user.id)
        ).fetchall()
        conn.close()
    return render_template('search_users.html',
                           user=current_user, query=query,
                           users=users, results=users)


# ЛИЧНЫЕ СООБЩЕНИЯ

@app.route('/messages')
@login_required
def messages():
    chats = db.get_chats(current_user.id)
    return render_template('messages.html', user=current_user, chats=chats)


@app.route('/chat/<int:user_id>', methods=['GET', 'POST'])
@login_required
def chat_with_user(user_id):
    other_user = db.get_user_by_id(user_id)
    if not other_user:
        return redirect(url_for('messages'))

    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if content:
            db.send_private_message(current_user.id, user_id, content)
        return redirect(url_for('chat_with_user', user_id=user_id))

    messages = db.get_messages_between(current_user.id, user_id)
    return render_template('chat.html',
                           user=current_user,
                           other_user=other_user,
                           messages=messages)


@app.route('/send-message', methods=['POST'])
@login_required
def send_message_route():
    receiver_id = request.form.get('receiver_id')
    content = request.form.get('content', '').strip()
    if receiver_id and content:
        db.send_private_message(current_user.id, int(receiver_id), content)
        return redirect(url_for('chat_with_user', user_id=int(receiver_id)))
    return redirect(url_for('messages'))


# ОБСУЖДЕНИЯ

@app.route('/discussions', methods=['GET', 'POST'])
@login_required
def discussions():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if title:
            discussion_id = db.create_discussion(title, current_user.id)
            return redirect(url_for('discussion_chat', discussion_id=discussion_id))
        return redirect(url_for('discussions'))

    discussions_list = db.get_all_discussions()
    return render_template('discussions.html',
                           user=current_user,
                           discussions=discussions_list)


@app.route('/discussion/<int:discussion_id>', methods=['GET', 'POST'])
@login_required
def discussion_chat(discussion_id):
    discussion = db.get_discussion(discussion_id)
    if not discussion:
        return redirect(url_for('discussions'))

    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if content:
            db.send_discussion_message(discussion_id, current_user.id, content)
        return redirect(url_for('discussion_chat', discussion_id=discussion_id))

    messages = db.get_discussion_messages(discussion_id)
    members = db.get_discussion_members(discussion_id)
    all_users = db.get_all_users()

    return render_template('discussion_chat.html',
                           user=current_user,
                           discussion=discussion,
                           messages=messages,
                           members=members,
                           all_users=all_users)


@app.route('/discussion/<int:discussion_id>/send', methods=['POST'])
@login_required
def send_discussion_message_route(discussion_id):
    content = request.form.get('content', '').strip()
    if content:
        db.send_discussion_message(discussion_id, current_user.id, content)
    return redirect(url_for('discussion_chat', discussion_id=discussion_id))


@app.route('/discussion/<int:discussion_id>/add-member', methods=['POST'])
@login_required
def add_discussion_member_route(discussion_id):
    user_id = request.form.get('user_id')
    if user_id:
        db.add_discussion_member(discussion_id, int(user_id))
    return redirect(url_for('discussion_chat', discussion_id=discussion_id))


@app.route('/discussion/<int:discussion_id>/theme', methods=['POST'])
@login_required
def change_discussion_theme_route(discussion_id):
    theme = request.form.get('theme', 'classic')
    db.update_discussion_theme(discussion_id, theme)
    return redirect(url_for('discussion_chat', discussion_id=discussion_id))


@app.route('/discussion/<int:discussion_id>/search-users')
@login_required
def search_discussion_users(discussion_id):
    query = request.args.get('q', '').strip()
    users = []
    if query:
        conn = db.get_db_connection()
        users = conn.execute(
            'SELECT id, username, avatar FROM users WHERE username LIKE ? LIMIT 20',
            (f'%{query}%',)
        ).fetchall()
        conn.close()
    return render_template('search_discussion_users.html',
                           user=current_user,
                           discussion_id=discussion_id,
                           query=query,
                           users=users)


# РЕЙТИНГ

@app.route('/ranking')
@login_required
def ranking():
    ranking_data = db.get_ranking()
    return render_template('ranking.html',
                           user=current_user,
                           users=ranking_data,
                           ranking=ranking_data)


# ПОМОЩЬ / ТЕОРИЯ / ЗАДАНИЯ
@app.route('/help')
def help_page():
    return render_template('help.html',
                           user=current_user if current_user.is_authenticated else None)


@app.route('/theory/<difficulty>')
@login_required
def theory(difficulty):
    if difficulty not in ['easy', 'medium', 'hard']:
        return redirect(url_for('profile'))
    return render_template('theory.html', user=current_user, difficulty=difficulty)


@app.route('/task/<int:task_id>')
@login_required
def task(task_id):
    task_data = db.get_task_by_id(task_id)
    if not task_data:
        return redirect(url_for('profile'))
    solutions = db.get_user_task_solutions(current_user.id, task_id)
    last_code = solutions[0]['code'] if solutions else ''
    has_failed = any(s['status'] != 'success' for s in solutions) if solutions else False
    return render_template('task.html',
        task=task_data, last_code=last_code,
        has_attempts=len(solutions) > 0,
        has_failed_attempts=has_failed,
        attempts_count=len(solutions))

# API
@app.route('/api/run', methods=['POST'])
@login_required
def run_code():
    data = request.get_json()
    code = data.get('code', '')
    task_id = data.get('task_id')
    task = db.get_task_by_id(task_id)
    if not task:
        return jsonify({'success': False, 'error': 'Задание не найдено'})
    if not code.strip():
        return jsonify({'success': False, 'error': 'Код пуст.'})
    html_template = task['html_template'] if task['html_template'] else \
        '<!DOCTYPE html>\n<html>\n<head><meta charset="UTF-8"><title>Результат</title></head>\n<body>{code}</body>\n</html>'
    if '<html' in code.lower() and '<body' in code.lower():
        full_html = code
    else:
        full_html = html_template.format(code=code)
    return jsonify({'success': True, 'html': full_html})


@app.route('/api/submit', methods=['POST'])
@login_required
def submit_solution():
    data = request.get_json()
    code = data.get('code', '')
    task_id = data.get('task_id')
    task = db.get_task_by_id(task_id)
    if not task:
        return jsonify({'success': False, 'error': 'Задание не найдено'})
    if not code.strip():
        return jsonify({'success': False, 'error': 'Код пуст.'})
    tests_config = db.get_tests_config(task_id)
    results = db.check_html_tests(code, tests_config) if tests_config else []
    all_passed = all(r['passed'] for r in results) if results else True
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    status = 'success' if all_passed else 'failed'
    error_message = None
    if not all_passed:
        failed = [r['name'] for r in results if not r['passed']]
        error_message = f'Не пройдено: {", ".join(failed[:3])}'
    db.save_solution(current_user.id, task_id, code, status, error_message)
    message = (f'✅ Все тесты пройдены ({passed_count}/{total_count})'
               if all_passed else f'⚠️ Пройдено {passed_count} из {total_count}')
    return jsonify({
        'success': True, 'status': status, 'message': message,
        'passed_count': passed_count, 'total_count': total_count,
        'all_passed': all_passed, 'results': results
    })


@app.route('/api/get-solution/<int:task_id>')
@login_required
def get_solution(task_id):
    solutions = db.get_user_task_solutions(current_user.id, task_id)
    if not solutions:
        return jsonify({'success': False, 'error': 'Сначала попробуйте сами!'})
    solution = db.get_solution_for_task(task_id)
    if solution:
        return jsonify({'success': True, 'code': solution['code'], 'steps': solution['steps']})
    return jsonify({'success': False, 'error': 'Решение не найдено'})

# ЗАПУСК

with app.app_context():
    db.init_db()
    db.add_default_tasks()


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Платформа запущена")
    print("📍 http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000)