import arcade
import random
from arcade.particles import FadeParticle, Emitter, EmitBurst

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
        # Эмиттеры для желтых частиц (при клике)
        self.click_emitters = []
        self.yellow_textures = []
        # Кэш для оптимизации
        self.background_texture = None
        self.deck_texture = None
        self.time_card_texture = None

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

        # Очищаем старые эмиттеры
        self.click_emitters.clear()

        # Создаем текстуры для желтых частиц
        self.create_yellow_textures()

        # Настройка битвы
        self.setup_battle()

        # Запускаем музыку битвы
        self.play_battle_music()

    def create_yellow_textures(self):
        """Создает текстуры для желтых частиц (легкие версии)"""
        yellow_colors = [
            arcade.color.YELLOW,
            arcade.color.GOLD,
            arcade.color.ORANGE,]

        self.yellow_textures.clear()
        # Создаем очень маленькие текстуры (4-6 пикселей)
        for color in yellow_colors:
            size = random.randint(4, 6)
            texture = arcade.make_soft_circle_texture(size, color, 180, 0)
            self.yellow_textures.append(texture)

    def create_yellow_particles(self, x, y):
        """Создает эмиттер желтых частиц"""
        # Ограничиваем количество активных эмиттеров
        if len(self.click_emitters) >= 3:
            oldest = self.click_emitters.pop(0)
        # Мутатор для быстрого исчезновения
        def particle_mutator(particle):
            particle.alpha = max(0, particle.alpha - 15)  # Быстро исчезает
        # Создаем эмиттер с минимальным количеством частиц
        emitter = Emitter(
            center_xy=(x, y),
            emit_controller=EmitBurst(15),
            particle_factory=lambda e: FadeParticle(
                filename_or_texture=random.choice(self.yellow_textures),
                change_xy=arcade.math.rand_in_circle((0.0, 0.0), 3.0),  # Медленно разлетаются
                lifetime=random.uniform(0.3, 0.5),  # Очень быстро исчезают
                start_alpha=255,
                end_alpha=0,
                scale=3.0,
                mutation_callback=particle_mutator,
            ),
        )

        return emitter

    def play_battle_music(self):
        self.stop_music()
        sound = arcade.load_sound("assets/battle_melody.mp3")
        if sound:
            self.music_player = sound.play(volume=self.music_volume, loop=True)

    def stop_music(self):
        if self.music_player:
            arcade.stop_sound(self.music_player)
            self.music_player = None

    def on_show_view(self):
        self.play_battle_music()

    def on_hide_view(self):
        self.stop_music()
        # Очищаем все эмиттеры при скрытии
        self.click_emitters.clear()

    def cleanup_sprites(self):
        self.deck_spritelist = None
        self.battle_enemy = None
        self.deck_sprite = None
        self.background_texture = None
        self.click_emitters.clear()

    def setup_battle(self):
        """Оптимизированная настройка битвы"""
        self.background_texture = arcade.load_texture('images/battle_background.jpg')
        self.deck_texture = arcade.load_texture("images/cards/inverted_card.jpg")
        self.time_card_texture = arcade.load_texture("images/cards/time_card.jpg")

        # Используем игрока
        self.battle_player = self.player
        self.battle_player.reset_battle_stats()

        # Создаем врага
        enemy_level = self.enemy_sprite.level
        enemy_name = self.enemy_sprite.name
        enemy_type = self.enemy_sprite.enemy_type

        self.battle_enemy = Enemy(
            name=enemy_name,
            level=enemy_level,
            enemy_center_x=self.ENEMY_CENTER_X,
            enemy_center_y=self.ENEMY_CENTER_Y,
            enemy_radius=60,
            enemy_type=enemy_type)

        if hasattr(self.battle_enemy, 'create_text_object'):
            self.battle_enemy.create_text_object()
        # Сохраняем опыт
        if enemy_type == "necromancer":
            self.enemy_exp_value = self.enemy_sprite.exp_value * 3
        elif enemy_type == "skeleton":
            self.enemy_exp_value = self.enemy_sprite.exp_value * 2
        else:
            self.enemy_exp_value = self.enemy_sprite.exp_value
        self.deck_spritelist = arcade.SpriteList()
        self.deck_sprite = arcade.Sprite(self.deck_texture)

        self.deck_sprite.width = self.ACTUAL_CARD_WIDTH
        self.deck_sprite.height = self.ACTUAL_CARD_HEIGHT
        self.deck_sprite.center_x = self.DECK_X
        self.deck_sprite.center_y = self.DECK_Y
        self.deck_spritelist.append(self.deck_sprite)

        # Инициализируем руку
        self.draw_new_hand()
        self.position_cards()

        # Настройка состояния битвы
        self.battle_timer = 0
        self.battle_turn = "player"

        # Создаем текстовые объекты
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
        """Оптимизированное создание руки"""
        if not self.battle_player:
            return

        # Очищаем старые спрайты
        if hasattr(self.battle_player, 'hand_sprites'):
            self.battle_player.hand_sprites.clear()

        if hasattr(self.battle_player, 'hand'):
            self.battle_player.hand.clear()

        self.battle_player.has_shield_reflection = False

        # Создаем карты
        for _ in range(6):
            self.battle_player.add_random_card()

    def position_cards(self):
        """Оптимизированное позиционирование карт"""
        if not self.battle_player or not hasattr(self.battle_player, 'hand'):
            return

        total_cards = len(self.battle_player.hand)
        if total_cards == 0:
            return

        # Вычисляем позиции
        distance_between_centers = self.ACTUAL_CARD_WIDTH + self.CARD_MARGIN
        group_center_x = self.SCREEN_WIDTH // 2

        if total_cards % 2 == 0:
            first_card_offset = -((total_cards / 2) - 0.5) * distance_between_centers
        else:
            first_card_offset = -((total_cards - 1) / 2) * distance_between_centers

        # Устанавливаем позиции
        for i, card in enumerate(self.battle_player.hand):
            if hasattr(card, 'sprite') and card.sprite:
                card.sprite.width = self.ACTUAL_CARD_WIDTH
                card.sprite.height = self.ACTUAL_CARD_HEIGHT
                card_center_x = group_center_x + first_card_offset + (i * distance_between_centers)
                card.sprite.center_x = card_center_x
                card.sprite.center_y = self.HAND_Y

    def enemy_attack(self):
        """Упрощенная атака врага"""
        if not self.battle_player or not self.battle_enemy:
            return False

        damage = self.battle_enemy.get_attack()

        if self.battle_player.has_shield_reflection:
            self.battle_player.has_shield_reflection = False
            self.battle_enemy.take_damage(damage)

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
        """Оптимизированный розыгрыш карты"""
        if not self.battle_player or not self.battle_enemy:
            return

        # Находим карту
        card_to_play = None
        for c in self.battle_player.hand:
            if c.suit == card.suit and c.value == card.value:
                card_to_play = c
                break

        if not card_to_play:
            return

        # Обрабатываем карту
        if card_to_play.suit == 'sword':
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
            potion_effect = self.battle_player.play_potion_card(
                card_to_play.value,
                self.battle_player.level)

            # Сообщение о зелье
            self.potion_effect_text = arcade.Text(
                potion_effect,
                self.SCREEN_WIDTH // 2,
                self.SCREEN_HEIGHT - 110,
                arcade.color.CYAN,
                20,
                anchor_x="center")
            self.potion_message_timer = 2.0

        # Удаляем карту
        self.battle_player.remove_card_from_hand(card_to_play)

        # Проверяем победу
        if self.battle_enemy.current_hp <= 0:
            exp_gained = self.enemy_exp_value
            new_exp, levels_gained = self.battle_player.add_experience(exp_gained)
            self.gained_experience = exp_gained
            self.levels_gained = levels_gained
            self.game_state = "win"
            return

        # Переход хода
        self.battle_turn = "enemy"
        self.battle_timer = 0

        # Обновляем позиции
        self.position_cards()

        # Если рука пуста - новая рука
        if len(self.battle_player.hand) == 0:
            self.draw_new_hand()
            self.position_cards()

    def on_draw(self):
        """Оптимизированная отрисовка"""
        self.clear()

        if self.game_state == "battle":
            self.draw_battle()
        elif self.game_state == "win":
            self.draw_battle_win()
        elif self.game_state == "lose":
            self.draw_battle_lose()

    def draw_battle(self):
        if self.background_texture:
            arcade.draw_texture_rect(self.background_texture, arcade.rect.XYWH(
                self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2,
                self.SCREEN_WIDTH, self.SCREEN_HEIGHT))

        # Враг
        if self.battle_enemy:
            self.battle_enemy.draw()

        # Колода
        if self.deck_spritelist:
            self.deck_spritelist.draw()
            self.deck_text.draw()
        if self.battle_player and len(self.battle_player.hand) >= 6:
            self.deck_warning_text.value = "Полная рука!"
            self.deck_warning_text.draw()

        # Карты в руке
        if hasattr(self.battle_player, 'hand_sprites'):
            self.battle_player.hand_sprites.draw()

        # Желтые частицы (поверх всего)
        for emitter in self.click_emitters:
            emitter.draw()

        # Эффекты зелий
        if (hasattr(self.battle_player, 'damage_multiplier_turns') and
                self.battle_player.damage_multiplier_turns > 0):
            multiplier_text = arcade.Text(
                f"Урон x{self.battle_player.damage_multiplier:.1f} ({self.battle_player.damage_multiplier_turns} ход.)",
                50, self.SCREEN_HEIGHT - 120,
                arcade.color.WHITE, 16)
            multiplier_text.draw()

        if hasattr(self, 'potion_effect_text') and self.potion_message_timer > 0:
            self.potion_effect_text.draw()

        # Текстовая информация
        if self.battle_player:
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
        """Отрисовка экрана победы"""
        arcade.set_background_color(arcade.color.BLACK)
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
        """Отрисовка экрана поражения"""
        arcade.set_background_color(arcade.color.BLACK)
        self.lose_text.draw()

        # Карта времени (используем кэшированную текстуру)
        time_card_spritelist = arcade.SpriteList()
        if self.time_card_texture:
            time_card = arcade.Sprite(self.time_card_texture)
        else:
            time_card = arcade.SpriteSolidColor(
                self.ACTUAL_CARD_WIDTH * 2,
                self.ACTUAL_CARD_HEIGHT * 2,
                arcade.color.BLUE
            )

        time_card.width = self.ACTUAL_CARD_WIDTH * 2
        time_card.height = self.ACTUAL_CARD_HEIGHT * 2
        time_card.center_x = self.SCREEN_WIDTH // 2
        time_card.center_y = self.SCREEN_HEIGHT // 2
        time_card_spritelist.append(time_card)
        time_card_spritelist.draw()

        self.return_text.value = "Нет, я не погибну здесь!.."
        self.return_text.draw()

    def on_update(self, delta_time):
        """Обновление состояния"""
        if self.game_state == "battle":
            self.update_battle(delta_time)

    def update_battle(self, delta_time):
        """Обновление битвы"""
        # Ход врага
        if self.battle_turn == "enemy":
            self.battle_timer += delta_time
            if self.battle_timer >= 1.0:
                self.enemy_attack()
                self.battle_timer = 0
                self.battle_turn = "player"

        # Таймер сообщения о зелье
        if hasattr(self, 'potion_message_timer'):
            self.potion_message_timer -= delta_time
            if self.potion_message_timer <= 0:
                self.potion_message_timer = 0

        # Эффекты зелий
        if self.battle_player:
            self.battle_player.apply_potion_effects(delta_time)

        # Обновляем эмиттеры частиц
        emitters_to_remove = []
        for emitter in self.click_emitters:
            emitter.update(delta_time)
            if emitter.can_reap():
                emitters_to_remove.append(emitter)

        # Удаляем завершенные эмиттеры
        for emitter in emitters_to_remove:
            self.click_emitters.remove(emitter)

    def on_key_press(self, key, modifiers):
        """Обработка нажатий клавиш"""
        if key == arcade.key.ESCAPE:
            if self.game_state == "lose":
                arcade.close_window()
            elif self.game_state == "battle":
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
        """Нажатия клавиш в битве"""
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
        """Нажатия клавиш при победе"""
        if key == arcade.key.SPACE:
            self.cleanup_sprites()
            if self.db and self.player:
                self.player.save_to_db(self.db)
            if self.return_callback:
                self.return_callback(self.player, enemy_defeated=True, enemy_exp_value=self.enemy_exp_value)

    def on_mouse_press(self, x, y, button, modifiers):
        """Обработка кликов мыши"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            # Создаем желтые частицы при ЛЮБОМ клике в режиме битвы
            if self.game_state == "battle":
                emitter = self.create_yellow_particles(x, y)
                self.click_emitters.append(emitter)

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
                    self.cleanup_sprites()
                    self.player.current_hp = self.player.max_hp
                    self.return_callback(self.player, enemy_defeated=False, respawn=True)
            return

        if self.game_state != "battle":
            return

        # Клик по колоде
        if self.deck_spritelist:
            clicked_deck = arcade.get_sprites_at_point((x, y), self.deck_spritelist)
            if clicked_deck:
                if self.battle_player and len(self.battle_player.hand) < 6:
                    if self.battle_player.add_random_card():
                        self.position_cards()
                return

        if self.battle_turn != "player":
            return

        # Клик по картам
        if hasattr(self.battle_player, 'hand'):
            for i in range(len(self.battle_player.hand) - 1, -1, -1):
                card = self.battle_player.hand[i]
                if hasattr(card, 'sprite') and card.sprite:
                    sprite = card.sprite
                    left = sprite.center_x - self.ACTUAL_CARD_WIDTH / 2
                    right = sprite.center_x + self.ACTUAL_CARD_WIDTH / 2
                    bottom = sprite.center_y - self.ACTUAL_CARD_HEIGHT / 2
                    top = sprite.center_y + self.ACTUAL_CARD_HEIGHT / 2

                    if left <= x <= right and bottom <= y <= top:
                        if hasattr(self.battle_player, 'selected_card'):
                            self.battle_player.selected_card = card
                        self.play_card(card)
                        break