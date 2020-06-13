from typing import List

from DateEvent import DateEvent
from Gender import Gender
import Marriage


class Person:

    def __init__(self, node):
        self.born: DateEvent
        self.mother: Person
        self.father: Person
        self.gender: Gender
        self.first_name = ""
        self.middle_name = ""
        self.last_name = ""
        self.died: DateEvent
        marriages: List[Marriage.Marriage]
        self.parse(node)

    @classmethod
    def parse(cls, node):
        rows = node.xpath("tr")
        cls.first_name = rows[0].xpath("//td[position()=2]/b/text()")[0]
        for row in rows:
            cells = row.xpath("td")
            cell_text = cells[0].text
            if cell_text is not None and cell_text.strip() == "Born":
                cls.born = DateEvent(cells)

    @property
    def name(self):
        return self.first_name + " " + self.last_name

    @classmethod
    def set_dob(cls, born: DateEvent):
        cls.born = born

    @classmethod
    def married(cls, marriage: Marriage):
        cls.marriages.append(marriage)
