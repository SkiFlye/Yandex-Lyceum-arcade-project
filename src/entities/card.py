import arcade
from dataclasses import dataclass


@dataclass
class Card:
    """Класс карты"""
    suit: str
    value: int
    actual_card_width: int = 0
    actual_card_height: int = 0

    def __post_init__(self):
        self.sprite = arcade.Sprite(f"images/cards/{self.suit}_{self.value}.jpg")
        if self.actual_card_width > 0 and self.actual_card_height > 0:
            self.sprite.width = self.actual_card_width
            self.sprite.height = self.actual_card_height

    def is_valid_value(self):
        if self.suit == 'shield':
            return 2 <= self.value <= 6
        else:
            return 2 <= self.value <= 10

    def get_effect_power(self, player_level=1, base_damage_per_level=0.2, base_block_per_level=0.15):
        multipliers = {
            'sword': 1.0,
            'shield': 1.0,}
        base_power = self.value * multipliers[self.suit]
        # Увеличение эффекта карт с увеличением уровня
        if self.suit == 'sword':
            level_multiplier = 1.0 + (player_level - 1) * base_damage_per_level
        elif self.suit == 'shield':
            level_multiplier = 1.0 + (player_level - 1) * base_block_per_level
        else:
            level_multiplier = 1.0
        return int(base_power * level_multiplier)