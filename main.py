import random
from typing import List, Tuple

import json

from coding.game import Game

players = [
    'Micheál',
    'Melissa',
]


def get_input(choices: List[Tuple]):
    all_tiles = set()
    all_commands = set()
    all_lines = set()
    for command, lines, tiles in choices:
        all_lines |= set(lines)
        all_commands.add(command)
        all_tiles |= set(tiles)
        # tile_list = ', '.join([f'{t.var} ({t.id})' for t in tiles])
        #
        # print(f"{command} ({command.id})")
        #       f"    lines: {str(lines)[1:-1]}\n"
        #       f"    tiles: {tile_list}")

    print(str(all_lines)[1:-1])
    print(', '.join([f"{c[0]} ({c[0].id})" for c in choices]))
    print(', '.join([f'{t.var} ({t.id})' for t in all_tiles]))

    while True:
        line = int(input('line: '))
        cmd_id = int(input('command: '))
        tile_id = int(input('tile: '))

        try:
            command = [c for c in all_commands if c.id == cmd_id][0]
            tile = [t for t in all_tiles if t.id == tile_id][0]
            break
        except (IndexError, ValueError):
            pass

    return line, command, tile


def random_choice(choices: List[Tuple]):

    choice = random.choice(choices)

    command = choice[0]
    line = random.choice(choice[1])
    tile = random.choice(choice[2])

    # print(f'Choice: {line:3} {command} --> {tile}')

    return line, command, tile


def main():

    commands = json.load(open('commands.json'))
    game = Game(commands)

    generator = game.run_game(players)
    choices = generator.send(None)

    while choices:
        # for line in game.list_code():
        #     print(line)

        response = random_choice(choices)
        try:
            choices = generator.send(response)
        except StopIteration:
            break


if __name__ == "__main__":
    main()
