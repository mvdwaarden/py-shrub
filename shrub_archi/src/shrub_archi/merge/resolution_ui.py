from typing import List

from .identity_resolver import ResolvedIdentity
from .select_ui import SelectModel, do_show_select_ui


class ResolutionTableModel(SelectModel):
    COL_COUNT: int = 6
    HEADER_LABELS: List[str] = ['Equal', 'Score', 'Rule', 'Class', 'Identity1',
                                'Identity2']

    def __init__(self, data: List[ResolvedIdentity]):
        super().__init__(data=data)
        for row in data:
            self.set_selected(row, row.resolver_result.manual_verification)

    def get_column_value_for(self, row: ResolvedIdentity, column: int):
        match column:
            case 0:
                return ''  # Checkbox column
            case 1:
                return row.resolver_result.score
            case 2:
                return row.resolver_result.rule
            case 3:
                return row.identity1.classification
            case 4:
                return row.identity1.name
            case 5:
                return row.identity2.name
            case _:
                return "?"

    def hit_row(self, row: ResolvedIdentity, search_text: str):
        def hit_identity(identity):
            return (identity.name and search_text in identity.name.lower()) or (
                    identity.description and search_text in identity.description.lower()) or (
                    identity.classification and search_text in identity.classification.lower())

        def hit_resolve_result(res):
            return search_text in str(res.score) or search_text in str(res.rule.lower())

        result = hit_identity(row.identity1) or hit_identity(
            row.identity2) or hit_resolve_result(row.resolver_result)
        return result


def do_show_resolve_ui(resolved_ids: List[ResolvedIdentity]) -> bool:
    selection = do_show_select_ui(model=ResolutionTableModel(resolved_ids),
                                  ok_text="Resolve")
    saved = False
    for row, selected in selection.items():
        row.resolver_result.manual_verification = selected
        saved = True

    return saved
