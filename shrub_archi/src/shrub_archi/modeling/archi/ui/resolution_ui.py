from typing import List

from shrub_archi.modeling.archi.model.archi_model import Relation
from shrub_archi.modeling.archi.resolver.entity_resolver import ResolvedEntity
from shrub_ui.src.shrub_ui.ui import TableSelectModel, do_show_select_ui


class ResolutionTableSelectModel(TableSelectModel):
    COL_COUNT: int = 8
    HEADER_LABELS: List[str] = [
        "Equal",
        "Score",
        "Rule",
        "Class",
        "ID 1",
        "Identity1",
        "ID 2",
        "Identity2",
    ]

    def __init__(self, data: List[ResolvedEntity]):
        super().__init__(data=data)
        for row in data:
            self.set_selected(row, row.resolver_result.manual_verification)

    def _row_name(self, identity):
        match identity:
            case Relation():
                if identity.name:
                    return f"{identity.source.name}-({identity.name})->{identity.target.name}"
                else:
                    return f"{identity.source.name}->{identity.target.name}"
            case _:
                return identity.name

    def column_value_for(self, row: ResolvedEntity, column: int):
        match column:
            case 0:
                return ""  # Checkbox column
            case 1:
                return row.resolver_result.score
            case 2:
                return row.resolver_result.rule
            case 3:
                return row.source.classification
            case 4:
                return row.source.unique_id
            case 5:
                return self._row_name(row.source)
            case 6:
                return row.target.unique_id
            case 7:
                return self._row_name(row.target)
            case _:
                return "?"

    def hit_row(self, row: ResolvedEntity, search_text: str):
        def hit_identity(identity):
            return (
                search_text in self._row_name(identity).lower()
                or (
                    identity.description and search_text in identity.description.lower()
                )
                or (
                    identity.classification
                    and search_text in identity.classification.lower()
                )
                or (identity.unique_id and search_text in identity.unique_id)
            )

        def hit_resolve_result(res):
            return search_text in str(res.score) or search_text in str(res.rule.lower())

        result = (
            hit_identity(row.source)
            or hit_identity(row.target)
            or hit_resolve_result(row.resolver_result)
        )
        return result


def do_show_resolve_ui(resolved_ids: List[ResolvedEntity]) -> bool:
    saved, selection = do_show_select_ui(
        model=ResolutionTableSelectModel(resolved_ids), ok_text="Resolve"
    )
    for row, selected in selection.items():
        row.resolver_result.manual_verification = selected

    return saved
