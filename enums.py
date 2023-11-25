from enum import Enum


class Mark(Enum):
    good = 0, 1, 0
    middle = 1, 1, 0
    bad = 1, 0, 0
    nothing = 1, 1, 1
