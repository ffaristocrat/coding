from typing import List
from coding.exceptions import EndProgram


class BaseCommand:
    _id = 0
    cmd = 'TEST'

    def __init__(self, game, value: str=None):
        self.game = game
        self.value = value
        self.id = self._make_id()

    def _make_id(self):
        BaseCommand._id += 1
        return BaseCommand._id

    def __repr__(self):
        return f'{self.cmd}'

    def action(self, target):
        raise NotImplementedError

    def allowed_lines(self, lines: List[int]):
        return lines

    def allowed_variables(self, targets: List[str]):
        return targets

    def self_destruct(self):
        line = [l for l, c in self.game.program.items() if c.command == self][0]
        self.game.delete_line(line)


class CommandWithValue(BaseCommand):
    def __repr__(self):
        return f'{self.cmd} {self.value}'


class CommandNoOp(BaseCommand):
    cmd = 'NOOP'

    def action(self, target):
        pass


class CommandEnd(BaseCommand):
    cmd = 'END'

    def action(self, target: str):
        raise EndProgram
        pass


class CommandGoto(CommandWithValue):
    cmd = 'GOTO'

    def action(self, target: str):
        self.game.jump_to_line(int(self.value))
        self.self_destruct()


class CommandClear(BaseCommand):
    cmd = 'CLEAR'

    def action(self, target: str):
        self.game.clear()


class CommandCopy(CommandWithValue):
    cmd = 'COPY'

    def action(self, target: str):
        self.game.set_var(target, self.game.var[self.value])


class CommandIncrement(BaseCommand):
    cmd = 'INCR'

    def action(self, target: str):
        self.game.change_var(target, 1)


class CommandDecrement(BaseCommand):
    cmd = 'DECR'

    def action(self, target: str):
        self.game.change_var(target, -1)


class CommandAdd(CommandWithValue):
    cmd = 'ADD'

    def action(self, target: str):
        self.game.change_var(target, self.game.var[self.value])


class CommandSubtract(CommandWithValue):
    cmd = 'SUB'

    def action(self, target: str):
        self.game.change_var(target, self.game.var[self.value])


class CommandLet(CommandWithValue):
    cmd = 'LET'

    def action(self, target: str):
        self.game.set_var(target, int(self.value))

    def __repr__(self):
        return f'LET = {self.value}'


class CommandToggle(CommandWithValue):
    cmd = 'TOGL'

    def action(self, target: str):
        self.game.set_register(
            int(self.value),
            1 - self.game.reg[int(self.value)]
        )

    def __repr__(self):
        return f'TOGL R[{self.value}]'


class CommandToggleViaVar(BaseCommand):
    cmd = 'TOGL R[ ]'

    def action(self, target: str):
        register = self.game.var[target]
        self.game.set_register(register, 1 - self.game.reg[register])


class CommandSend(BaseCommand):
    cmd = 'SEND'

    def action(self, target: str):
        self.game.send(target)


class CommandDelete(CommandWithValue):
    cmd = 'DELETE'

    def action(self, target: str):
        self.game.delete_line(int(self.value))
        self.self_destruct()

    def allowed_lines(self, lines: List[int]):
        return [line for line in lines if line != int(self.value)]

