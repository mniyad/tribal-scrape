class DateEvent:
    def __init__(self, node):
        self.location: str = ''
        self.date: str = ''
        self.parse(node)

    def parse(self, node):
        self.date = node[1].text.strip() if node[1].text is not None else ""
        self.location = node[2].text.strip() if node[2].text is not None else ""
