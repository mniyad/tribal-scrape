from typing import List

from Gender import Gender
from Person import Person


class Children(List[Person]):
    def __init__(self, node):
        super().__init__()
        self.parse(node)

    def parse(self, node):
        children = node.xpath("tr[position() > 1]")
        for child in children:
            new_child = child.xpath("td/table")
            if new_child is not None and len(new_child) > 0:
                name = child.xpath("td[position()=2]/b")[0].text.strip()
                child_person = Person(child, name)
                gender = new_child[0].xpath("tr/td[position()=2]")[0].text
                child_person.gender = Gender.MALE if gender == "M" else Gender.FEMALE
                self.append(child_person)
