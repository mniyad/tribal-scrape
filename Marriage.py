from DateEvent import DateEvent
from Person import Person


class Marriage:

    def __init__(self, married: DateEvent, husband: Person, wife: Person):
        self.married = married
        self.husband = husband
        self.wife = wife
        self.divorced: DateEvent
