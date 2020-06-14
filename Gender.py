from enum import Enum


class Gender(Enum):
    MALE = 0
    FEMALE = 1

    def __str__(self):
        return "M" if self.value == 0 else "F"
