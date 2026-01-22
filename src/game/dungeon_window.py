import arcade
import random
import time
from arcade import Camera2D

from src.data.database import GameDatabase
from src.entities.player import WorldPlayer, Player
from src.entities.enemy import WorldEnemy
from src.game.battle_window import BattleWindow


class DungeonWindow(arcade.View):
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
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        # Сохраняем константы
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

        # Флаг для золота (чтобы дать опыт один раз)
        self.gold_collected = False

        # Музыка подземелья
        self.music_player = None
        self.music_volume = 0.4

    def setup(self):
        """Настройка подземелья"""
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
        self.gold_sprites = arcade.SpriteList()
        self.world_instruction_texts = []

        # Если игрок не передан, создаем нового или загружаем
        if not self.player:
            self.player = Player(
                name=self.player_name,
                base_max_hp=100,
                base_health_per_level=self.BASE_HEALTH_PER_LEVEL,
                experience_to_next_level=100)

            if not self.player.load_from_db(self.db):
                print("Создан новый персонаж Player")
            else:
                print(f"Загружен сохраненный персонаж: {self.player.name} (Ур.{self.player.level})")

        # Сбрасываем флаг золота
        self.gold_collected = False

        # Текстовые объекты
        self.world_player_stats_text = None

        # Настройка подземелья
        self.setup_dungeon()

        # Запускаем музыку подземелья
        self.play_dungeon_music()

    def play_dungeon_music(self):
        """Запускает музыку для подземелья"""
        try:
            self.stop_music()
            sound = arcade.load_sound("dungeon_melody.mp3")
            if sound:
                self.music_player = sound.play(volume=self.music_volume, loop=True)
                print("Музыка подземелья запущена")
        except:
            print("Не удалось загрузить музыку подземелья")
            self.music_player = None

    def stop_music(self):
        """Останавливает музыку"""
        if self.music_player:
            self.music_player.stop()
            self.music_player = None

    def on_show_view(self):
        """Вызывается при показе этого View"""
        self.play_dungeon_music()

    def on_hide_view(self):
        """Вызывается при скрытии этого View"""
        self.stop_music()

    def setup_dungeon(self):
        """Настройка подземелья"""
        # Загружаем карту level2.tmx
        self.tile_map = arcade.load_tilemap("level2.tmx", scaling=self.TILE_SCALING)
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

        # Устанавливаем позицию игрока на точку спавна
        spawn_point = self.scene["spawn"][0]
        self.world_player.center_x = spawn_point.center_x
        self.world_player.center_y = spawn_point.center_y

        # Создаем SpriteList для игрока
        self.world_player_sprite_list = arcade.SpriteList()
        self.world_player_sprite_list.append(self.world_player)

        # Устанавливаем начальную позицию камеры на игрока
        self.world_camera.position = (
            self.world_player.center_x - self.SCREEN_WIDTH / 2,
            self.world_player.center_y - self.SCREEN_HEIGHT / 2)

        # Создаем врагов
        self.create_dungeon_enemies()

        # Создаем золотые тайлы
        self.create_gold_tiles()

        # Создаем физический движок с слоем collision
        self.physics_engine = arcade.PhysicsEngineSimple(
            self.world_player,
            self.scene["collision"])

        self.create_dungeon_text_objects()

    def create_dungeon_enemies(self):
        """Создание врагов в подземелье"""
        self.enemy_sprites.clear()
        for spawn_point in self.scene["skeleton_spawn"]:
            enemy_level = random.randint(15, 20)
            enemy_name = "Темный скелет"
            enemy = WorldEnemy(
                name=enemy_name,
                level=enemy_level,
                center_x=spawn_point.center_x,
                center_y=spawn_point.center_y,
                enemy_radius=self.ENEMY_RADIUS,
                enemy_type="skeleton")
            self.enemy_sprites.append(enemy)

        for spawn_point in self.scene["ghost_spawn"]:
            enemy_level = random.randint(15, 20)
            enemy_name = "Призрак"
            enemy = WorldEnemy(
                name=enemy_name,
                level=enemy_level,
                center_x=spawn_point.center_x,
                center_y=spawn_point.center_y,
                enemy_radius=self.ENEMY_RADIUS,
                enemy_type="ghost")
            self.enemy_sprites.append(enemy)

        # Минотавры (30 уровня)
        for spawn_point in self.scene["minotaur_spawn"]:
            enemy_level = 30
            enemy_name = "Минотавр"
            enemy = WorldEnemy(
                name=enemy_name,
                level=enemy_level,
                center_x=spawn_point.center_x,
                center_y=spawn_point.center_y,
                enemy_radius=self.ENEMY_RADIUS * 1.5,
                enemy_type="minotaur")
            self.enemy_sprites.append(enemy)

        for spawn_point in self.scene["necromancer's_spawn"]:
            enemy_level = 30
            enemy_name = "Приспешник тьмы"
            enemy = WorldEnemy(
                name=enemy_name,
                level=enemy_level,
                center_x=spawn_point.center_x,
                center_y=spawn_point.center_y,
                enemy_radius=self.ENEMY_RADIUS,
                enemy_type="necromancer")
            self.enemy_sprites.append(enemy)

        # Мастер карт (50 уровня, финальный босс)
        for spawn_point in self.scene["card_master_spawn"]:
            enemy_level = 50
            enemy_name = "Мастер карт"
            enemy = WorldEnemy(
                name=enemy_name,
                level=enemy_level,
                center_x=spawn_point.center_x,
                center_y=spawn_point.center_y,
                enemy_radius=self.ENEMY_RADIUS * 2,
                enemy_type="card_master")
            self.enemy_sprites.append(enemy)

        # Также добавляем обычных врагов для разнообразия
        for spawn_point in self.scene["goblin_spawn"]:
            enemy_level = random.randint(10, 15)
            enemy_name = "Темный гоблин"
            enemy = WorldEnemy(
                name=enemy_name,
                level=enemy_level,
                center_x=spawn_point.center_x,
                center_y=spawn_point.center_y,
                enemy_radius=self.ENEMY_RADIUS,
                enemy_type="goblin")
            self.enemy_sprites.append(enemy)

        print(
            f"Создано врагов в подземелье: Призраков - {len([e for e in self.enemy_sprites if e.enemy_type == 'ghost'])}, "
            f"Минотавров - {len([e for e in self.enemy_sprites if e.enemy_type == 'minotaur'])}, "
            f"Мастеров карт - {len([e for e in self.enemy_sprites if e.enemy_type == 'card_master'])}, "
            f"Темных гоблинов - {len([e for e in self.enemy_sprites if e.enemy_type == 'goblin'])}")

    def create_gold_tiles(self):
        """Создание золотых тайлов"""
        self.gold_sprites.clear()
        for gold_tile in self.scene["gold"]:
            self.gold_sprites.append(gold_tile)

    def create_dungeon_text_objects(self):
        """Создание текстовых объектов для подземелья"""
        self.world_instruction_texts = [
            arcade.Text("Управление: WASD или стрелки", 10, self.SCREEN_HEIGHT - 30,
                        arcade.color.WHITE, 14),
            arcade.Text("Подземелье", 10, self.SCREEN_HEIGHT - 55,
                        arcade.color.YELLOW, 14),
            arcade.Text("ESC - выход, F5 - сохранить игру", 10, self.SCREEN_HEIGHT - 105,
                        arcade.color.WHITE, 14)]

        # Отображение характеристик игрока
        self.world_player_stats_text = arcade.Text(
            "",
            10, self.SCREEN_HEIGHT - 135,
            arcade.color.WHITE, 14)

    def start_battle(self, enemy_sprite):
        """Начинает битву с выбранным врагом"""
        self.stop_music()

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

    def return_from_battle(self, player, enemy_defeated=False, enemy_exp_value=0, respawn=False):
        """Возвращение из битвы в подземелье"""
        self.player = player
        # Очищаем списки движения
        self.keys_pressed.clear()
        self.world_player.dx = 0
        self.world_player.dy = 0
        self.world_player.is_walking = False
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

        # Возвращаемся в подземелье и запускаем музыку
        self.window.show_view(self)
        self.play_dungeon_music()

    def check_gold_collision(self):
        """Проверка коллизии с золотыми монетами"""
        if self.gold_collected:
            return
        gold_hits = arcade.check_for_collision_with_list(self.world_player, self.gold_sprites)
        if gold_hits:
            self.gold_collected = True
            # Даем +5 уровней
            for _ in range(5):
                 self.player.level_up()
            # Удаляем золотые тайлы
            for gold in gold_hits:
                self.gold_sprites.remove(gold)

    def on_draw(self):
        self.clear()
        self.draw_dungeon()

    def draw_dungeon(self):
        self.world_camera.use()
        # Отрисовываем слои из карты
        self.scene["floor"].draw()
        if not self.gold_collected:
            self.gold_sprites.draw()
        # Отрисовываем врагов и игрока
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
            f"HP: {self.player.current_hp}/{self.player.max_hp} | "
            f"Подземелье")
        self.world_player_stats_text.draw()
        # Показываем сообщение о золоте
        if self.gold_collected:
            gold_text = arcade.Text(
                "Вы получили +5 уровней!",
                self.SCREEN_WIDTH // 2,
                100,
                arcade.color.GOLD,
                24,
                anchor_x="center",
                anchor_y="center")
            gold_text.draw()

    def on_update(self, delta_time):
        self.update_dungeon(delta_time)

    def update_dungeon(self, delta_time):
        # Обновление движения игрока
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
        # Обновление движка
        self.physics_engine.update()
        # Обновление анимации врагов
        for enemy in self.enemy_sprites:
            if enemy.is_alive:
                enemy.update_animation(delta_time)
        # Проверка столкновений с врагами
        enemies_hit = arcade.check_for_collision_with_list(self.world_player, self.enemy_sprites)
        for enemy in enemies_hit:
            if enemy.is_alive:
                enemy.is_alive = False
                self.start_battle(enemy)
                return
        # Проверка столкновений с золотом
        self.check_gold_collision()
        # Обновление камеры
        self.update_camera(delta_time)

    def update_camera(self, delta_time=0):
        """Обновление камеры с плавным слежением"""
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
        self.player.save_to_db(self.db)