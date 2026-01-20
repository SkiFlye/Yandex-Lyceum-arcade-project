import arcade
from src.game.main_window import MainWindow


# Константы
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
ACTUAL_CARD_WIDTH = int(1024 * 0.15)
ACTUAL_CARD_HEIGHT = int(1024 * 0.2)
CARD_MARGIN = 40
HAND_Y = 260
ENEMY_CENTER_X = SCREEN_WIDTH // 2
ENEMY_CENTER_Y = SCREEN_HEIGHT - 230
DECK_X = 1000
DECK_Y = 570
PLAYER_SCALE = 0.01
PLAYER_SPEED = 100
ENEMY_DETECTION_RADIUS = 100
ENEMY_RADIUS = 30
TILE_SCALING = 1.0
CAMERA_LERP = 0.15
# Состояния игры
STATE_WORLD = "world"
STATE_BATTLE = "battle"
STATE_BATTLE_WIN = "battle_win"
STATE_BATTLE_LOSE = "battle_lose"
# Константы характеристик для уровней
BASE_HEALTH_PER_LEVEL = 10
BASE_DAMAGE_PER_LEVEL = 0.2
BASE_BLOCK_PER_LEVEL = 0.15
# Враги
ENEMY_NAMES = ["Гоблин"]
# База данных
DB_NAME = "data/game_save.db"


def main():
    window = arcade.Window(
        width=1200,
        height=800,
        title="Карточный Рогалик"
    )
    main_view = MainWindow()
    main_view.setup()
    window.show_view(main_view)
    arcade.run()


if __name__ == "__main__":
    main()