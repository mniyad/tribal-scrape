from DateEvent import DateEvent
from Husband import Husband
from Wife import Wife


class Marriage:

    def __init__(self, married: DateEvent, husband: Husband, wife: Wife):
        self.married = married
        self.husband = husband
        self.wife = wife
        self.divorced: DateEvent
