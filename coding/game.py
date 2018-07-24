import random
from itertools import product
from typing import NamedTuple, List, Dict, Set, Tuple

import coding.commands

from coding.commands import BaseCommand, CommandEnd, CommandNoOp
from coding.exceptions import EndProgram, InvalidPlayException
from coding.player import Player

COLORS = ['WHITE', 'BLACK', 'RED', 'BLUE']
RESOURCES = ['N/A', 'CPU', 'RAM', 'VP']
VARIABLES = ['A%', 'B%', 'C%', 'D%']
COLOR_MAP = {(i // 2, i % 2): c for i, c in enumerate(COLORS)}
RESOURCE_MAP = {(i // 2, i % 2): r for i, r in enumerate(RESOURCES)}
VARIABLE_MAP = {v: i for i, v in enumerate(VARIABLES)}


class Tile:
    _id = 0

    def __init__(self, var: str):
        self.var: str = var
        self.var_id: int = VARIABLE_MAP[var]
        self.id: int = self._make_id()

    @classmethod
    def _make_id(cls):
        cls._id += 1
        return cls._id

    def __repr__(self):
        return self.var


class ProgramLine:
    def __init__(self, command: BaseCommand, tile: Tile, line_no: int):
        self.command: BaseCommand = command
        self.tile: Tile = tile
        self.line_no: int = line_no

    def __repr__(self):
        return f"{self.line_no:3} {self.command} --> {self.tile}"


class Game:
    max_players = len(COLORS)

    def __init__(self, commands: Dict, lines: int=12, rounds: int=5,
                 variable_copies: int=4, tile_hand_size: int=4,
                 command_hand_extra: int=2):
        self.lines: int = lines
        self.rounds: int = rounds
        self.variable_copies: int = variable_copies
        self.tile_hand_size: int = tile_hand_size
        self.extra_hand_size: int = command_hand_extra
        self.commands: Dict = commands
        self.command_states: Dict = {
            k: i for i, k in enumerate(sorted({
                (cmd['class'], cmd['value'])
                for cmd in commands['commands']
            }))
        }
        self.command_states_length: int = len(self.command_states)

        self.program_lines: List[int] = [
            i * 10 for i in range(1, self.lines + 1)]

        self._deck: List[BaseCommand] = []
        self._tiles: List[Tile] = []

        self.players: Dict[str, Player] = {}
        self.deck: List[BaseCommand] = []
        self.tiles: List[Tile] = []

        self.program: Dict[int, ProgramLine] = {}
        self.var: Dict = {}
        self.reg: List = []

        self.current_round: int = 0
        self.current_line: int = 0
        self.first_player: str = None
        self.goto_line: int = None
        self.current_player_index: int = None

        self.running = False

    @property
    def ml_state(self):
        program_cmd_state = [0] * self.command_states_length * self.lines
        program_tile_state = [0] * self.lines * len(VARIABLES)

        for i, num in enumerate(self.program_lines):
            if num in self.program:
                line = self.program[num]
                program_cmd_state[
                    self.command_states[
                        (line.command.cmd, line.command.value)
                    ] + (i * self.command_states_length)
                ] = 1
                program_tile_state[
                    line.tile.var_id + (i * len(VARIABLES))
                ] = 1

        state = program_cmd_state + program_tile_state

        for i in range(self.max_players):
            # index is from the perspective of the current player
            c = COLORS[(self.current_player_index + i) % 4]
            p = self.players[c]
            for r in RESOURCES:
                state.append(p.resources[r])
            state.append(len(p.hand))
            state.append(len(p.tiles))

            # indicate color
            state.extend([
                1 if i == j else 0 for j in range(self.max_players)])

        return state

    @property
    def register_resource(self):
        return RESOURCE_MAP[(self.reg[0], self.reg[1])]

    @property
    def register_color(self):
        return COLOR_MAP[(self.reg[2], self.reg[3])]

    @property
    def available_lines(self):
        lines = [
            line for line in self.program_lines
            if line not in self.program
        ]
        return lines

    def list_code(self):
        lines = sorted(list(self.program.keys()))
        return [self.program[num] for num in lines]

    def create_deck(self):
        self._deck.clear()
        for card in self.commands['commands']:
            cls = getattr(coding.commands, card['class'])
            for i in range(card['copies']):
                self._deck.append(cls(self, card['value']))

    def shuffle_deck(self) -> List:
        deck = random.sample(self._deck, len(self._deck))

        # Remove cards still in players hands
        return [
            command for command in deck
            if not any(
                [command in player.hand
                    for player in self.players.values()]
            )
        ]

    def draw_from_deck(self):
        if not self.deck:
            self.deck = self.shuffle_deck()

        return self.deck.pop()

    def create_tiles(self):
        self._tiles = [
            Tile(var)
            for var, _ in product(VARIABLES, range(self.variable_copies))
        ]

    def shuffle_tiles(self) -> List:
        deck = random.sample(self._tiles, len(self._tiles))

        # Ignore tiles still in players hands
        return [
            tile for tile in deck
            if not any(
                [tile in player.tiles
                    for player in self.players.values()]
            )
        ]

    def draw_from_tiles(self):
        if not self.tiles:
            self.tiles = self.shuffle_tiles()

        return self.tiles.pop()

    def initialize_game(self, players: List):
        self.create_deck()
        self.create_tiles()

        self.deck = self.shuffle_deck()
        self.tiles = self.shuffle_tiles()

        for color, name in zip(COLORS, players):
            self.players[color] = Player(self, color, name)

        player_string = ', '.join([str(p) for p in self.players.values()])
        print(f"Starting new game with {player_string}")

        self.set_first_player(random.choice(list(self.players.keys())))
        self.running = True
        self.clear()

    def initialize_round(self, round_num: int):
        print(f'Starting round {round_num}')
        self.current_round = round_num
        base_hand_size = \
            self.lines // len(self.players) + self.extra_hand_size

        for player in self.players.values():
            ram = player.resources['ram']
            hand_size = base_hand_size + ram
            cards_dealt = hand_size - len(player.hand)
            while len(player.hand) < hand_size:
                player.hand.append(self.draw_from_deck())
            print(f'{player} dealt {cards_dealt - ram} commands plus '
                  f'{ram} bonus commands from RAM')
            player.resources['ram'] = 0

        self.reset_program()

    def run_game(self, players: List):
        self.initialize_game(players)

        for round_num in range(1, self.rounds + 1):
            generator = self.run_round(round_num)

            choices = generator.send(None)
            while True:
                response = yield choices
                try:
                    choices = generator.send(response)
                except StopIteration:
                    break

        self.end_game()

        return

    def run_round(self, round_num: int):
        self.initialize_round(round_num)

        self.current_player_index = [
            i for i, c in enumerate(COLORS) if c == self.first_player
        ][0]

        while self.available_lines:
            player = self.players.get(COLORS[self.current_player_index])

            if player and player.hand:
                if not player.tiles:
                    player.tiles = [
                        self.draw_from_tiles()
                        for _ in range(self.tile_hand_size)]

                while True:
                    response = yield self.gather_options(player)
                    line, command, tile = response

                    try:
                        player.play_command(line, command, tile)
                        break
                    except InvalidPlayException:
                        pass

            self.current_player_index = (self.current_player_index + 1) % 4

        self.current_player_index = None
        self.run_program()
        self.end_round()
        print(f'End round {round_num}')
        return

    def gather_options(self, player: Player) -> List[tuple]:
        choices = []
        for command in player.hand:
            allowed_lines = command.allowed_lines(self.available_lines)
            allowed_vars = command.allowed_variables(player.tiles)

            choices.append(
                (command, allowed_lines, allowed_vars)
            )

        return choices

    def run_program(self):
        print('RUN')
        self.current_line = 10

        while self.current_line:
            if self.current_line in self.program:
                line = self.program[self.current_line]
                print(line)

                try:
                    line.command.action(line.tile.var)
                except EndProgram:
                    break

            if self.goto_line:
                print(f"\tContinuing execution from line {line}")
                self.current_line = self.goto_line
                self.goto_line = None
            else:
                self.current_line = min([
                    line_num for line_num in self.program.keys()
                    if line_num > self.current_line
                ])

    def end_round(self):
        pass

    def end_game(self):
        best_score = 0
        for color, player in self.players.items():
            vp = player.resources['VP']
            print(f"{player}: {vp} VP")
            if vp > best_score:
                best_score = vp

        winners = []
        for color, player in self.players.items():
            vp = player.resources['VP']
            if vp == best_score:
                winners.append(str(player))

        print(f"{' & '.join(winners)} is the winner!")
        self.running = False

    def enter_command(self, color: str, line: int, command: BaseCommand,
                      tile: Tile):

        self.program[line] = ProgramLine(command, tile, line)
        print(f'{self.players[color]} added\n    {self.program[line]}')

    def reset_program(self):
        print(f'DELETE {min(self.program_lines)}-{max(self.program_lines)}')
        print(f'AUTO {min(self.program_lines)}, 10')
        print(f'999     END')

        self.program = {
            999: ProgramLine(CommandEnd(self, None), Tile(''), 999)
        }

    def clear(self):
        print('CLEAR')
        for v in VARIABLES:
            print(f"LET {v} = 0")
            self.var[v] = 0

        print(f"DIM R(3)")
        self.reg = [0, 0, 0, 0]

    def send(self, var: str):
        resource = self.register_resource
        color = self.register_color
        value = self.var[var]
        print(f'\t{color}.{resource} += {value}')

        player = self.players.get(color)
        if not player:
            return

        if resource not in ['N/A']:
            player.resources[resource] += value

        if resource in ['CPU']:
            if self.first_player is None or (
                    self.first_player != color and
                    self.players[color].resources['CPU'] >
                    self.players[self.first_player].resources['CPU']):

                self.set_first_player(color)

    def set_first_player(self, color: str):
        self.first_player = color
        print(f'\t{self.players[color]} is now first player')

    def jump_to_line(self, line: int):
        self.goto_line = line

    def delete_line(self, num: int):
        command = self.program[num].command
        self.program[num].command = CommandNoOp(self)
        print(f"\tDeleted {command} on line {num}")

    def change_var(self, var: str, value: int):
        self.set_var(var, self.var[var] + value)

    def set_var(self, var: str, value: int):
        old_val = self.var[var]
        self.var[var] = int(value) % 4
        new_val = self.var[var]

        if old_val != new_val:
            print(f'\t{var} changed from {old_val} to {new_val}')

    def set_register(self, reg: int, value: int):
        old_val = self.reg[reg]
        self.reg[reg] = value % 2
        new_val = self.reg[reg]

        if old_val != new_val:
            print(f'\tR[{reg}] flipped from {old_val} to {new_val}')
