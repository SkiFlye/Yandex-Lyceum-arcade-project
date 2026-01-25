import sqlite3


class GameDatabase:
    def __init__(self, db_name="data/game_save.db"):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_save (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            level INTEGER DEFAULT 1,
            experience INTEGER DEFAULT 0,
            experience_to_next_level INTEGER DEFAULT 100,
            max_hp INTEGER DEFAULT 100,
            current_hp INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(player_name))''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL)''')
        conn.commit()
        conn.close()

    def save_player(self, player_name, level, experience, experience_to_next_level, max_hp, current_hp):
        """Сохранение или обновление игрока по имени"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        # Проверяем, существует ли уже сохранение для этого игрока
        cursor.execute('SELECT id FROM player_save WHERE player_name = ?', (player_name,))
        existing = cursor.fetchone()
        if existing:
            # Обновляем существующее сохранение
            cursor.execute('''
            UPDATE player_save 
            SET level = ?, experience = ?, experience_to_next_level = ?, 
                max_hp = ?, current_hp = ?, last_played = CURRENT_TIMESTAMP
            WHERE player_name = ?
            ''', (level, experience, experience_to_next_level, max_hp, current_hp, player_name))
        else:
            # Создаем новое сохранение для этого игрока
            cursor.execute('''
            INSERT INTO player_save (player_name, level, experience, experience_to_next_level, max_hp, current_hp)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (player_name, level, experience, experience_to_next_level, max_hp, current_hp))
        conn.commit()
        conn.close()

    def load_player(self, player_name):
        """Загрузка игрока по имени"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT player_name, level, experience, experience_to_next_level, max_hp, current_hp 
        FROM player_save 
        WHERE player_name = ?
        LIMIT 1''', (player_name,))
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

    def delete_player(self, player_name):
        """Удаление сохранения игрока"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM player_save WHERE player_name = ?', (player_name,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0  # Возвращает True если удалено

    def get_all_players(self):
        """Получение списка всех сохраненных игроков"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT player_name, level, last_played 
        FROM player_save 
        ORDER BY last_played DESC''')
        players = cursor.fetchall()
        conn.close()
        return [{'name': p[0], 'level': p[1], 'last_played': p[2]} for p in players]