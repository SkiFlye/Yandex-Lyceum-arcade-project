import arcade
import random
import time
from arcade import Camera2D

from src.data.database import GameDatabase
from src.entities.player import WorldPlayer, Player
from src.entities.enemy import WorldEnemy
from src.game.battle_window import BattleWindow
from src.game.dungeon_window import DungeonWindow


class GameWorldWindow(arcade.View):
    def __init__(self,
                 screen_width=1200,
                 screen_height=800,
                 player_name=None,
                 player_scale=0.01,
                 player_speed=100,
                 enemy_radius=30,
                 tile_scaling=1.0,
                 camera_lerp=0.15,
                 base_health_per_level=10,
                 base_damage_per_level=0.2,
                 base_block_per_level=0.15,
                 db_name="data/game_save.db",
                 player=None):
        super().__init__()
        arcade.set_background_color(arcade.color.BLACK)
        # Сохраняем константы как атрибуты класса
        self.SCREEN_WIDTH = screen_width
        self.SCREEN_HEIGHT = screen_height
        self.PLAYER_SCALE = player_scale
        self.PLAYER_SPEED = player_speed
        self.ENEMY_RADIUS = enemy_radius
        self.TILE_SCALING = tile_scaling
        self.CAMERA_LERP = camera_lerp
        self.BASE_HEALTH_PER_LEVEL = base_health_per_level
        self.BASE_DAMAGE_PER_LEVEL = base_damage_per_level
        self.BASE_BLOCK_PER_LEVEL = base_block_per_level
        self.DB_NAME = db_name
        # Инициализация базы данных
        self.db = GameDatabase(db_name)
        self.player_name = player_name or "Player"
        # Основной объект игрока
        self.player = player
        # Музыка мира
        self.music_player = None
        self.music_volume = 0.4

    def setup(self):
        # Настройка мира
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
        if not self.player:
            self.player = Player(
                name=self.player_name,
                base_max_hp=100,
                base_health_per_level=self.BASE_HEALTH_PER_LEVEL,
                experience_to_next_level=100)
            # Пытаемся загрузить сохранение
            if not self.player.load_from_db(self.db, self.player_name):
                print("Создан новый персонаж Player")
            else:
                print(f"Загружен сохраненный персонаж: {self.player.name} (Ур.{self.player.level})")
        # Текстовые объекты для мира
        self.world_player_stats_text = None
        # Настройка мира
        self.setup_world()
        # Запускаем музыку мира
        self.play_world_music()

    def play_world_music(self):
        """Запускает музыку для мира"""
        self.stop_music()
        # Загружаем и запускаем музыку мира
        sound = arcade.load_sound("assets/world_melody.mp3")
        if sound:
            self.music_player = sound.play(volume=self.music_volume, loop=True)

    def stop_music(self):
        """Останавливает музыку"""
        if self.music_player:
            arcade.stop_sound(self.music_player)
            self.music_player = None

    def on_show_view(self):
        """Вызывается при показе этого View"""
        self.play_world_music()

    def on_hide_view(self):
        """Вызывается при скрытии этого View"""
        self.stop_music()

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

    def create_world_text_objects(self):
        """Создание текстовых объектов для мира"""
        self.world_instruction_texts = [
            arcade.Text("Управление: WASD или стрелки", 10, self.SCREEN_HEIGHT - 30,
                        arcade.color.WHITE, 14),
            arcade.Text("Подойдите к врагу для начала боя", 10, self.SCREEN_HEIGHT - 55,
                        arcade.color.WHITE, 14),
            arcade.Text("ESC - выход, F5 - сохранить игру", 10, self.SCREEN_HEIGHT - 80,
                        arcade.color.WHITE, 14)]
        # Отображение характеристик игрока в мире
        self.world_player_stats_text = arcade.Text(
            "",
            10, self.SCREEN_HEIGHT - 110,
            arcade.color.WHITE, 14)

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

    def start_battle(self, enemy_sprite):
        """Начинает битву с выбранным врагом"""
        # Останавливаем музыку мира
        self.stop_music()

        # Создаем окно битвы
        battle_window = BattleWindow(
            screen_width=self.SCREEN_WIDTH,
            screen_height=self.SCREEN_HEIGHT,
            player=self.player,
            enemy_sprite=enemy_sprite,
            base_damage_per_level=self.BASE_DAMAGE_PER_LEVEL,
            base_block_per_level=self.BASE_BLOCK_PER_LEVEL,
            db=self.db,
            return_callback=self.return_from_battle
        )
        battle_window.setup()
        self.window.show_view(battle_window)

    def return_from_battle(self, player, enemy_defeated=True, enemy_exp_value=0, respawn=False):
        """Возвращение из битвы в мир"""
        self.keys_pressed.clear()
        self.player = player
        if respawn:
            # Возвращаем героя на точку спавна в подземелье
            spawn_point = self.scene["spawn"][0]
            self.world_player.center_x = spawn_point.center_x
            self.world_player.center_y = spawn_point.center_y
            # Сбрасываем здоровье
            self.player.current_hp = self.player.max_hp
        # Если враг побежден, удаляем его с карты
        if enemy_defeated:
            enemy_sprite_to_remove = None
            for enemy in self.enemy_sprites:
                if not enemy.is_alive:
                    enemy_sprite_to_remove = enemy
                    break

            if enemy_sprite_to_remove:
                self.enemy_sprites.remove(enemy_sprite_to_remove)

        # Возвращаемся в мир и запускаем музыку
        self.window.show_view(self)
        self.play_world_music()

    def on_draw(self):
        self.clear()
        self.draw_world()

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

    def on_update(self, delta_time):
        self.update_world(delta_time)

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
            self.enter_dungeon()
        self.update_camera(delta_time)

    def enter_dungeon(self):
        """Переход в подземелье"""
        # Останавливаем музыку мира
        self.stop_music()

        dungeon_window = DungeonWindow(
            screen_width=self.SCREEN_WIDTH,
            screen_height=self.SCREEN_HEIGHT,
            player_name=self.player.name,
            player_scale=self.PLAYER_SCALE,
            player_speed=self.PLAYER_SPEED,
            enemy_radius=self.ENEMY_RADIUS,
            tile_scaling=self.TILE_SCALING,
            camera_lerp=self.CAMERA_LERP,
            base_health_per_level=self.BASE_HEALTH_PER_LEVEL,
            base_damage_per_level=self.BASE_DAMAGE_PER_LEVEL,
            base_block_per_level=self.BASE_BLOCK_PER_LEVEL,
            db_name=self.DB_NAME,
            player=self.player)

        dungeon_window.setup()
        self.window.show_view(dungeon_window)

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

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.save_game()
            arcade.close_window()
            return

        if key in (arcade.key.W, arcade.key.A, arcade.key.S, arcade.key.D,
                   arcade.key.UP, arcade.key.DOWN, arcade.key.LEFT, arcade.key.RIGHT):
            self.keys_pressed.add(key)
        elif key == arcade.key.F5:
            self.save_game()

    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)

    def save_game(self):
        """Сохраняет игру в базу данных"""
        if self.player:
            self.player.save_to_db(self.db)
