import arcade

from src.entities.card import Card
from src.entities.enemy import Enemy


class BattleWindow(arcade.View):
    def __init__(self,
                 screen_width=1200,
                 screen_height=800,
                 actual_card_width=153,
                 actual_card_height=204,
                 card_margin=40,
                 hand_y=260,
                 enemy_center_x=600,
                 enemy_center_y=550,
                 deck_x=1000,
                 deck_y=570,
                 player=None,
                 enemy_sprite=None,
                 base_damage_per_level=0.2,
                 base_block_per_level=0.15,
                 db=None,
                 return_callback=None):
        super().__init__()
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
        self.BASE_DAMAGE_PER_LEVEL = base_damage_per_level
        self.BASE_BLOCK_PER_LEVEL = base_block_per_level
        # Основные объекты
        self.player = player
        self.enemy_sprite = enemy_sprite
        self.db = db
        self.return_callback = return_callback
        # Музыка битвы
        self.music_player = None
        self.music_volume = 0.5

    def setup(self):
        self.game_state = "battle"  # "battle", "win", "lose"
        self.battle_player = None
        self.battle_enemy = None
        self.deck_sprite = None
        self.deck_spritelist = None
        self.battle_turn = "player"
        self.battle_timer = 0
        # Текстовые объекты для боя
        self.deck_text = None
        self.deck_warning_text = None
        self.player_hp_text = None
        self.player_level_text = None
        self.turn_text = None
        self.win_text = None
        self.lose_text = None
        self.return_text = None
        self.experience_gained_text = None
        # Эффекты зелий
        self.potion_effect_text = None
        self.potion_message_timer = 0
        # Настройка битвы
        self.setup_battle()
        # Запускаем музыку битвы
        self.play_battle_music()

    def play_battle_music(self):
        self.stop_music()
        # Загружаем и запускаем музыку битвы
        sound = arcade.load_sound("assets/battle_melody.mp3")
        if sound:
            self.music_player = sound.play(volume=self.music_volume, loop=True)

    def stop_music(self):
        if self.music_player:
            arcade.stop_sound(self.music_player)
            self.music_player = None

    def on_show_view(self):
        """Вызывается при показе этого View"""
        self.play_battle_music()

    def on_hide_view(self):
        """Вызывается при скрытии этого View"""
        self.stop_music()

    def setup_battle(self):
        """Настройка битвы"""
        # Используем основного игрока для боя
        self.battle_player = self.player
        self.battle_player.reset_battle_stats()  # Сбрасываем временные характеристики
        # Используем уровень, имя и тип врага с карты мира
        enemy_level = self.enemy_sprite.level
        enemy_name = self.enemy_sprite.name
        enemy_type = self.enemy_sprite.enemy_type
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
            self.enemy_exp_value = self.enemy_sprite.exp_value * 3  # Босс дает в 3 раза больше опыта
        elif enemy_type == "skeleton":
            self.enemy_exp_value = self.enemy_sprite.exp_value * 2  # Скелет дает в 2 раза больше опыта
        else:
            self.enemy_exp_value = self.enemy_sprite.exp_value

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

        self.create_battle_text_objects()

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
            self.SCREEN_WIDTH - 1000, self.SCREEN_HEIGHT - 250,
            arcade.color.WHITE, 24,
            anchor_x="center")

        self.win_text = arcade.Text(
            "ПОБЕДА!",
            self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2,
            arcade.color.GOLD, 50,
            anchor_x="center", anchor_y="center")

        self.lose_text = arcade.Text(
            "ПОРАЖЕНИЕ!",
            self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 + 300,
            arcade.color.RED, 50,
            anchor_x="center", anchor_y="center")

        self.return_text = arcade.Text(
            "Нажмите ПРОБЕЛ для продолжения путешествия",
            self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 310,
            arcade.color.WHITE, 24,
            anchor_x="center", anchor_y="center")

        self.experience_gained_text = arcade.Text(
            "",
            self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 120,
            arcade.color.CYAN, 28,
            anchor_x="center", anchor_y="center")

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
                self.game_state = "win"
                return True
        else:
            actual_damage = self.battle_player.take_damage(damage)
            if self.battle_player.current_hp <= 0:
                self.game_state = "lose"
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
        # Обрабатываем разные типы карт
        if card_to_play.suit == 'sword':
            # Карта атаки
            effect = self.battle_player.get_card_effect(
                card_to_play,
                self.BASE_DAMAGE_PER_LEVEL,
                self.BASE_BLOCK_PER_LEVEL)
            damage = int(effect)

            if self.battle_player.damage_multiplier > 1.0:
                damage = int(damage * self.battle_player.damage_multiplier)
                self.battle_player.damage_multiplier_turns -= 1
                if self.battle_player.damage_multiplier_turns <= 0:
                    self.battle_player.damage_multiplier = 1.0
                    self.battle_player.damage_multiplier_turns = 0
            self.battle_enemy.take_damage(damage)

        elif card_to_play.suit == 'shield':
            # Карта защиты
            effect = self.battle_player.get_card_effect(
                card_to_play,
                self.BASE_DAMAGE_PER_LEVEL,
                self.BASE_BLOCK_PER_LEVEL)

            if card_to_play.value == 6:
                self.battle_player.has_shield_reflection = True
                block = int(effect)
                self.battle_player.block += block
            else:
                block = int(effect)
                self.battle_player.block += block

        elif card_to_play.suit == 'potion':
            # Карта зелья - передаем уровень игрока
            potion_effect = self.battle_player.play_potion_card(
                card_to_play.value,
                self.battle_player.level)
            # Выводим сообщение о эффекте зелья
            self.potion_effect_text = arcade.Text(
                potion_effect,
                self.SCREEN_WIDTH // 2,
                self.SCREEN_HEIGHT - 110,
                arcade.color.CYAN,
                20,
                anchor_x="center")
            # Сохраняем время показа сообщения
            self.potion_message_timer = 2.0  # Показывать 2 секунды
        # Удаляем карту из руки
        self.battle_player.remove_card_from_hand(card_to_play)
        # Проверяем, побежден ли враг
        if self.battle_enemy.current_hp <= 0:
            exp_gained = self.enemy_exp_value
            new_exp, levels_gained = self.battle_player.add_experience(exp_gained)
            self.gained_experience = exp_gained
            self.levels_gained = levels_gained
            self.game_state = "win"
            return
        # Передаем ход врагу
        self.battle_turn = "enemy"
        self.battle_timer = 0
        # Перепозиционируем карты
        self.position_cards()
        # Если рука пустая, берем новую
        if len(self.battle_player.hand) == 0:
            self.draw_new_hand()
            self.position_cards()

    def on_draw(self):
        self.clear()
        if self.game_state == "battle":
            self.draw_battle()
        elif self.game_state == "win":
            self.draw_battle_win()
        elif self.game_state == "lose":
            self.draw_battle_lose()

    def draw_battle(self):
        # Фон битвы
        self.background = arcade.load_texture('images/battle_background.jpg')
        arcade.draw_texture_rect(self.background, arcade.rect.XYWH(
            self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2,
            self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        # Враг
        self.battle_enemy.draw()
        # Колода
        self.deck_spritelist.draw()
        self.deck_text.draw()

        if len(self.battle_player.hand) >= 6:
            self.deck_warning_text.value = "Полная рука!"
            self.deck_warning_text.draw()
        # Карты в руке
        self.battle_player.hand_sprites.draw()
        # Эффекты зелий
        if self.battle_player.damage_multiplier_turns > 0:
            multiplier_text = arcade.Text(
                f"Урон x{self.battle_player.damage_multiplier:.1f} ({self.battle_player.damage_multiplier_turns} ход.)",
                50,
                self.SCREEN_HEIGHT - 120,
                arcade.color.WHITE,
                16
            )
            multiplier_text.draw()
        if hasattr(self, 'potion_effect_text') and self.potion_message_timer > 0:
            self.potion_effect_text.draw()

        # Текстовая информация
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
        time_card_spritelist = arcade.SpriteList()
        time_card = arcade.Sprite("images/cards/time_card.jpg")
        time_card.width = self.ACTUAL_CARD_WIDTH * 2
        time_card.height = self.ACTUAL_CARD_HEIGHT * 2
        time_card.center_x = self.SCREEN_WIDTH // 2
        time_card.center_y = self.SCREEN_HEIGHT // 2
        time_card_spritelist.append(time_card)
        time_card_spritelist.draw()
        self.return_text.value = "Нет, я не погибну здесь!.."
        self.return_text.draw()

    def on_update(self, delta_time):
        if self.game_state == "battle":
            self.update_battle(delta_time)

    def update_battle(self, delta_time):
        if self.battle_turn == "enemy":
            self.battle_timer += delta_time
            if self.battle_timer >= 1.0:
                self.enemy_attack()
                self.battle_timer = 0
                self.battle_turn = "player"
        # Обновляем таймер сообщения о зелье
        if hasattr(self, 'potion_message_timer'):
            self.potion_message_timer -= delta_time
            if self.potion_message_timer <= 0:
                self.potion_message_timer = 0
        # Применяем эффекты зелий каждый ход
        if self.battle_player:
            self.battle_player.apply_potion_effects(delta_time)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            if self.game_state == "lose":
                arcade.close_window()
            elif self.game_state == "battle":
                # Возвращаемся в мир
                if self.return_callback:
                    self.return_callback(self.player, enemy_defeated=False)
            return

        if self.game_state == "battle":
            self.on_key_press_battle(key, modifiers)
        elif self.game_state == "win":
            self.on_key_press_battle_win(key, modifiers)
        elif self.game_state == "lose":
            self.on_key_press_battle_lose(key, modifiers)

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
            # Сохраняем игру и возвращаемся в мир
            if self.db and self.player:
                self.player.save_to_db(self.db)
            if self.return_callback:
                self.return_callback(self.player, enemy_defeated=True, enemy_exp_value=self.enemy_exp_value)

    def on_key_press_battle_lose(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            arcade.close_window()

    def on_mouse_press(self, x, y, button, modifiers):
        if self.game_state == "lose":
            card_center_x = self.SCREEN_WIDTH // 2
            card_center_y = self.SCREEN_HEIGHT // 2 - 100
            card_width = self.ACTUAL_CARD_WIDTH * 2
            card_height = self.ACTUAL_CARD_HEIGHT * 2
            left = card_center_x - card_width / 2
            right = card_center_x + card_width / 2
            top = card_center_y + card_height / 2
            bottom = card_center_y - card_height / 2
            if left <= x <= right and bottom <= y <= top:
                if self.return_callback:
                    self.player.current_hp = self.player.max_hp
                    self.return_callback(self.player, enemy_defeated=False, respawn=True)
            return

        if self.game_state != "battle":
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