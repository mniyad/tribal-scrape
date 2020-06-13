from Children import Children
from Husband import Husband
from TribalScraper import TribalScraper
from Wife import Wife


class FamilyGroup:

    def __init__(self, node):
        self.wife: Wife
        self.husband: Husband
        self.children: Children
        self.parse(node)

    @classmethod
    def parse(cls, node):
        pass
