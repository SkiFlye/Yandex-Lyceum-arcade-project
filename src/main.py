import arcade
from roguelike_card_game.src.game import GameWindow


# Константы
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
ACTUAL_CARD_WIDTH = int(1024 * 0.15)
ACTUAL_CARD_HEIGHT = int(1024 * 0.2)
CARD_MARGIN = 40
HAND_Y = 200
ENEMY_CENTER_X = SCREEN_WIDTH // 2
ENEMY_CENTER_Y = SCREEN_HEIGHT - 300
DECK_X = SCREEN_WIDTH - 200
DECK_Y = SCREEN_HEIGHT - 300
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
    window = GameWindow(
        screen_width=SCREEN_WIDTH,
        screen_height=SCREEN_HEIGHT,
        actual_card_width=ACTUAL_CARD_WIDTH,
        actual_card_height=ACTUAL_CARD_HEIGHT,
        card_margin=CARD_MARGIN,
        hand_y=HAND_Y,
        enemy_center_x=ENEMY_CENTER_X,
        enemy_center_y=ENEMY_CENTER_Y,
        deck_x=DECK_X,
        deck_y=DECK_Y,
        player_scale=PLAYER_SCALE,
        player_speed=PLAYER_SPEED,
        enemy_radius=ENEMY_RADIUS,
        tile_scaling=TILE_SCALING,
        camera_lerp=CAMERA_LERP,
        state_world=STATE_WORLD,
        state_battle=STATE_BATTLE,
        state_battle_win=STATE_BATTLE_WIN,
        state_battle_lose=STATE_BATTLE_LOSE,
        base_health_per_level=BASE_HEALTH_PER_LEVEL,
        base_damage_per_level=BASE_DAMAGE_PER_LEVEL,
        base_block_per_level=BASE_BLOCK_PER_LEVEL,
        enemy_names=ENEMY_NAMES,
        db_name=DB_NAME)
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()