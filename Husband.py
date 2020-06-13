from Gender import Gender
from Person import Person


class Husband(Person):
    wife: Person

    def __init__(self, node):
        super(Husband, self).__init__(node)
        self.husband: Person
        self.gender = Gender.MALE
