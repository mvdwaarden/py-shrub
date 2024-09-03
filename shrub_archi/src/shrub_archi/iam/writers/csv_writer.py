from shrub_archi.iam.model.iam_model import IamLocalView


def iam_write_csv(local_view: IamLocalView, file: str):
    with open(f"{file}-users.csv", "w") as ofp:
        ofp.write("email;groups\n")
        for u in [u for u in local_view.map_identities.values() if u.email]:
            ofp.write(f"{u.email};t.b.d.\n")

