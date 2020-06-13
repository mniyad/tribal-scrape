from lxml import html
import requests
from typing import Dict

from Husband import Husband
from Marriage import Marriage
from Person import Person
from Wife import Wife


def trim(string: str):
    return string.replace('\xa0', '')


class TribalScraper:
    url_template = r'https://saikura.tribalpages.com/tribe/browse?userid=saikura&view=77&reporttype=4&pid='
    people: Dict[str, Person]
    wives: Dict[str, Marriage]
    husbands: Dict[str, Marriage]

    def __init__(self):
        self.start = 1

    @staticmethod
    def parse(pid: int):
        url = TribalScraper.url_template + str(pid)
        page = requests.get(url)
        tree = html.fromstring(page.content)
        tables = tree.xpath(".//table[@border=1]")
        for table in tables:
            name = trim(table.xpath("tr/td[position()=1]/b/text()")[0])
            if name == "Wife":
                w = Wife(table)
                TribalScraper.people[w.name] = w

            if name == "Husband":
                h = Husband(table)
                TribalScraper.people[h.name] = h

            if name == "Children":
                c = Children(table)



def main():
    scraper = TribalScraper()
    scraper.parse(58)


if __name__ == "__main__":
    # execute only if run as a script
    main()
