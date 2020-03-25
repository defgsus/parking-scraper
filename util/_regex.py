import re


class RegexFilter:

    def __init__(self, *regex):
        self.expressions = []
        for r in regex:
            if isinstance(r, str):
                r = re.compile(r)
            self.expressions.append(r)

    def matches(self, text):
        for r in self.expressions:
            for i in r.finditer(text):
                return True
        return False
