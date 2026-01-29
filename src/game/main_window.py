import arcade
import arcade.gui
import sqlite3
from arcade.gui import UIManager, UIInputText, UITextureButton
from src.game.game_world_window import GameWorldWindow


class MainWindow(arcade.View):
    """Главное окно с меню авторизации и регистрации"""
    def __init__(self):
        super().__init__()
        # UI Manager
        self.ui_manager = UIManager()
        # Состояния
        self.current_screen = "auth"
        self.error_message = ""
        self.info_message = ""
        # Данные для авторизации
        self.username = ""
        self.password = ""
        # Элементы UI
        self.name_input = None
        self.password_input = None
        self.buttons = []
        # UI элементы для хранения
        self.ui_elements = []
        # Фон меню
        self.background = None
        # Размеры окна
        self.SCREEN_WIDTH = 1200
        self.SCREEN_HEIGHT = 800
        # Музыка
        self.music_player = None
        self.music_volume = 0.3

    def setup(self):
        """Настройка окна меню"""
        self.background = arcade.load_texture("images/main_background.jpg")
        self.setup_auth_screen()
        self.play_music()

    def play_music(self):
        """Запускает фоновую музыку главного меню"""
        self.stop_music()
        sound = arcade.load_sound("assets/main_window_melody.mp3")
        if sound:
            self.music_player = arcade.play_sound(sound, volume=self.music_volume, loop=True)

    def stop_music(self):
        """Останавливает музыку"""
        if self.music_player:
            arcade.stop_sound(self.music_player)
            self.music_player = None

    def on_show_view(self):
        """Вызывается при показе этого View (когда переходим на это окно)"""
        # Включаем UI менеджер при показе окна
        self.ui_manager.enable()
        self.play_music()

    def on_hide_view(self):
        """Вызывается при скрытии этого View (когда уходим с этого окна)"""
        # ВАЖНО: Отключаем UI менеджер при скрытии окна
        self.ui_manager.disable()
        self.stop_music()

    def clear_ui(self):
        """Очищает все UI элементы"""
        # Очищаем менеджер UI
        self.ui_manager.clear()
        # Очищаем ссылки
        self.name_input = None
        self.password_input = None
        self.buttons.clear()
        self.ui_elements.clear()

    def setup_auth_screen(self):
        """Настройка экрана авторизации"""
        self.clear_ui()
        self.current_screen = "auth"
        self.error_message = ""
        self.info_message = ""
        # Заголовок
        title = arcade.Text(
            "Fate Deck",
            self.window.width // 2,
            self.window.height - 100,
            arcade.color.GOLD,
            40,
            anchor_x="center",
            anchor_y="center")
        self.ui_elements.append(title)
        # Подзаголовок
        subtitle = arcade.Text(
            "Авторизация",
            self.window.width // 2,
            self.window.height - 150,
            arcade.color.WHITE,
            24,
            anchor_x="center",
            anchor_y="center")
        self.ui_elements.append(subtitle)
        # Поле для имени
        name_label = arcade.Text(
            "Имя героя:",
            self.window.width // 2 - 220,
            self.window.height - 250,
            arcade.color.WHITE,
            20,
            anchor_x="center",
            anchor_y="center")
        self.ui_elements.append(name_label)
        self.name_input = UIInputText(
            x=self.window.width // 2 - 150,
            y=self.window.height - 270,
            width=400,
            height=40,
            text="",
            font_size=18)
        self.ui_manager.add(self.name_input)
        # Поле для пароля
        password_label = arcade.Text(
            "Пароль:",
            self.window.width // 2 - 200,
            self.window.height - 320,
            arcade.color.WHITE,
            20,
            anchor_x="center",
            anchor_y="center")
        self.ui_elements.append(password_label)

        self.password_input = UIInputText(
            x=self.window.width // 2 - 150,
            y=self.window.height - 340,
            width=400,
            height=40,
            text="",
            font_size=18,
            password_char="*")
        self.ui_manager.add(self.password_input)
        # Кнопка "Войти"
        login_button = UITextureButton(
            x=self.window.width // 2 - 220,
            y=self.window.height - 445,
            width=200,
            height=50,
            text="Войти",
            font_size=20)
        login_button.on_click = self.on_login_click
        self.ui_manager.add(login_button)
        self.buttons.append(login_button)
        # Кнопка "Создать героя"
        create_button = UITextureButton(
            x=self.window.width // 2 + 20,
            y=self.window.height - 445,
            width=200,
            height=50,
            text="Создать героя",
            font_size=20)
        create_button.on_click = self.on_create_click
        self.ui_manager.add(create_button)
        self.buttons.append(create_button)
        # Кнопка "Выход"
        exit_button = UITextureButton(
            x=self.window.width // 2 - 100,
            y=self.window.height - 525,
            width=200,
            height=50,
            text="Выход",
            font_size=20)
        exit_button.on_click = self.on_exit_click
        self.ui_manager.add(exit_button)
        self.buttons.append(exit_button)

    def setup_menu_screen(self):
        """Настройка главного меню после авторизации"""
        self.clear_ui()
        self.current_screen = "menu"
        self.error_message = ""
        self.info_message = f"Добро пожаловать, {self.username}!"
        # Заголовок
        title = arcade.Text(
            "ГЛАВНОЕ МЕНЮ",
            self.window.width // 2,
            self.window.height - 100,
            arcade.color.GOLD,
            40,
            anchor_x="center",
            anchor_y="center")
        self.ui_elements.append(title)
        # Приветствие
        welcome_text = arcade.Text(
            self.info_message,
            self.window.width // 2,
            self.window.height - 180,
            arcade.color.GREEN,
            24,
            anchor_x="center",
            anchor_y="center")
        self.ui_elements.append(welcome_text)
        # Кнопка "Начать игру"
        start_button = UITextureButton(
            x=self.window.width // 2 - 150,
            y=self.window.height - 310,
            width=300,
            height=60,
            text="Начать игру",
            font_size=24)
        start_button.on_click = self.on_start_game_click
        self.ui_manager.add(start_button)
        self.buttons.append(start_button)
        # Кнопка "Выйти из аккаунта"
        logout_button = UITextureButton(
            x=self.window.width // 2 - 150,
            y=self.window.height - 410,
            width=300,
            height=60,
            text="Выйти из аккаунта",
            font_size=24)
        logout_button.on_click = self.on_logout_click
        self.ui_manager.add(logout_button)
        self.buttons.append(logout_button)

    def check_hero_exists(self, username, password):
        """Проверяет существование героя и правильность пароля. Использует базу данных SQLite."""
        conn = sqlite3.connect("data/game_save.db")
        cursor = conn.cursor()
        # Проверяем существование героя и пароль
        cursor.execute("SELECT name, password FROM passwords WHERE name = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        if result:
            stored_name, stored_password = result
            if stored_password == password:
                return "success"
            else:
                return "wrong_password"
        else:
            return "not_found"

    def create_hero(self, username, password):
        """Создает нового героя."""
        conn = sqlite3.connect("data/game_save.db")
        cursor = conn.cursor()
        # Создаем таблицу если её нет
        cursor.execute('''CREATE TABLE IF NOT EXISTS passwords (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL)''')
        # Пытаемся добавить нового игрока
        try:
            cursor.execute(
                "INSERT INTO passwords (name, password) VALUES (?, ?)",
                (username, password))
            conn.commit()
            conn.close()
            return True, "Герой успешно создан!"
        except sqlite3.IntegrityError:
            conn.close()
            return False, "Герой с таким именем уже существует!"

    def on_login_click(self, event):
        """Обработчик кнопки 'Войти'"""
        self.username = self.name_input.text.strip()
        self.password = self.password_input.text.strip()
        if not self.username or not self.password:
            self.error_message = "Заполните все поля!"
            return
        result = self.check_hero_exists(self.username, self.password)
        if result == "success":
            self.setup_menu_screen()
        elif result == "wrong_password":
            self.error_message = "Введен неверный пароль!"
        elif result == "not_found":
            self.error_message = "Такого героя нет!"

    def on_create_click(self, event):
        """Обработчик кнопки 'Создать героя'"""
        self.username = self.name_input.text.strip()
        self.password = self.password_input.text.strip()
        if not self.username or not self.password:
            self.error_message = "Заполните все поля!"
            return
        # Проверяем длину имени
        if len(self.username) < 3:
            self.error_message = "Имя должно содержать минимум 3 символа!"
            return

        if len(self.username) > 20:
            self.error_message = "Имя должно содержать максимум 20 символов!"
            return
        # Проверяем длину пароля
        if len(self.password) < 4:
            self.error_message = "Пароль должен содержать минимум 4 символа!"
            return
        # Создаем героя
        success, message = self.create_hero(self.username, self.password)
        if success:
            self.info_message = message
            self.setup_menu_screen()
        else:
            self.error_message = message

    def on_start_game_click(self, event):
        """Обработчик кнопки 'Начать игру'"""
        # Останавливаем музыку главного меню
        self.stop_music()
        self.ui_manager.disable()
        # Создаем окно игры с именем авторизованного пользователя
        game_view = GameWorldWindow(
            screen_width=1200,
            screen_height=800,
            player_name=self.username,
            player_scale=0.01,
            player_speed=100,
            enemy_radius=30,
            tile_scaling=1.0,
            camera_lerp=0.15,
            base_health_per_level=10,
            base_damage_per_level=0.2,
            base_block_per_level=0.15,
            db_name="data/game_save.db")
        game_view.setup()
        self.window.show_view(game_view)

    def on_logout_click(self, event):
        """Обработчик кнопки 'Выйти из аккаунта'"""
        self.username = ""
        self.password = ""
        self.setup_auth_screen()

    def on_exit_click(self, event):
        """Обработчик кнопки 'Выход'"""
        self.window.close()

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(
            self.background,
            arcade.rect.XYWH(
                self.window.width // 2,
                self.window.height // 2,
                self.window.width,
                self.window.height))
        # Рисуем полупрозрачную панель
        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.window.width // 2, self.window.height - 370, 600, 300),
            (0, 0, 0, 200))
        # Рисуем текстовые элементы
        for element in self.ui_elements:
            if isinstance(element, arcade.Text):
                element.draw()
        if self.error_message:
            error_text = arcade.Text(
                self.error_message,
                self.window.width // 2,
                self.window.height - 180,
                arcade.color.RED,
                18,
                anchor_x="center",
                anchor_y="center",
                bold=True)
            error_text.draw()
        self.ui_manager.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.close()