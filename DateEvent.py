class DateEvent:
    def __init__(self, node):
        self.location: str
        self.date: str
        self.parse(node)

    @classmethod
    def parse(cls, node):
        cls.date = node[2].text.strip() if node[2].text is not None else ""
        cls.location = node[3].text.strip() if node[3].text is not None else ""
