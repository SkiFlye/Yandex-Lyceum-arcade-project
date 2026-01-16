import arcade


class Enemy:
    def __init__(self, name=None, base_max_hp=50, level=1,
                 enemy_center_x=600, enemy_center_y=500, enemy_radius=60, enemy_type="goblin"):
        self.name = name
        self.level = level
        self.enemy_type = enemy_type

        # Разные базовые HP для разных типов врагов
        if enemy_type == "goblin":
            base_hp = 30
            self.scale = 0.4
        elif enemy_type == "skeleton":
            base_hp = 60
            self.scale = 0.4
        elif enemy_type == "necromancer":
            base_hp = 150
            self.scale = 0.8
        else:
            base_hp = 50
            self.scale = 0.4

        self.max_hp = base_hp + (level - 1) * 10
        self.current_hp = self.max_hp

        # Разная сила атаки для разных типов врагов
        if enemy_type == "goblin":
            attack_base = 1.0
        elif enemy_type == "skeleton":
            attack_base = 1.5
        elif enemy_type == "necromancer":
            attack_base = 2.5
        else:
            attack_base = 1.0

        self.attack_power = attack_base + (level - 1) * 0.5
        self.center_x = enemy_center_x
        self.center_y = enemy_center_y
        self.radius = enemy_radius

        # Загружаем текстуры для анимации
        self.textures = []
        self.load_animation_textures()

        # Создаем спрайт и SpriteList
        self.sprite = arcade.Sprite()
        self.sprite.texture = self.textures[0]
        self.sprite.scale = self.scale
        self.sprite.center_x = enemy_center_x
        self.sprite.center_y = enemy_center_y

        # SpriteList для отрисовки
        self.sprite_list = arcade.SpriteList()
        self.sprite_list.append(self.sprite)

        # Параметры анимации
        self.animation_timer = 0
        self.animation_speed = 0.3
        self.current_frame = 0

        # Текстовые объекты
        self.hp_text = None
        self.level_text = None
        self.create_text_object()

    def load_animation_textures(self):
        """Загружает текстуры для анимации врага"""
        # Загружаем два кадра для анимации
        texture1 = arcade.load_texture(f"images/enemies/{self.enemy_type}/{self.enemy_type}_1.jpg")
        texture2 = arcade.load_texture(f"images/enemies/{self.enemy_type}/{self.enemy_type}_2.jpg")

        self.textures.append(texture1)
        self.textures.append(texture2)

    def update_animation(self, delta_time):
        """Обновляет анимацию врага"""
        self.animation_timer += delta_time

        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.textures)
            self.sprite.texture = self.textures[self.current_frame]

    def take_damage(self, amount):
        self.current_hp = max(0, self.current_hp - amount)
        if self.hp_text:
            self.hp_text.value = f"HP: {self.current_hp}/{self.max_hp}"
        return self.current_hp <= 0

    def get_attack(self):
        return int(self.attack_power)

    def create_text_object(self):
        self.hp_text = arcade.Text(
            f"HP: {self.current_hp}/{self.max_hp}",
            self.center_x, self.center_y + self.radius + 120,
            arcade.color.WHITE, 20,
            anchor_x="center", anchor_y="center")
        self.level_text = arcade.Text(
            f"{self.name} (Ур.{self.level})",
            self.center_x, self.center_y + self.radius + 150,
            arcade.color.YELLOW, 22,
            anchor_x="center", anchor_y="center")

    def draw(self):
        """Отрисовка врага с анимацией"""
        # Рисуем спрайт через SpriteList
        self.sprite_list.draw()
        # Рисуем текстовую информацию
        self.hp_text.draw()
        self.level_text.draw()


class WorldEnemy(arcade.Sprite):
    """Класс для врага на карте мира с анимацией"""
    def __init__(self, name="Враг", level=1, center_x=0, center_y=0, enemy_radius=30, enemy_type="goblin"):
        super().__init__()
        self.name = name
        self.level = level
        self.enemy_type = enemy_type
        self.enemy_radius = enemy_radius
        # Загружаем текстуры для анимации
        self.textures = []
        self.load_animation_textures()
        # Устанавливаем первую текстуру
        self.texture = self.textures[0]
        self.scale = self.get_scale_for_type()
        self.center_x = center_x
        self.center_y = center_y
        # Характеристики врага
        self.exp_value = level * 25
        # Флаг для отслеживания, уничтожен ли враг
        self.is_alive = True
        # Для анимации
        self.animation_timer = 0
        self.animation_speed = 0.5  # Смена кадров каждые 0.5 секунды
        self.current_frame = 0
        # Текстовый объект для имени
        self.name_text = arcade.Text(
            f"{self.name} (Ур.{self.level})",
            center_x,
            center_y + enemy_radius + 100,
            arcade.color.RED,
            14,
            anchor_x="center")

    def get_scale_for_type(self):
        """Возвращает масштаб в зависимости от типа врага"""
        scales = {
            "goblin": 0.15,
            "skeleton": 0.15,
            "necromancer": 0.1}
        return scales.get(self.enemy_type, 0.2)

    def load_animation_textures(self):
        """Загружает текстуры для анимации врага в мире"""
        # Загружаем два кадра для анимации
        texture1 = arcade.load_texture(f"images/enemies/{self.enemy_type}/{self.enemy_type}_1.jpg")
        texture2 = arcade.load_texture(f"images/enemies/{self.enemy_type}/{self.enemy_type}_2.jpg")
        self.textures.append(texture1)
        self.textures.append(texture2)
    def update_animation(self, delta_time):
        """Обновляет анимацию врага"""
        self.animation_timer += delta_time
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.textures)
            self.texture = self.textures[self.current_frame]

    def update_text_position(self, camera_x, camera_y):
        """Обновляет позицию текста относительно камеры"""
        if not self.is_alive:
            return
        screen_x = self.center_x - camera_x
        screen_y = self.center_y - camera_y
        # Обновляем позицию текста
        self.name_text.x = screen_x
        self.name_text.y = screen_y + self.enemy_radius + 100

    def destroy(self):
        """Уничтожение врага"""
        self.is_alive = False
        # Помечаем спрайт для удаления из SpriteList
        if self in self.sprite_lists:
            self.remove_from_sprite_lists()

    def draw_name(self):
        """Рисует имя врага"""
        if self.is_alive:
            self.name_text.draw()