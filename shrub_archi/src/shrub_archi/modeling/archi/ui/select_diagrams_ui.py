from typing import List, Tuple

from shrub_archi.modeling.archi.model.archi_model import View
from shrub_archi.ui.select_ui import TableSelectModel, do_show_select_ui


class ViewTableSelectModel(TableSelectModel):
    COL_COUNT: int = 8
    HEADER_LABELS: List[str] = [
        "Select",
        "ID",
        "Classification",
        "Name",
        "Description",
        "Source",
        "Elements",
        "Relations",
    ]

    def __init__(self, data: List[View]):
        super().__init__(data=data)

    def column_value_for(self, row: View, column: int):
        match column:
            case 0:
                return ""  # Checkbox column
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
            case 6:
                return len(row.referenced_elements) if row.referenced_elements else 0
            case 7:
                return len(row.referenced_relations) if row.referenced_relations else 0
            case _:
                return "?"

    def hit_row(self, row: View, search_text: str):
        def hit_identity(identity):
            return (
                (identity.name and search_text in identity.name.lower())
                or (
                    identity.description and search_text in identity.description.lower()
                )
                or (
                    identity.classification
                    and search_text in identity.classification.lower()
                )
            )

        result = hit_identity(row)
        return result


def do_select_diagrams_ui(views: List[View]) -> Tuple[bool, List[View]]:
    model = ViewTableSelectModel(views)
    selected, selection = do_show_select_ui(
        model=model, ok_text="Select", title="Select Diagrams"
    )
    return selected, [row for row, selected in selection.items() if selected is True]
