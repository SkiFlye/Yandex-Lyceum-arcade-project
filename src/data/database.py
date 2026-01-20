import sqlite3


class GameDatabase:
    def __init__(self, db_name="data/game_save.db"):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        # Создаем таблицу
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_save (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL DEFAULT 'Player',
            level INTEGER DEFAULT 1,
            experience INTEGER DEFAULT 0,
            experience_to_next_level INTEGER DEFAULT 100,
            max_hp INTEGER DEFAULT 100,
            current_hp INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()

    def save_player(self, level, experience, experience_to_next_level, max_hp, current_hp):
        """Сохранение или обновление игрока"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM player_save')
        existing = cursor.fetchone()
        if existing:
            cursor.execute('''
            UPDATE player_save 
            SET level = ?, experience = ?, experience_to_next_level = ?, 
                max_hp = ?, current_hp = ?, last_played = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (level, experience, experience_to_next_level, max_hp, current_hp, existing[0]))
        else:
            cursor.execute('''
            INSERT INTO player_save (name, level, experience, experience_to_next_level, max_hp, current_hp)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', ('Player', level, experience, experience_to_next_level, max_hp, current_hp))
        conn.commit()
        conn.close()

    def load_player(self):
        """Загрузка игрока"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT name, level, experience, experience_to_next_level, max_hp, current_hp 
        FROM player_save 
        LIMIT 1''')
        result = cursor.fetchone()
        conn.close()
        if result:
            return {
                'name': result[0],
                'level': result[1],
                'experience': result[2],
                'experience_to_next_level': result[3],
                'max_hp': result[4],
                'current_hp': result[5]}
        return None