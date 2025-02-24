from shrub_archi.modeling.archi.model.archi_model import Entity, Entities
from shrub_archi.modeling.archi.repository.repository_merger import NaiveEntityResolver
from shrub_archi.modeling.archi.resolver.entity_resolver import (
    RepositoryEntityResolver,
    ResolvedEntityAction,
)
from shrub_archi.modeling.archi.resolver.resolution_store import ResolutionStore
from typing import Dict
from shrub_archi.modeling.archi.repository.repository import Repository

def test_entity_resolver():
    source_ids: Dict[str,Entity] = {}
    target_ids: Dict[str,Entity] = {}

    source_ids["1"] = Entity(unique_id="1", name="piet", classification="")
    source_ids["2"] = Entity(unique_id="2", name="klaas", classification="")
    target_ids["11"] = Entity(unique_id="11", name="pieto", classification="")
    target_ids["22"] = Entity(unique_id="22", name="klaasj", classification="")

    for resolved_Entity in RepositoryEntityResolver().resolve(Repository(source_ids), target_ids):
        print(resolved_Entity)


def test_stacked_action():
    actions = (
            ResolvedEntityAction.REPLACE_TARGET_ID.value
            + ResolvedEntityAction.REPLACE_TARGET_NAME.value
    )

    assert ResolvedEntityAction.REPLACE_TARGET_NAME.part_of(actions) is True
    assert ResolvedEntityAction.REPLACE_TARGET_ID.part_of(actions) is True
    assert ResolvedEntityAction.REPLACE_TARGET_DESCRIPTION.part_of(actions) is False


def test_entity_resolver_with_resolutions():
    source_ids: Dict[str,Entity] = {}
    target_ids: Dict[str,Entity] = {}

    source_ids["1"] = Entity(unique_id="1", name="piet", classification="")
    source_ids["2"] = Entity(unique_id="2", name="klaas", classification="")
    target_ids["11"] = Entity(unique_id="11", name="pieto", classification="")
    target_ids["22"] = Entity(unique_id="22", name="klaasj", classification="")

    res_store = ResolutionStore()
    res_store.read_from_string(
        """{
            "1": "11"
        }"""
    )
    for resolved_Entity in RepositoryEntityResolver().resolve(
        source_ids, target_ids, comparator=NaiveEntityResolver()
    ):
        print(resolved_Entity)
