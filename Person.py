import json
from typing import List

from DateEvent import DateEvent
from Gender import Gender


class Person:

    def __init__(self, node, name: str):
        self.born: DateEvent = None
        self.mother: Person
        self.father: Person
        self.gender: Gender = None
        self.name = name
        self.died: DateEvent
        self.parse(node)

    def parse(self, node):
        rows = node.xpath("tr")
        if self.name is None:
            self.name = str(rows[0].xpath("td[position()=2]/b/text()")[0]).strip()
        for row in rows:
            self.person_info(row)

    def person_info(self, row):
        cells = row.xpath("td")
        cell_text = cells[0].text
        if cell_text is not None and cell_text.strip() == "Born":
            self.born = DateEvent(cells)

    def set_gender(self, value: Gender):
        self.gender = value
