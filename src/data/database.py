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
            has_shield_6 INTEGER DEFAULT 0,  -- 0 = False, 1 = True
            UNIQUE(player_name))''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL)''')
        conn.commit()
        conn.close()

    def save_player(self, player_name, level, experience, experience_to_next_level, max_hp, current_hp,
                    has_shield_6=False):
        """Сохранение или обновление игрока по имени"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        # Проверяем, существует ли уже сохранение для этого игрока
        cursor.execute('SELECT id FROM player_save WHERE player_name = ?', (player_name,))
        existing = cursor.fetchone()
        # Преобразуем bool в int для SQLite
        has_shield_6_int = 1 if has_shield_6 else 0
        if existing:
            # Обновляем существующее сохранение
            cursor.execute('''
            UPDATE player_save 
            SET level = ?, experience = ?, experience_to_next_level = ?, 
                max_hp = ?, current_hp = ?, has_shield_6 = ?, last_played = CURRENT_TIMESTAMP
            WHERE player_name = ?
            ''', (level, experience, experience_to_next_level, max_hp, current_hp, has_shield_6_int,
                  player_name))
        else:
            # Создаем новое сохранение для этого игрока
            cursor.execute('''
            INSERT INTO player_save (player_name, level, experience, experience_to_next_level, max_hp, current_hp, 
            has_shield_6)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (player_name, level, experience, experience_to_next_level, max_hp, current_hp,
                  has_shield_6_int))
        conn.commit()
        conn.close()

    def load_player(self, player_name):
        """Загрузка игрока по имени"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT player_name, level, experience, experience_to_next_level, max_hp, current_hp, has_shield_6
        FROM player_save 
        WHERE player_name = ?
        LIMIT 1''', (player_name,))
        result = cursor.fetchone()
        conn.close()
        if result:
            # Преобразуем значение has_shield_6 из int в bool
            has_shield_6_value = result[6]
            has_shield_6_bool = bool(has_shield_6_value) if has_shield_6_value is not None else False
            return {
                'name': result[0],
                'level': result[1],
                'experience': result[2],
                'experience_to_next_level': result[3],
                'max_hp': result[4],
                'current_hp': result[5],
                'has_shield_6': has_shield_6_bool
            }
        return None

    def get_has_shield_6(self, player_name):
        """Проверяет, есть ли у игрока карта shield_6"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT has_shield_6 FROM player_save WHERE player_name = ?
        ''', (player_name,))
        result = cursor.fetchone()
        conn.close()
        if result:
            value = result[0]
            return bool(value) if value is not None else False
        return False

    def set_has_shield_6(self, player_name, has_shield_6):
        """Устанавливает флаг наличия карты shield_6"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        # Преобразуем bool в int
        has_shield_6_int = 1 if has_shield_6 else 0
        cursor.execute('''
        UPDATE player_save SET has_shield_6 = ? WHERE player_name = ?
        ''', (has_shield_6_int, player_name))
        conn.commit()
        conn.close()

    def create_new_player(self, player_name, has_shield_6=False):
        """Создает нового игрока с начальными значениями"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        # Преобразуем bool в int
        has_shield_6_int = 1 if has_shield_6 else 0
        cursor.execute('''
        INSERT INTO player_save (player_name, level, experience, experience_to_next_level, max_hp, current_hp, has_shield_6)
        VALUES (?, 1, 0, 100, 100, 100, ?)
        ''', (player_name, has_shield_6_int))
        conn.commit()
        conn.close()

    def player_exists(self, player_name):
        """Проверяет, существует ли игрок в базе данных"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM player_save WHERE player_name = ?', (player_name,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def delete_player(self, player_name):
        """Удаляет игрока из базы данных"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM player_save WHERE player_name = ?', (player_name,))
        conn.commit()
        conn.close()

    def get_all_players(self):
        """Получает список всех игроков"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT player_name, level, has_shield_6 FROM player_save ORDER BY player_name')
        results = cursor.fetchall()
        conn.close()
        players = []
        for result in results:
            players.append({
                'name': result[0],
                'level': result[1],
                'has_shield_6': bool(result[2]) if result[2] is not None else False
            })
        return players

    # Методы для работы с паролями
    def save_password(self, name, password):
        """Сохраняет пароль"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO passwords (name, password)
        VALUES (?, ?)
        ''', (name, password))
        conn.commit()
        conn.close()

    def get_password(self, name):
        """Получает пароль по имени"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM passwords WHERE name = ?', (name,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def password_exists(self, name):
        """Проверяет, существует ли пароль для указанного имени"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM passwords WHERE name = ?', (name,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
