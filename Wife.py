from Gender import Gender
from Person import Person


class Wife(Person):

    def __init__(self, node):
        super(Wife, self).__init__(node)
        self.husband: Person
        self.gender = Gender.FEMALE
