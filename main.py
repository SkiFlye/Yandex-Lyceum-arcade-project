import arcade
import random
from dataclasses import dataclass
import math
import time
from arcade import Camera2D
import sqlite3

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
PLAYER_SCALE = 0.15
PLAYER_SPEED = 100
ENEMY_DETECTION_RADIUS = 100
ENEMY_RADIUS = 30
TILE_SCALING = 1.0
CAMERA_LERP = 0.15
STATE_WORLD = "world"
STATE_BATTLE = "battle"
STATE_BATTLE_WIN = "battle_win"
STATE_BATTLE_LOSE = "battle_lose"
BASE_HEALTH_PER_LEVEL = 10
BASE_DAMAGE_PER_LEVEL = 0.2
BASE_BLOCK_PER_LEVEL = 0.15
ENEMY_NAMES = ["Гоблин"]


class GameDatabase:
    def __init__(self):
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect("game_save.db")
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_save (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL DEFAULT 'Player',
            level INTEGER DEFAULT 1,
            experience INTEGER DEFAULT 0,
            max_hp INTEGER DEFAULT 100,
            current_hp INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()

    def save_player(self, level, experience, max_hp, current_hp):
        conn = sqlite3.connect("game_save.db")
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM player_save')
        existing = cursor.fetchone()
        if existing:
            cursor.execute('''UPDATE player_save 
            SET level = ?, experience = ?, max_hp = ?, current_hp = ?, last_played = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (level, experience, max_hp, current_hp, existing[0]))
        else:
            cursor.execute('''INSERT INTO player_save (name, level, experience, max_hp, current_hp)
            VALUES (?, ?, ?, ?, ?)
            ''', ('Player', level, experience, max_hp, current_hp))
        conn.commit()
        conn.close()

    def load_player(self):
        conn = sqlite3.connect("game_save.db")
        cursor = conn.cursor()
        cursor.execute('''SELECT name, level, experience, max_hp, current_hp FROM player_save LIMIT 1''')
        result = cursor.fetchone()
        conn.close()
        if result:
            return {'name': result[0], 'level': result[1], 'experience': result[2], 'max_hp': result[3],
                    'current_hp': result[4]}
        return None


@dataclass
class Card:
    suit: str
    value: int

    def __post_init__(self):
        self.sprite = arcade.Sprite(f"images/cards/{self.suit}_{self.value}.jpg")
        self.sprite.width = ACTUAL_CARD_WIDTH
        self.sprite.height = ACTUAL_CARD_HEIGHT

    def is_valid_value(self):
        if self.suit == 'shield':
            return 2 <= self.value <= 6
        else:
            return 2 <= self.value <= 10

    def get_effect_power(self, player_level=1):
        multipliers = {'sword': 1.0, 'shield': 1.0, }
        base_power = self.value * multipliers[self.suit]
        if self.suit == 'sword':
            level_multiplier = 1.0 + (player_level - 1) * BASE_DAMAGE_PER_LEVEL
        elif self.suit == 'shield':
            level_multiplier = 1.0 + (player_level - 1) * BASE_BLOCK_PER_LEVEL
        else:
            level_multiplier = 1.0
        return int(base_power * level_multiplier)


class Enemy:
    def __init__(self, name=None, base_max_hp=50, level=1):
        self.name = name or random.choice(ENEMY_NAMES)
        self.level = level
        self.max_hp = base_max_hp + (level - 1) * 10
        self.current_hp = self.max_hp
        self.attack_power = 1 + (level - 1) * 0.5
        self.center_x = ENEMY_CENTER_X
        self.center_y = ENEMY_CENTER_Y
        self.radius = 60

    def take_damage(self, amount):
        self.current_hp = max(0, self.current_hp - amount)
        return self.current_hp <= 0

    def get_attack(self):
        return int(self.attack_power)

    def create_text_object(self):
        self.hp_text = arcade.Text("", self.center_x, self.center_y + self.radius + 40, arcade.color.WHITE, 20,
                                   anchor_x="center", anchor_y="center")
        self.level_text = arcade.Text(f"{self.name} (Ур.{self.level})", self.center_x, self.center_y + self.radius + 70,
                                      arcade.color.YELLOW, 22, anchor_x="center", anchor_y="center")

    def draw(self):
        arcade.draw_circle_filled(self.center_x, self.center_y, self.radius, arcade.color.RED)
        self.hp_text.value = f"HP: {self.current_hp}/{self.max_hp}"
        self.hp_text.draw()
        self.level_text.draw()


class Player:
    def __init__(self, name="Player", base_max_hp=100):
        self.name = name
        self.level = 1
        self.experience = 0
        self.experience_to_next_level = 100
        self.base_max_hp = base_max_hp
        self.max_hp = self.calculate_max_hp()
        self.current_hp = self.max_hp
        self.block = 0
        self.hand = []
        self.hand_sprites = arcade.SpriteList()
        self.has_shield_reflection = False

    def calculate_max_hp(self):
        return int(self.base_max_hp + (self.level - 1) * BASE_HEALTH_PER_LEVEL)

    def take_damage(self, amount):
        actual_damage = max(0, amount - self.block)
        self.current_hp -= actual_damage
        self.block = max(0, self.block - amount)
        return actual_damage

    def add_card_to_hand(self, card: Card):
        if len(self.hand) >= 6:
            return False
        for existing_card in self.hand:
            if existing_card.suit == card.suit and existing_card.value == card.value:
                return False
        self.hand.append(card)
        self.hand_sprites.append(card.sprite)
        return True

    def remove_card_from_hand(self, card: Card):
        for i, c in enumerate(self.hand):
            if c.suit == card.suit and c.value == card.value:
                self.hand.pop(i)
                if card.sprite in self.hand_sprites:
                    self.hand_sprites.remove(card.sprite)
                break

    def add_random_card(self):
        if len(self.hand) >= 6:
            return False
        suits = ['sword', 'shield']
        all_cards = []
        for suit in suits:
            if suit == 'shield':
                values = range(2, 7)
            else:
                values = range(2, 11)

            for value in values:
                all_cards.append((suit, value))
        available_cards = []
        for suit, value in all_cards:
            card_exists = False
            for card in self.hand:
                if card.suit == suit and card.value == value:
                    card_exists = True
                    break
            if not card_exists:
                available_cards.append((suit, value))
        if available_cards:
            suit, value = random.choice(available_cards)
            card = Card(suit, value)
            return self.add_card_to_hand(card)
        return False

    def add_experience(self, amount):
        self.experience += amount
        levels_gained = 0
        while self.experience >= self.experience_to_next_level:
            self.level_up()
            levels_gained += 1
            if levels_gained >= 5:
                break
        return self.experience, levels_gained

    def level_up(self):
        self.level += 1
        self.experience = max(0, self.experience - self.experience_to_next_level)
        self.experience_to_next_level = int(self.experience_to_next_level * 1.5)
        old_max_hp = self.max_hp
        self.max_hp = self.calculate_max_hp()
        hp_restored = int((self.max_hp - old_max_hp) * 0.5)
        self.current_hp = min(self.max_hp, self.current_hp + hp_restored)
        return self.level

    def get_card_effect(self, card: Card):
        return card.get_effect_power(self.level)

    def reset_battle_stats(self):
        self.block = 0
        self.has_shield_reflection = False
        self.hand.clear()
        self.hand_sprites.clear()

    def save_to_db(self, db):
        db.save_player(self.level, self.experience, self.max_hp, self.current_hp)

    def load_from_db(self, db):
        data = db.load_player()
        if data:
            self.name = data['name']
            self.level = data['level']
            self.experience = data['experience']
            self.max_hp = data['max_hp']
            self.current_hp = data['current_hp']
            return True
        return False


class WorldPlayer(arcade.Sprite):
    def __init__(self):
        super().__init__()
        self.textures = {'up': [], 'down': [], 'left': [], 'right': []}
        self.textures['up'].append(arcade.load_texture("images/hero/up/up_1.jpg"))
        self.textures['up'].append(arcade.load_texture("images/hero/up/up_2.jpg"))
        self.textures['down'].append(arcade.load_texture("images/hero/down/down_1.jpg"))
        self.textures['down'].append(arcade.load_texture("images/hero/down/down_2.jpg"))
        self.textures['left'].append(arcade.load_texture("images/hero/left/left_1.jpg"))
        self.textures['left'].append(arcade.load_texture("images/hero/left/left_2.jpg"))
        self.textures['right'].append(arcade.load_texture("images/hero/right/right_1.jpg"))
        self.textures['right'].append(arcade.load_texture("images/hero/right/right_2.jpg"))
        self.set_texture_by_direction('down', 0)
        self.center_x = SCREEN_WIDTH / 2
        self.center_y = SCREEN_HEIGHT / 2
        self.speed = PLAYER_SPEED
        self.dx = 0
        self.dy = 0
        self.current_direction = 'down'
        self.walk_frame = 0
        self.last_walk_time = 0
        self.walk_frame_duration = 0.3
        self.is_walking = False

    def set_texture_by_direction(self, direction, frame):
        self.texture = self.textures[direction][frame]
        self.current_direction = direction


class WorldEnemy(arcade.Sprite):
    def __init__(self, name="Враг", level=1, center_x=0, center_y=0):
        super().__init__()
        self.texture = arcade.make_soft_square_texture(ENEMY_RADIUS * 2, arcade.color.RED, 255, 255)
        self.scale = 1.0
        self.center_x = center_x
        self.center_y = center_y
        self.name = name
        self.level = level
        self.exp_value = level * 25
        self.is_alive = True
        self.name_text = arcade.Text(f"{self.name} (Ур.{self.level})", self.center_x, self.center_y + ENEMY_RADIUS + 20,
                                     arcade.color.YELLOW, 14, anchor_x="center", anchor_y="center")

    def update_text_position(self, camera_x, camera_y):
        if not self.is_alive:
            return
        screen_x = self.center_x - camera_x
        screen_y = self.center_y - camera_y
        self.name_text.x = screen_x
        self.name_text.y = screen_y + ENEMY_RADIUS + 20

    def destroy(self):
        self.is_alive = False
        if self in self.sprite_lists:
            self.remove_from_sprite_lists()


class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Карточный Рогалик")
        arcade.set_background_color(arcade.color.BLACK)
        self.db = GameDatabase()

    def setup(self):
        self.game_state = STATE_WORLD
        self.world_camera = Camera2D()
        self.gui_camera = Camera2D()
        self.keys_pressed = set()
        self.map_left = 0
        self.map_right = 0
        self.map_bottom = 0
        self.map_top = 0
        self.enemy_sprites = arcade.SpriteList()
        self.cave_entrance_sprites = arcade.SpriteList()
        self.world_instruction_texts = []
        self.player = Player(name="Player")
        if not self.player.load_from_db(self.db):
            print("Создан новый персонаж Player")
        else:
            print(f"Загружен сохраненный персонаж: {self.player.name} (Ур.{self.player.level})")
        self.battle_turn = "player"
        self.battle_timer = 0
        self.setup_world()

    def setup_world(self):
        self.tile_map = arcade.load_tilemap("level1.tmx", scaling=TILE_SCALING)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        self.map_left = 0
        self.map_bottom = 0
        self.map_right = self.tile_map.width * self.tile_map.tile_width * TILE_SCALING
        self.map_top = self.tile_map.height * self.tile_map.tile_height * TILE_SCALING
        self.world_width = self.map_right
        self.world_height = self.map_top
        self.world_player = WorldPlayer()
        self.world_player.scale = PLAYER_SCALE
        self.world_player_sprite_list = arcade.SpriteList()
        self.world_player_sprite_list.append(self.world_player)
        spawn_point = self.scene["spawn"][0]
        self.world_player.center_x = spawn_point.center_x
        self.world_player.center_y = spawn_point.center_y
        self.world_camera.position = (self.world_player.center_x - SCREEN_WIDTH / 2,
                                      self.world_player.center_y - SCREEN_HEIGHT / 2)
        self.create_enemies()
        for sprite in self.scene["cave_entrance"]:
            self.cave_entrance_sprites.append(sprite)
        self.physics_engine = arcade.PhysicsEngineSimple(self.world_player, self.scene["collision"])
        self.create_world_text_objects()
        self.create_battle_text_objects()

    def create_world_text_objects(self):
        self.world_instruction_texts = [arcade.Text("Управление: WASD или стрелки", 10, SCREEN_HEIGHT - 30,
                                                    arcade.color.WHITE, 14),
                                        arcade.Text("Подойдите к врагу (красный квадрат) для начала боя",
                                                    10, SCREEN_HEIGHT - 55, arcade.color.WHITE, 14),
                                        arcade.Text("ESC - выход", 10, SCREEN_HEIGHT - 80, arcade.color.WHITE, 14)]
        self.world_player_stats_text = arcade.Text("", 10, SCREEN_HEIGHT - 110, arcade.color.WHITE, 14)

    def create_battle_text_objects(self):
        self.deck_text = arcade.Text("Колода", DECK_X, DECK_Y - ACTUAL_CARD_HEIGHT // 2 - 20, arcade.color.WHITE, 16,
                                     anchor_x="center", anchor_y="center")
        self.deck_warning_text = arcade.Text("", DECK_X, DECK_Y - ACTUAL_CARD_HEIGHT // 2 - 40, arcade.color.RED, 14,
                                             anchor_x="center", anchor_y="center")
        self.player_hp_text = arcade.Text("", 50, SCREEN_HEIGHT - 50, arcade.color.WHITE, 18)
        self.player_level_text = arcade.Text("", 50, SCREEN_HEIGHT - 80, arcade.color.GOLD, 16)
        self.turn_text = arcade.Text("", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50, arcade.color.WHITE, 24,
                                     anchor_x="center")
        self.win_text = arcade.Text("ПОБЕДА!", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, arcade.color.GOLD, 50,
                                    anchor_x="center", anchor_y="center")
        self.lose_text = arcade.Text("ПОРАЖЕНИЕ!", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, arcade.color.RED, 50,
                                     anchor_x="center", anchor_y="center")
        self.return_text = arcade.Text("Нажмите ПРОБЕЛ для продолжения", SCREEN_WIDTH // 2,
                                       SCREEN_HEIGHT // 2 - 60, arcade.color.WHITE, 24,
                                       anchor_x="center", anchor_y="center")
        self.experience_gained_text = arcade.Text("", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120, arcade.color.GREEN,
                                                  28, anchor_x="center", anchor_y="center")

    def create_enemies(self):
        self.enemy_sprites.clear()
        num_enemies = random.randint(3, 5)
        for i in range(num_enemies):
            enemy_level = random.randint(1, 3)
            enemy_name = random.choice(ENEMY_NAMES)
            valid_position = False
            attempts = 0
            while not valid_position and attempts < 100:
                enemy_x = random.randint(100, 900 - 100)
                enemy_y = random.randint(100, 900 - 100)
                on_spawn = False
                for spawn_point in self.scene["spawn"]:
                    distance = math.sqrt((enemy_x - spawn_point.center_x) ** 2 + (enemy_y - spawn_point.center_y) ** 2)
                    if distance < 200:
                        on_spawn = True
                        break
                on_collision = False
                temp_sprite = arcade.SpriteSolidColor(ENEMY_RADIUS * 2, ENEMY_RADIUS * 2, arcade.color.RED)
                temp_sprite.center_x = enemy_x
                temp_sprite.center_y = enemy_y
                for wall in self.scene["collision"]:
                    if arcade.check_for_collision(temp_sprite, wall):
                        on_collision = True
                        break
                valid_position = not (on_spawn or on_collision)
                attempts += 1
            if valid_position:
                enemy = WorldEnemy(name=enemy_name, level=enemy_level, center_x=enemy_x, center_y=enemy_y)
                self.enemy_sprites.append(enemy)

    def start_battle(self, enemy_sprite):
        self.game_state = STATE_BATTLE
        self.battle_player = self.player
        self.battle_player.reset_battle_stats()
        enemy_level = enemy_sprite.level
        enemy_name = enemy_sprite.name
        self.battle_enemy = Enemy(name=enemy_name, level=enemy_level)
        self.battle_enemy.create_text_object()
        self.enemy_exp_value = enemy_sprite.exp_value
        self.deck_spritelist = arcade.SpriteList()
        self.deck_sprite = arcade.Sprite("images/cards/inverted_card.jpg")
        self.deck_sprite.width = ACTUAL_CARD_WIDTH
        self.deck_sprite.height = ACTUAL_CARD_HEIGHT
        self.deck_sprite.center_x = DECK_X
        self.deck_sprite.center_y = DECK_Y
        self.deck_spritelist.append(self.deck_sprite)
        self.draw_new_hand()
        self.position_cards()
        self.battle_timer = 0
        self.battle_turn = "player"

    def draw_new_hand(self):
        if not self.battle_player:
            return
        self.battle_player.hand.clear()
        self.battle_player.hand_sprites.clear()
        self.battle_player.has_shield_reflection = False
        for i in range(6):
            self.battle_player.add_random_card()

    def position_cards(self):
        if not self.battle_player:
            return
        total_cards = len(self.battle_player.hand)
        if total_cards == 0:
            return
        distance_between_centers = ACTUAL_CARD_WIDTH + CARD_MARGIN
        group_center_x = SCREEN_WIDTH // 2
        if total_cards % 2 == 0:
            first_card_offset = -((total_cards / 2) - 0.5) * distance_between_centers
        else:
            first_card_offset = -((total_cards - 1) / 2) * distance_between_centers
        for i, card in enumerate(self.battle_player.hand):
            card_center_x = group_center_x + first_card_offset + (i * distance_between_centers)
            card.sprite.center_x = card_center_x
            card.sprite.center_y = HAND_Y

    def enemy_attack(self):
        if not self.battle_player or not self.battle_enemy:
            return False
        damage = self.battle_enemy.get_attack()
        if self.battle_player.has_shield_reflection:
            self.battle_player.has_shield_reflection = False
            reflected_damage = damage
            self.battle_enemy.take_damage(reflected_damage)
            if self.battle_enemy.current_hp <= 0:
                self.game_state = STATE_BATTLE_WIN
                return True
        else:
            actual_damage = self.battle_player.take_damage(damage)
            if self.battle_player.current_hp <= 0:
                self.game_state = STATE_BATTLE_LOSE
                return True
        self.battle_player.block = 0
        return False

    def play_card(self, card: Card):
        if not self.battle_player or not self.battle_enemy:
            return
        card_to_play = None
        for c in self.battle_player.hand:
            if c.suit == card.suit and c.value == card.value:
                card_to_play = c
                break
        if not card_to_play:
            return
        effect = self.battle_player.get_card_effect(card_to_play)
        if card_to_play.suit == 'sword':
            damage = int(effect)
            self.battle_enemy.take_damage(damage)
        elif card_to_play.suit == 'shield':
            if card_to_play.value == 6:
                self.battle_player.has_shield_reflection = True
                block = int(effect)
                self.battle_player.block += block
            else:
                block = int(effect)
                self.battle_player.block += block
        self.battle_player.remove_card_from_hand(card_to_play)
        if self.battle_enemy.current_hp <= 0:
            exp_gained = self.enemy_exp_value
            new_exp, levels_gained = self.battle_player.add_experience(exp_gained)
            self.gained_experience = exp_gained
            self.levels_gained = levels_gained
            self.game_state = STATE_BATTLE_WIN
            return
        self.battle_turn = "enemy"
        self.battle_timer = 0
        self.position_cards()
        if len(self.battle_player.hand) == 0:
            self.draw_new_hand()
            self.position_cards()

    def on_draw(self):
        self.clear()
        if self.game_state == STATE_WORLD:
            self.draw_world()
        elif self.game_state == STATE_BATTLE:
            self.draw_battle()
        elif self.game_state == STATE_BATTLE_WIN:
            self.draw_battle_win()
        elif self.game_state == STATE_BATTLE_LOSE:
            self.draw_battle_lose()

    def draw_world(self):
        self.world_camera.use()
        self.scene["grass"].draw()
        self.scene["flowers"].draw()
        self.scene["river"].draw()
        self.scene["bridge"].draw()
        self.scene["railings"].draw()
        self.scene["cave"].draw()
        self.scene["cave_entrance"].draw()
        cam_x, cam_y = self.world_camera.position
        enemies_to_remove = []
        for enemy in self.enemy_sprites:
            if enemy.is_alive:
                enemy.update_text_position(cam_x, cam_y)
            else:
                enemies_to_remove.append(enemy)
        self.enemy_sprites.draw()
        self.world_player_sprite_list.draw()
        self.gui_camera.use()
        for enemy in self.enemy_sprites:
            if enemy.is_alive:
                enemy.name_text.draw()
        for enemy in enemies_to_remove:
            enemy.remove_from_sprite_lists()
        for text in self.world_instruction_texts:
            text.draw()
        self.world_player_stats_text.value = (
            f"Имя: {self.player.name} | "
            f"Уровень: {self.player.level} | "
            f"Опыт: {self.player.experience}/{self.player.experience_to_next_level} | "
            f"HP: {self.player.current_hp}/{self.player.max_hp}")
        self.world_player_stats_text.draw()

    def draw_battle(self):
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)
        self.battle_enemy.draw()
        self.deck_spritelist.draw()
        self.deck_text.draw()
        if len(self.battle_player.hand) >= 6:
            self.deck_warning_text.value = "Полная рука!"
            self.deck_warning_text.draw()
        self.battle_player.hand_sprites.draw()
        self.player_hp_text.value = (
            f"{self.battle_player.name} HP: {self.battle_player.current_hp}/{self.battle_player.max_hp} | "
            f"Блок: {self.battle_player.block}")
        self.player_hp_text.draw()
        self.player_level_text.value = (
            f"Уровень: {self.battle_player.level} | "
            f"Опыт: {self.battle_player.experience}/{self.battle_player.experience_to_next_level}")
        self.player_level_text.draw()
        self.turn_text.value = f"Ход: {'Игрок' if self.battle_turn == 'player' else 'Враг'}"
        self.turn_text.draw()

    def draw_battle_win(self):
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)
        self.win_text.draw()
        self.experience_gained_text.value = f"+{self.gained_experience} опыта"
        self.experience_gained_text.draw()
        if self.levels_gained > 0:
            level_up_text = arcade.Text(f"НОВЫЙ УРОВЕНЬ {self.battle_player.level}!", SCREEN_WIDTH // 2,
                                        SCREEN_HEIGHT // 2 - 160, arcade.color.GREEN, 32, anchor_x="center",
                                        anchor_y="center")
            level_up_text.draw()
        self.return_text.draw()

    def draw_battle_lose(self):
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)
        self.lose_text.draw()
        self.return_text.value = "Нажмите ESC для выхода"
        self.return_text.draw()

    def on_update(self, delta_time):
        if self.game_state == STATE_WORLD:
            self.update_world(delta_time)
        elif self.game_state == STATE_BATTLE:
            self.update_battle(delta_time)

    def update_world(self, delta_time):
        new_direction = None
        self.world_player.dx = 0
        self.world_player.dy = 0

        if arcade.key.W in self.keys_pressed:
            self.world_player.dy += 1
            new_direction = 'up'
        if arcade.key.S in self.keys_pressed:
            self.world_player.dy -= 1
            new_direction = 'down'
        if arcade.key.A in self.keys_pressed:
            self.world_player.dx -= 1
            new_direction = 'left'
        if arcade.key.D in self.keys_pressed:
            self.world_player.dx += 1
            new_direction = 'right'
        self.world_player.is_walking = (self.world_player.dx != 0 or self.world_player.dy != 0)
        if new_direction and new_direction != self.world_player.current_direction:
            self.world_player.current_direction = new_direction
            self.world_player.set_texture_by_direction(self.world_player.current_direction, 0)
            self.world_player.walk_frame = 0
        if self.world_player.is_walking:
            current_time = time.time()
            if current_time - self.world_player.last_walk_time > self.world_player.walk_frame_duration:
                self.world_player.walk_frame = (self.world_player.walk_frame + 1) % 2
                self.world_player.last_walk_time = current_time
                self.world_player.set_texture_by_direction(self.world_player.current_direction,
                                                           self.world_player.walk_frame)
        else:
            self.world_player.set_texture_by_direction(self.world_player.current_direction, 0)
        if self.world_player.dx != 0 and self.world_player.dy != 0:
            factor = 0.7071
            self.world_player.dx *= factor
            self.world_player.dy *= factor
        self.world_player.center_x += self.world_player.dx * self.world_player.speed * delta_time
        self.world_player.center_y += self.world_player.dy * self.world_player.speed * delta_time
        self.physics_engine.update()
        enemies_hit = arcade.check_for_collision_with_list(self.world_player, self.enemy_sprites)
        for enemy in enemies_hit:
            if enemy.is_alive:
                enemy.is_alive = False
                self.start_battle(enemy)
                return
        cave_hits = arcade.check_for_collision_with_list(self.world_player, self.cave_entrance_sprites)
        if cave_hits:
            print("Подземелье. Будет разработано в будущем(наверное)")
        self.update_camera(delta_time)

    def update_camera(self, delta_time=0):
        target_x = self.world_player.center_x
        target_y = self.world_player.center_y
        cam_x, cam_y = self.world_camera.position
        cam_center_x = cam_x + SCREEN_WIDTH / 2
        cam_center_y = cam_y + SCREEN_HEIGHT / 2
        new_cam_center_x = cam_center_x + (target_x - cam_center_x) * CAMERA_LERP
        new_cam_center_y = cam_center_y + (target_y - cam_center_y) * CAMERA_LERP
        new_cam_x = new_cam_center_x - SCREEN_WIDTH / 2
        new_cam_y = new_cam_center_y - SCREEN_HEIGHT / 2
        half_width = SCREEN_WIDTH / 2
        half_height = SCREEN_HEIGHT / 2
        if new_cam_x < half_width:
            new_cam_x = half_width
        elif new_cam_x > self.world_width - half_width:
            new_cam_x = self.world_width - half_width
        if new_cam_y < half_height:
            new_cam_y = half_height
        elif new_cam_y > self.world_height - half_height:
            new_cam_y = self.world_height - half_height
        self.world_camera.position = (new_cam_x, new_cam_y)
        self.gui_camera.position = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

    def update_battle(self, delta_time):
        if self.battle_turn == "enemy":
            self.battle_timer += delta_time
            if self.battle_timer >= 1.0:
                self.enemy_attack()
                self.battle_timer = 0
                self.battle_turn = "player"

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            if self.game_state == STATE_BATTLE_LOSE:
                self.close()
            elif self.game_state == STATE_BATTLE:
                self.return_to_world()
            else:
                self.save_game()
                self.close()
            return
        if self.game_state == STATE_WORLD:
            self.on_key_press_world(key, modifiers)
        elif self.game_state == STATE_BATTLE:
            self.on_key_press_battle(key, modifiers)
        elif self.game_state == STATE_BATTLE_WIN:
            self.on_key_press_battle_win(key, modifiers)
        elif self.game_state == STATE_BATTLE_LOSE:
            self.on_key_press_battle_lose(key, modifiers)

    def on_key_press_world(self, key, modifiers):
        if key in (arcade.key.W, arcade.key.A, arcade.key.S, arcade.key.D,):
            self.keys_pressed.add(key)

    def on_key_press_battle(self, key, modifiers):
        if key == arcade.key.SPACE and self.battle_turn == "player":
            if self.enemy_attack():
                return
            self.draw_new_hand()
            self.position_cards()
            self.battle_turn = "player"
        if key == arcade.key.E and self.battle_turn == "player":
            if self.enemy_attack():
                return
            self.draw_new_hand()
            self.position_cards()
            self.battle_turn = "player"

    def on_key_press_battle_win(self, key, modifiers):
        if key == arcade.key.SPACE:
            self.return_to_world()

    def on_key_press_battle_lose(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.close()

    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.game_state != STATE_BATTLE:
            return
        clicked_deck = arcade.get_sprites_at_point((x, y), self.deck_spritelist)
        if clicked_deck:
            if len(self.battle_player.hand) < 6:
                if self.battle_player.add_random_card():
                    self.position_cards()
            return
        if self.battle_turn != "player":
            return
        for i in range(len(self.battle_player.hand) - 1, -1, -1):
            card = self.battle_player.hand[i]
            sprite = card.sprite
            left = sprite.center_x - ACTUAL_CARD_WIDTH / 2
            right = sprite.center_x + ACTUAL_CARD_WIDTH / 2
            bottom = sprite.center_y - ACTUAL_CARD_HEIGHT / 2
            top = sprite.center_y + ACTUAL_CARD_HEIGHT / 2
            if left <= x <= right and bottom <= y <= top:
                self.battle_player.selected_card = card
                self.play_card(card)
                break

    def return_to_world(self):
        if self.game_state == STATE_BATTLE_WIN:
            print(f"Опыт сохранен: {self.player.name} - Ур.{self.player.level}, "
                  f"Опыт: {self.player.experience}/{self.player.experience_to_next_level}")
            self.save_game()
        self.game_state = STATE_WORLD

    def save_game(self):
        if self.player:
            self.player.save_to_db(self.db)
            print(f"Игра сохранена: {self.player.name} (Ур.{self.player.level})")

    def load_game(self):
        if self.player.load_from_db(self.db):
            print(f"Игра загружена: {self.player.name} (Ур.{self.player.level})")
            return True
        return False


def main():
    window = GameWindow()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()