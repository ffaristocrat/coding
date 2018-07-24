class GameException(Exception):
    pass


class GameFlowException(GameException):
    pass


class EndProgram(GameFlowException):
    pass


class InvalidPlayException(GameException):
    pass
