import arcade
import random
from src.entities.card import Card


class Player:
    def __init__(self, name="Player", base_max_hp=100,
                 base_health_per_level=10, experience_to_next_level=100):
        self.name = name
        self.level = 1
        self.experience = 0
        self.experience_to_next_level = experience_to_next_level
        self.base_max_hp = base_max_hp
        self.base_health_per_level = base_health_per_level
        self.max_hp = self.calculate_max_hp()
        self.current_hp = self.max_hp
        self.block = 0
        self.hand = []
        self.selected_card = None
        self.hand_sprites = arcade.SpriteList()
        self.has_shield_reflection = False
        self.damage_multiplier = 1.0
        self.damage_multiplier_turns = 0  # Оставшееся количество ходов действия множителя
        self.heal_amount = 0  # Количество восстановления здоровья
        self.heal_turns = 0  # Оставшееся количество ходов действия лечения

    def calculate_max_hp(self):
        return int(self.base_max_hp + (self.level - 1) * self.base_health_per_level)

    def add_experience(self, amount):
        """Добавляет опыт игроку"""
        self.experience += amount

        # Проверяем, достигнут ли новый уровень
        levels_gained = 0
        while self.experience >= self.experience_to_next_level:
            self.level_up()
            levels_gained += 1
            if levels_gained >= 5:
                break

        return self.experience, levels_gained

    def level_up(self):
        """Повышение уровня персонажа"""
        self.level += 1
        self.experience = max(0, self.experience - self.experience_to_next_level)

        # Увеличиваем необходимое количество опыта для следующего уровня
        self.experience_to_next_level = int(self.experience_to_next_level * 1.5)

        # Увеличиваем максимальное здоровье
        old_max_hp = self.max_hp
        self.max_hp = self.calculate_max_hp()

        # Восстанавливаем часть здоровья при повышении уровня
        hp_restored = int((self.max_hp - old_max_hp) * 0.5)
        self.current_hp = min(self.max_hp, self.current_hp + hp_restored)

        return self.level

    def take_damage(self, amount):
        # Применяем множитель урона от зелий
        actual_amount = int(amount * self.damage_multiplier)
        actual_damage = max(0, actual_amount - self.block)
        self.current_hp -= actual_damage
        self.block = max(0, self.block - actual_amount)
        return actual_damage

    def apply_potion_effects(self, delta_time=0):
        """Применяет эффекты зелий каждый ход"""
        # Лечение
        if self.heal_turns > 0:
            self.current_hp = min(self.max_hp, self.current_hp + self.heal_amount)
            self.heal_turns -= 1
            if self.heal_turns <= 0:
                self.heal_amount = 0

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

        suits = ['sword', 'shield', 'potion']
        all_cards = []

        for suit in suits:
            if suit == 'shield':
                values = range(2, 7)
            elif suit == 'potion':
                values = range(2, 8)  # 2-7 включительно
            else:  # sword
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

    def get_card_effect(self, card: Card, base_damage_per_level=0.2, base_block_per_level=0.15):
        """Получить эффект карты с учетом уровня игрока"""
        return card.get_effect_power(self.level, base_damage_per_level, base_block_per_level)

    def play_potion_card(self, card_value, player_level):
        """Обработка карты зелья с учетом уровня игрока"""
        if card_value == 2:
            # Зелье 2 уровня: лечит на 50 здоровья * уровень игрока
            heal_amount = int(50 + (50 * player_level * 0.1))
            self.current_hp = min(self.max_hp, self.current_hp + heal_amount)
            return f"Вы выпили зелье исцеления! +{heal_amount} HP"

        elif 3 <= card_value <= 6:
            multiplier = 1.0 + (card_value - 2) * 0.5
            self.damage_multiplier = multiplier
            self.damage_multiplier_turns = 3
            return f"Выпито зелье силы! Урон x{multiplier:.1f} на 3 хода"

        elif card_value == 7:
            heal_amount = 100
            self.current_hp = min(self.max_hp, self.current_hp + heal_amount)
            multiplier = 3.0
            self.damage_multiplier = multiplier
            self.damage_multiplier_turns = 5
            return f"Выпито легендарное зелье! +{heal_amount} HP, Урон x{multiplier} на 5 ходов"
        return "Неизвестное зелье"

    def reset_battle_stats(self):
        """Сбрасывает временные характеристики перед началом нового боя"""
        self.block = 0
        self.has_shield_reflection = False
        self.hand.clear()
        self.hand_sprites.clear()
        self.selected_card = None
        # Сбрасываем эффекты зелий
        self.damage_multiplier = 1.0
        self.damage_multiplier_turns = 0
        self.heal_amount = 0
        self.heal_turns = 0

    def save_to_db(self, db):
        """Сохранение игрока в базу данных"""
        db.save_player(self.name,
            self.level,
            self.experience,
            self.experience_to_next_level,
            self.max_hp,
            self.current_hp)

    def load_from_db(self, db, player_name):
        """Загрузка игрока из базы данных"""
        data = db.load_player(player_name)
        if data:
            self.name = data['name']
            self.level = data['level']
            self.experience = data['experience']
            self.experience_to_next_level = data['experience_to_next_level']
            self.max_hp = data['max_hp']
            self.current_hp = data['current_hp']
            return True
        return False


class WorldPlayer(arcade.Sprite):
    def __init__(self, player_scale=0.01, player_speed=100):
        super().__init__()
        self.textures = {
            'up': [],
            'down': [],
            'left': [],
            'right': []}
        self.textures['up'].append(arcade.load_texture("images/hero/up/up_1.jpg"))
        self.textures['up'].append(arcade.load_texture("images/hero/up/up_2.jpg"))

        self.textures['down'].append(arcade.load_texture("images/hero/down/down_1.jpg"))
        self.textures['down'].append(arcade.load_texture("images/hero/down/down_2.jpg"))

        self.textures['left'].append(arcade.load_texture("images/hero/left/left_1.jpg"))
        self.textures['left'].append(arcade.load_texture("images/hero/left/left_2.jpg"))

        self.textures['right'].append(arcade.load_texture("images/hero/right/right_1.jpg"))
        self.textures['right'].append(arcade.load_texture("images/hero/right/right_2.jpg"))
        self.set_texture_by_direction('down', 0)
        self.scale = player_scale
        self.center_x = 0
        self.center_y = 0
        self.speed = player_speed
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
