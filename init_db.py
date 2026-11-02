import database as db

if __name__ == '__main__':
    print("🚀 Запуск инициализации базы данных...")
    db.init_db()
    db.add_default_tasks()
    print("✅ Инициализация завершена!")