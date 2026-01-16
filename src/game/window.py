import arcade
import random
import math
import time
from arcade import Camera2D

from roguelike_card_game.src.data.database import GameDatabase
from roguelike_card_game.src.entities.card import Card
from roguelike_card_game.src.entities.player import Player, WorldPlayer
from roguelike_card_game.src.entities.enemy import Enemy, WorldEnemy


class GameWindow(arcade.Window):
    def __init__(self,
                 screen_width=1200,
                 screen_height=800,
                 actual_card_width=153,
                 actual_card_height=204,
                 card_margin=40,
                 hand_y=200,
                 enemy_center_x=600,
                 enemy_center_y=500,
                 deck_x=1000,
                 deck_y=500,
                 player_scale=0.01,
                 player_speed=100,
                 enemy_radius=30,
                 tile_scaling=1.0,
                 camera_lerp=0.15,
                 state_world="world",
                 state_battle="battle",
                 state_battle_win="battle_win",
                 state_battle_lose="battle_lose",
                 base_health_per_level=10,
                 base_damage_per_level=0.2,
                 base_block_per_level=0.15,
                 enemy_names=None,
                 db_name="data/game_save.db"):

        super().__init__(screen_width, screen_height, "Карточный Рогалик")
        arcade.set_background_color(arcade.color.BLACK)
        # Сохраняем константы как атрибуты класса
        self.SCREEN_WIDTH = screen_width
        self.SCREEN_HEIGHT = screen_height
        self.ACTUAL_CARD_WIDTH = actual_card_width
        self.ACTUAL_CARD_HEIGHT = actual_card_height
        self.CARD_MARGIN = card_margin
        self.HAND_Y = hand_y
        self.ENEMY_CENTER_X = enemy_center_x
        self.ENEMY_CENTER_Y = enemy_center_y
        self.DECK_X = deck_x
        self.DECK_Y = deck_y
        self.PLAYER_SCALE = player_scale
        self.PLAYER_SPEED = player_speed
        self.ENEMY_RADIUS = enemy_radius
        self.TILE_SCALING = tile_scaling
        self.CAMERA_LERP = camera_lerp
        self.STATE_WORLD = state_world
        self.STATE_BATTLE = state_battle
        self.STATE_BATTLE_WIN = state_battle_win
        self.STATE_BATTLE_LOSE = state_battle_lose
        self.BASE_HEALTH_PER_LEVEL = base_health_per_level
        self.BASE_DAMAGE_PER_LEVEL = base_damage_per_level
        self.BASE_BLOCK_PER_LEVEL = base_block_per_level
        self.ENEMY_NAMES = enemy_names or ["Гоблин"]
        self.DB_NAME = db_name
        # Инициализация базы данных
        self.db = GameDatabase(db_name)

    def setup(self):
        self.game_state = self.STATE_WORLD
        self.scene = None
        self.world_camera = Camera2D()
        self.gui_camera = Camera2D()
        self.physics_engine = None
        self.world_player = None
        self.world_player_sprite_list = None
        self.keys_pressed = set()
        self.map_left = 0
        self.map_right = 0
        self.map_bottom = 0
        self.map_top = 0
        self.enemy_sprites = arcade.SpriteList()
        self.cave_entrance_sprites = arcade.SpriteList()
        self.world_instruction_texts = []
        self.debug_text = None
        # Основной объект игрока
        self.player = Player(
            name="Player",
            base_max_hp=100,
            base_health_per_level=self.BASE_HEALTH_PER_LEVEL,
            experience_to_next_level=100)
        # Пытаемся загрузить сохранение
        if not self.player.load_from_db(self.db):
            print("Создан новый персонаж Player")
        else:
            print(f"Загружен сохраненный персонаж: {self.player.name} (Ур.{self.player.level})")
        self.battle_player = None
        self.battle_enemy = None
        self.deck_sprite = None
        self.deck_spritelist = None
        self.battle_turn = "player"
        self.battle_timer = 0
        # Текстовые объекты для мира и боя
        self.deck_text = None
        self.deck_warning_text = None
        self.player_hp_text = None
        self.player_level_text = None
        self.turn_text = None
        self.win_text = None
        self.lose_text = None
        self.return_text = None
        self.experience_gained_text = None
        # Настройка мира
        self.setup_world()

    def setup_world(self):
        """Настройка мира"""
        # Загружаем карту
        self.tile_map = arcade.load_tilemap("level1.tmx", scaling=self.TILE_SCALING)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        # Устанавливаем границы карты
        self.map_left = 0
        self.map_bottom = 0
        self.map_right = self.tile_map.width * self.tile_map.tile_width * self.TILE_SCALING
        self.map_top = self.tile_map.height * self.tile_map.tile_height * self.TILE_SCALING
        self.world_width = self.map_right
        self.world_height = self.map_top
        # Создаем игрока
        self.world_player = WorldPlayer(
            player_scale=self.PLAYER_SCALE,
            player_speed=self.PLAYER_SPEED)
        self.world_player.scale = 0.15
        # Создаем SpriteList для игрока
        self.world_player_sprite_list = arcade.SpriteList()
        self.world_player_sprite_list.append(self.world_player)
        # Устанавливаем позицию игрока на точку спавна
        spawn_point = self.scene["spawn"][0]
        self.world_player.center_x = spawn_point.center_x
        self.world_player.center_y = spawn_point.center_y
        # Устанавливаем начальную позицию камеры на игрока
        self.world_camera.position = (
            self.world_player.center_x - self.SCREEN_WIDTH / 2,
            self.world_player.center_y - self.SCREEN_HEIGHT / 2)
        # Создаем врагов
        self.create_enemies()
        for sprite in self.scene["cave_entrance"]:
            self.cave_entrance_sprites.append(sprite)
        # Создаем физический движок с слоем collision
        self.physics_engine = arcade.PhysicsEngineSimple(
            self.world_player,
            self.scene["collision"])
        self.create_world_text_objects()
        self.create_battle_text_objects()

    def create_world_text_objects(self):
        """Создание текстовых объектов для мира"""
        self.world_instruction_texts = [
            arcade.Text("Управление: WASD или стрелки", 10, self.SCREEN_HEIGHT - 30,
                        arcade.color.WHITE, 14),
            arcade.Text("Подойдите к врагу (красный квадрат) для начала боя", 10, self.SCREEN_HEIGHT - 55,
                        arcade.color.WHITE, 14),
            arcade.Text("ESC - выход, F5 - сохранить игру", 10, self.SCREEN_HEIGHT - 80,
                        arcade.color.WHITE, 14)]
        # Отображение характеристик игрока в мире
        self.world_player_stats_text = arcade.Text(
            "",
            10, self.SCREEN_HEIGHT - 110,
            arcade.color.WHITE, 14)

    def create_battle_text_objects(self):
        """Создание текстовых объектов для боя"""
        self.deck_text = arcade.Text(
            "Колода",
            self.DECK_X, self.DECK_Y - self.ACTUAL_CARD_HEIGHT // 2 - 20,
            arcade.color.WHITE, 16,
            anchor_x="center", anchor_y="center")
        self.deck_warning_text = arcade.Text(
            "",
            self.DECK_X, self.DECK_Y - self.ACTUAL_CARD_HEIGHT // 2 - 40,
            arcade.color.RED, 14,
            anchor_x="center", anchor_y="center")
        self.player_hp_text = arcade.Text(
            "",
            50, self.SCREEN_HEIGHT - 50,
            arcade.color.WHITE, 18)
        self.player_level_text = arcade.Text(
            "",
            50, self.SCREEN_HEIGHT - 80,
            arcade.color.GOLD, 16)
        self.turn_text = arcade.Text(
            "",
            self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT - 50,
            arcade.color.WHITE, 24,
            anchor_x="center")
        self.win_text = arcade.Text(
            "ПОБЕДА!",
            self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2,
            arcade.color.GOLD, 50,
            anchor_x="center", anchor_y="center")
        self.lose_text = arcade.Text(
            "ПОРАЖЕНИЕ!",
            self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2,
            arcade.color.RED, 50,
            anchor_x="center", anchor_y="center")
        self.return_text = arcade.Text(
            "Нажмите ПРОБЕЛ для продолжения путешествия",
            self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 60,
            arcade.color.WHITE, 24,
            anchor_x="center", anchor_y="center")

        self.experience_gained_text = arcade.Text(
            "",
            self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 120,
            arcade.color.CYAN, 28,
            anchor_x="center", anchor_y="center")

    def create_enemies(self):
        self.enemy_sprites.clear()
        if "goblin_spawn" in self.scene:
            for spawn_point in self.scene["goblin_spawn"]:
                enemy_level = random.randint(1, 3)
                enemy_name = "Гоблин"
                enemy = WorldEnemy(
                    name=enemy_name,
                    level=enemy_level,
                    center_x=spawn_point.center_x,
                    center_y=spawn_point.center_y,
                    enemy_radius=self.ENEMY_RADIUS,
                    enemy_type="goblin")
                self.enemy_sprites.append(enemy)
        if "skeleton_spawn" in self.scene:
            for spawn_point in self.scene["skeleton_spawn"]:
                enemy_level = 5  # Скелеты всегда 5 уровня
                enemy_name = "Скелет"
                enemy = WorldEnemy(
                    name=enemy_name,
                    level=enemy_level,
                    center_x=spawn_point.center_x,
                    center_y=spawn_point.center_y,
                    enemy_radius=self.ENEMY_RADIUS,
                    enemy_type="skeleton")
                self.enemy_sprites.append(enemy)
        if "necromancer's_spawn" in self.scene:
            for spawn_point in self.scene["necromancer's_spawn"]:
                enemy_level = 10
                enemy_name = "Некромант"
                enemy = WorldEnemy(
                    name=enemy_name,
                    level=enemy_level,
                    center_x=spawn_point.center_x,
                    center_y=spawn_point.center_y,
                    enemy_radius=self.ENEMY_RADIUS,
                    enemy_type="necromancer"
                )
                self.enemy_sprites.append(enemy)
        print(f"Создано врагов: Гоблинов - {len([e for e in self.enemy_sprites if e.enemy_type == 'goblin'])}, "
              f"Скелетов - {len([e for e in self.enemy_sprites if e.enemy_type == 'skeleton'])}, "
              f"Некромантов - {len([e for e in self.enemy_sprites if e.enemy_type == 'necromancer'])}")

    def start_battle(self, enemy_sprite):
        self.game_state = self.STATE_BATTLE
        # Используем основного игрока для боя
        self.battle_player = self.player
        self.battle_player.reset_battle_stats()  # Сбрасываем временные характеристики
        # Используем уровень, имя и тип врага с карты мира
        enemy_level = enemy_sprite.level
        enemy_name = enemy_sprite.name
        enemy_type = enemy_sprite.enemy_type
        # Создаем врага для боя с определенным типом
        self.battle_enemy = Enemy(
            name=enemy_name,
            level=enemy_level,
            enemy_center_x=self.ENEMY_CENTER_X,
            enemy_center_y=self.ENEMY_CENTER_Y,
            enemy_radius=60,
            enemy_type=enemy_type)
        self.battle_enemy.create_text_object()
        # Сохраняем опыт, который даст враг
        if enemy_type == "necromancer":
            self.enemy_exp_value = enemy_sprite.exp_value * 3  # Босс дает в 3 раза больше опыта
        elif enemy_type == "skeleton":
            self.enemy_exp_value = enemy_sprite.exp_value * 2  # Скелет дает в 2 раза больше опыта
        else:
            self.enemy_exp_value = enemy_sprite.exp_value
        self.deck_spritelist = arcade.SpriteList()
        self.deck_sprite = arcade.Sprite("images/cards/inverted_card.jpg")
        self.deck_sprite.width = self.ACTUAL_CARD_WIDTH
        self.deck_sprite.height = self.ACTUAL_CARD_HEIGHT
        self.deck_sprite.center_x = self.DECK_X
        self.deck_sprite.center_y = self.DECK_Y
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
        for _ in range(6):
            self.battle_player.add_random_card()

    def position_cards(self):
        if not self.battle_player:
            return
        total_cards = len(self.battle_player.hand)
        if total_cards == 0:
            return
        distance_between_centers = self.ACTUAL_CARD_WIDTH + self.CARD_MARGIN
        group_center_x = self.SCREEN_WIDTH // 2
        if total_cards % 2 == 0:
            first_card_offset = -((total_cards / 2) - 0.5) * distance_between_centers
        else:
            first_card_offset = -((total_cards - 1) / 2) * distance_between_centers
        for i, card in enumerate(self.battle_player.hand):
            # Устанавливаем размеры карты
            card.sprite.width = self.ACTUAL_CARD_WIDTH
            card.sprite.height = self.ACTUAL_CARD_HEIGHT
            card_center_x = group_center_x + first_card_offset + (i * distance_between_centers)
            card.sprite.center_x = card_center_x
            card.sprite.center_y = self.HAND_Y

    def enemy_attack(self):
        if not self.battle_player or not self.battle_enemy:
            return False
        damage = self.battle_enemy.get_attack()
        if self.battle_player.has_shield_reflection:
            self.battle_player.has_shield_reflection = False
            reflected_damage = damage
            self.battle_enemy.take_damage(reflected_damage)
            if self.battle_enemy.current_hp <= 0:
                self.game_state = self.STATE_BATTLE_WIN
                return True
        else:
            actual_damage = self.battle_player.take_damage(damage)
            if self.battle_player.current_hp <= 0:
                self.game_state = self.STATE_BATTLE_LOSE
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
        # Используем эффект карты с учетом уровня игрока
        effect = self.battle_player.get_card_effect(
            card_to_play,
            self.BASE_DAMAGE_PER_LEVEL,
            self.BASE_BLOCK_PER_LEVEL)
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
            self.game_state = self.STATE_BATTLE_WIN
            return
        self.battle_turn = "enemy"
        self.battle_timer = 0
        self.position_cards()
        if len(self.battle_player.hand) == 0:
            self.draw_new_hand()
            self.position_cards()

    def on_draw(self):
        self.clear()
        if self.game_state == self.STATE_WORLD:
            self.draw_world()
        elif self.game_state == self.STATE_BATTLE:
            self.draw_battle()
        elif self.game_state == self.STATE_BATTLE_WIN:
            self.draw_battle_win()
        elif self.game_state == self.STATE_BATTLE_LOSE:
            self.draw_battle_lose()

    def draw_world(self):
        self.world_camera.use()
        self.scene["grass"].draw()
        self.scene["flowers"].draw()
        self.scene["river"].draw()
        self.scene["bridges"].draw()
        self.scene["railings"].draw()
        self.scene["cave"].draw()
        self.scene["cave_entrance"].draw()
        self.scene["cemetery"].draw()
        cam_x, cam_y = self.world_camera.position
        enemies_to_remove = []
        for enemy in self.enemy_sprites:
            if not enemy.is_alive:
                enemies_to_remove.append(enemy)
        self.enemy_sprites.draw()
        self.world_player_sprite_list.draw()
        self.gui_camera.use()
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
            level_up_text = arcade.Text(
                f"НОВЫЙ УРОВЕНЬ {self.battle_player.level}!",
                self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 160,
                arcade.color.GREEN, 32,
                anchor_x="center", anchor_y="center")
            level_up_text.draw()
        self.return_text.draw()

    def draw_battle_lose(self):
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)
        self.lose_text.draw()
        self.return_text.value = "Нажмите ESC для выхода"
        self.return_text.draw()

    def on_update(self, delta_time):
        if self.game_state == self.STATE_WORLD:
            self.update_world(delta_time)
        elif self.game_state == self.STATE_BATTLE:
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
        if arcade.key.UP in self.keys_pressed:
            self.world_player.dy += 1
            new_direction = 'up'
        if arcade.key.DOWN in self.keys_pressed:
            self.world_player.dy -= 1
            new_direction = 'down'
        if arcade.key.LEFT in self.keys_pressed:
            self.world_player.dx -= 1
            new_direction = 'left'
        if arcade.key.RIGHT in self.keys_pressed:
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
        for enemy in self.enemy_sprites:
            if enemy.is_alive:
                enemy.update_animation(delta_time)
        enemies_hit = arcade.check_for_collision_with_list(self.world_player, self.enemy_sprites)
        for enemy in enemies_hit:
            if enemy.is_alive:
                enemy.is_alive = False
                self.start_battle(enemy)
                return
        cave_hits = arcade.check_for_collision_with_list(self.world_player, self.cave_entrance_sprites)
        if cave_hits:
            print("Вход в пещеру! Уровень 2 будет добавлен позже.")
        self.update_camera(delta_time)

    def update_camera(self, delta_time=0):
        """Обновление камеры с плавным слежением и ограничением границ"""
        target_x = self.world_player.center_x
        target_y = self.world_player.center_y
        cam_center_x, cam_center_y = self.world_camera.position
        new_cam_center_x = cam_center_x + (target_x - cam_center_x) * self.CAMERA_LERP
        new_cam_center_y = cam_center_y + (target_y - cam_center_y) * self.CAMERA_LERP
        min_center_x = self.SCREEN_WIDTH / 2
        min_center_y = self.SCREEN_HEIGHT / 2
        max_center_x = self.map_right - self.SCREEN_WIDTH / 2
        max_center_y = self.map_top - self.SCREEN_HEIGHT / 2
        if new_cam_center_x < min_center_x:
            new_cam_center_x = min_center_x
        elif new_cam_center_x > max_center_x:
            new_cam_center_x = max_center_x
        if new_cam_center_y < min_center_y:
            new_cam_center_y = min_center_y
        elif new_cam_center_y > max_center_y:
            new_cam_center_y = max_center_y
        self.world_camera.position = (new_cam_center_x, new_cam_center_y)
        self.gui_camera.position = (self.SCREEN_WIDTH / 2, self.SCREEN_HEIGHT / 2)

    def update_battle(self, delta_time):
        if self.battle_turn == "enemy":
            self.battle_timer += delta_time
            if self.battle_timer >= 1.0:
                self.enemy_attack()
                self.battle_timer = 0
                self.battle_turn = "player"

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            if self.game_state == self.STATE_BATTLE_LOSE:
                self.close()
            elif self.game_state == self.STATE_BATTLE:
                self.return_to_world()
            else:
                self.save_game()
                self.close()
            return
        if self.game_state == self.STATE_WORLD:
            self.on_key_press_world(key, modifiers)
        elif self.game_state == self.STATE_BATTLE:
            self.on_key_press_battle(key, modifiers)
        elif self.game_state == self.STATE_BATTLE_WIN:
            self.on_key_press_battle_win(key, modifiers)
        elif self.game_state == self.STATE_BATTLE_LOSE:
            self.on_key_press_battle_lose(key, modifiers)

    def on_key_press_world(self, key, modifiers):
        if key in (arcade.key.W, arcade.key.A, arcade.key.S, arcade.key.D,
                   arcade.key.UP, arcade.key.DOWN, arcade.key.LEFT, arcade.key.RIGHT):
            self.keys_pressed.add(key)
        elif key == arcade.key.F5:
            self.save_game()

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
        if self.game_state != self.STATE_BATTLE:
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
            left = sprite.center_x - self.ACTUAL_CARD_WIDTH / 2
            right = sprite.center_x + self.ACTUAL_CARD_WIDTH / 2
            bottom = sprite.center_y - self.ACTUAL_CARD_HEIGHT / 2
            top = sprite.center_y + self.ACTUAL_CARD_HEIGHT / 2
            if left <= x <= right and bottom <= y <= top:
                self.battle_player.selected_card = card
                self.play_card(card)
                break

    def return_to_world(self):
        if self.game_state == self.STATE_BATTLE_WIN:
            self.save_game()
        self.game_state = self.STATE_WORLD
        self.battle_player = None
        self.battle_enemy = None
        self.deck_spritelist = None

    def save_game(self):
        """Сохраняет игру в базу данных"""
        if self.player:
            self.player.save_to_db(self.db)

    def load_game(self):
        """Загружает игру из базы данных"""
        if self.player.load_from_db(self.db):
            return True
        return False