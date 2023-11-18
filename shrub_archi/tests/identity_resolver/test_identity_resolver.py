from shrub_archi.merge.identity_resolver import RepositoryResolver, ResolvedIdentityAction, ResolutionStore, NaiveIdentityResolver
from shrub_archi.merge.model import Identity, Identities


def test_identity_resolver():
    ids1: Identities = {}
    ids2: Identities = {}

    ids1["1"] = Identity(unique_id="1", name="piet", classification="")
    ids1["2"] = Identity(unique_id="2", name="klaas", classification="")
    ids2["11"] = Identity(unique_id="11", name="pieto", classification="")
    ids2["22"] = Identity(unique_id="22", name="klaasj", classification="")

    for resolved_identity in RepositoryResolver().resolve(ids1, ids2):
        print(resolved_identity)


def test_stacked_action():
    actions = ResolvedIdentityAction.REPLACE_TARGET_ID.value + ResolvedIdentityAction.REPLACE_TARGET_NAME.value

    assert ResolvedIdentityAction.REPLACE_TARGET_NAME.part_of(actions) is True
    assert ResolvedIdentityAction.REPLACE_TARGET_ID.part_of(actions) is True
    assert ResolvedIdentityAction.REPLACE_TARGET_DESCRIPTION.part_of(actions) is False


def test_identity_resolver_with_resolutions():
    ids1: Identities = {}
    ids2: Identities = {}

    ids1["1"] = Identity(unique_id="1", name="piet", classification="")
    ids1["2"] = Identity(unique_id="2", name="klaas", classification="")
    ids2["11"] = Identity(unique_id="11", name="pieto", classification="")
    ids2["22"] = Identity(unique_id="22", name="klaasj", classification="")

    res_store = ResolutionStore()
    res_store.read_from_string(
        """{
            "1": "11"
        }"""
    )
    for resolved_identity in RepositoryResolver().resolve(ids1, ids2, comparator=NaiveIdentityResolver(resolution_store="/tmp")):
        print(resolved_identity)
