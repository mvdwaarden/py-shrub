from typing import List
import os
import os.path
import pathlib
from shrub_archi.model.model import ElementType
import uuid


class Generator:
    def __init__(self, separator=','):
        self.separator = separator

    def cleanup(self) -> "Generator":
        for filename in [self.get_elements_filename(), self.get_relations_filename(), self.get_properties_filename()]:
            if os.path.exists(filename):
                os.remove(filename)
        return self

    def _get_filename(self, filename) -> str:
        return os.path.join(pathlib.Path.home(), filename)

    def write_elements_csv(self, data: List[List], element_type: ElementType):
        with open(self.get_elements_filename(), "w") as ofp:
            ofp.write(f"{self.separator}".join(["ID","Type","Name","Documentation","Specialization"]))
            ofp.write("\n")
            for row in data:
                ofp.write(f"{self._escape(self.generate_id())}{self.separator}")
                ofp.write(f"{self._escape(element_type.value)}{self.separator}")
                for col in row:
                    ofp.write(f'{self._escape(col)}{self.separator}')
                ofp.write("\n")

    def get_elements_filename(self):
        return self._get_filename("elements.csv")

    def get_relations_filename(self):
        return self._get_filename("relations.csv")

    def get_properties_filename(self):
        return self._get_filename("properties.csv")

    def generate_id(self) -> str:
        return f"id-{uuid.uuid4()}"

    def _escape(self, data) -> str:
        return f'"{data}"'
