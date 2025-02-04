from shrub_archi.modeling.archi.model.archi_model import Entity, Entities
from shrub_archi.modeling.archi.repository.repository_merger import NaiveEntityResolver
from shrub_archi.modeling.archi.resolver.entity_resolver import (
    RepositoryResolver,
    ResolvedEntityAction,
)
from shrub_archi.modeling.archi.resolver.resolution_store import ResolutionStore


def test_Entity_resolver():
    ids1: Entities = {}
    ids2: Entities = {}

    ids1["1"] = Entity(unique_id="1", name="piet", classification="")
    ids1["2"] = Entity(unique_id="2", name="klaas", classification="")
    ids2["11"] = Entity(unique_id="11", name="pieto", classification="")
    ids2["22"] = Entity(unique_id="22", name="klaasj", classification="")

    for resolved_Entity in RepositoryResolver().resolve(ids1, ids2):
        print(resolved_Entity)


def test_stacked_action():
    actions = (
            ResolvedEntityAction.REPLACE_TARGET_ID.value
            + ResolvedEntityAction.REPLACE_TARGET_NAME.value
    )

    assert ResolvedEntityAction.REPLACE_TARGET_NAME.part_of(actions) is True
    assert ResolvedEntityAction.REPLACE_TARGET_ID.part_of(actions) is True
    assert ResolvedEntityAction.REPLACE_TARGET_DESCRIPTION.part_of(actions) is False


def test_Entity_resolver_with_resolutions():
    ids1: Entities = {}
    ids2: Entities = {}

    ids1["1"] = Entity(unique_id="1", name="piet", classification="")
    ids1["2"] = Entity(unique_id="2", name="klaas", classification="")
    ids2["11"] = Entity(unique_id="11", name="pieto", classification="")
    ids2["22"] = Entity(unique_id="22", name="klaasj", classification="")

    res_store = ResolutionStore()
    res_store.read_from_string(
        """{
            "1": "11"
        }"""
    )
    for resolved_Entity in RepositoryResolver().resolve(
        ids1, ids2, comparator=NaiveEntityResolver()
    ):
        print(resolved_Entity)
