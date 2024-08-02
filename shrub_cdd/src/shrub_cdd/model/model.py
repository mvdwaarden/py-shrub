EDGE_ATTRIBUTE_WEIGHT = "weight"


class Node:
    def __init__(self, id: int):
        self.id: int = id
        self.initializer = None
        self.attribute = None
        self.value = None
        self.values = []

    def __hash__(self):
        return self.id

    def __str__(self):
        return str(self.id)
