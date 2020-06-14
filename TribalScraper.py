from xml import etree

from lxml import html
import requests
from typing import Dict, List

from Children import Children
from FamilyGroup import FamilyGroup
from Gender import Gender
from Marriage import Marriage
from Person import Person


def trim(string: str):
    return string.replace('\xa0', '')


class TribalScraper:
    url_template = r'https://saikura.tribalpages.com/tribe/browse?userid=saikura&view=77&reporttype=4&pid='
    people: Dict[str, Person]
    wives: Dict[str, Marriage]
    husbands: Dict[str, Marriage]

    def __init__(self):
        self.start = 1
        self.family_groups: List[FamilyGroup] = []

    def parse(self, pid: int):
        url = TribalScraper.url_template + str(pid)
        page = requests.get(url)
        tree = html.fromstring(page.content)
        rows = tree.xpath("/html/body/center/table/tr/td")
        for row in rows:
            create_new = row.xpath("b")
            tables = row.xpath("table")
            if len(create_new) > 0:
                family_group: FamilyGroup = FamilyGroup()
                self.family_groups.append(family_group)
            elif len(tables) > 0:
                table = tables[0]
                name = trim(table.xpath("tr/td[position()=1]/b/text()")[0])
                if name == "Wife":
                    w = Person(table, None)
                    w.gender = Gender.FEMALE
                    family_group.wife = w

                if name == "Husband":
                    h = Person(table, None)
                    h.gender = Gender.MALE
                    family_group.husband = h

                if name == "Children":
                    c = Children(table)
                    family_group.children = c


def main():
    scraper = TribalScraper()
    scraper.parse(34)


if __name__ == "__main__":
    # execute only if run as a script
    main()
