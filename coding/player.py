from typing import List
from collections import defaultdict

from coding.commands import BaseCommand
from coding.exceptions import InvalidPlayException


class Player:
    def __init__(self, game, color: str, name: str=None):
        self.game = game
        self.color = color
        self.name = name or color
        self.hand: List[BaseCommand] = []
        self.tiles: List[str] = []

        self.resources = defaultdict(int)

    def __repr__(self):
        if self.name:
            return f"{self.name} ({self.color})"
        return self.color

    def play_command(self, line, command, tile):
        if tile not in self.tiles:
            raise InvalidPlayException(f'{tile} not in hand')
        if command not in self.hand:
            raise InvalidPlayException(f'{command} not in hand')
        if line not in self.game.available_lines:
            raise InvalidPlayException(f'{line} not available')

        for i in range(len(self.tiles)):
            if self.tiles[i] == tile:
                self.tiles.pop(i)
                break

        for i in range(len(self.hand)):
            if self.hand[i] == command:
                self.hand.pop(i)
                break

        self.game.enter_command(self.color, line, command, tile)

    def draw_tile(self):
        self.tiles.append(self.game.draw_from_tiles())

    def draw_card(self):
        self.hand.append(self.game.draw_from_deck())


