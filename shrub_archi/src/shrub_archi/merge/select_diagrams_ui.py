from typing import List, Optional, Dict

from shrub_archi.merge.identity import Identity
from .identity_resolver import ResolvedIdentity
from .select_ui import SelectModel, do_show_select_ui


class ViewTableModel(SelectModel):
    COL_COUNT: int = 6
    HEADER_LABELS: List[str] = ['Select', 'ID', 'Classification', 'Name', 'Description',
                                'Source']

    def __init__(self, data: List[ResolvedIdentity]):
        super().__init__(data=data)

    def get_column_value_for(self, row: Identity, column: int):
        match column:
            case 0:
                return ''  # Checkbox column
            case 1:
                return row.unique_id
            case 2:
                return row.classification
            case 3:
                return row.name
            case 4:
                return row.description
            case 5:
                return row.source
            case _:
                return "?"

    def hit_row(self, row: Identity, search_text: str):
        def hit_identity(identity):
            return (identity.name and search_text in identity.name.lower()) or (
                    identity.description and search_text in identity.description.lower()) or (
                    identity.classification and search_text in identity.classification.lower())

        result = hit_identity(row)
        return result


def do_select_diagrams_ui(views: List[Identity]) -> Dict[Identity, Optional[bool]]:
    model = ViewTableModel(views)
    return [row for row, selected in do_show_select_ui(model=model, ok_text="Select",
                                                       title="Select Diagrams").items()
            if selected is True]
