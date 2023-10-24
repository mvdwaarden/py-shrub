from shrub_archi.identity_resolver import IdentityRepository, Identity, IdentityResolver


def test_identity_resolver():
    repo1 = IdentityRepository()
    repo2 = IdentityRepository()

    repo1.add(Identity(unique_id="1", name="piet", classification="", description=""))
    repo1.add(Identity(unique_id="2", name="klaas", classification="", description=""))
    repo2.add(Identity(unique_id="11", name="pieto", classification="", description=""))
    repo2.add(
        Identity(unique_id="22", name="klaasj", classification="", description=""))

    for resolved_identity in IdentityResolver(0).resolve(repo1, repo2):
        print(resolved_identity)