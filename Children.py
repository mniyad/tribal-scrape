from typing import List

from Person import Person
from TribalScraper import TribalScraper


class Children(List[Person]):
    def __init__(self, node):
        super().__init__()
        self.parse(node)

    @classmethod
    def parse(cls, node):
        pass

