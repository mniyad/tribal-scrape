import json

from Children import Children
from Person import Person


class FamilyGroup:

    def __init__(self):
        self.wife: Person = None
        self.husband: Person = None
        self.children: Children = None

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)
