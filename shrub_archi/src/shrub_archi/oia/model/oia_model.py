from shrub_archi.iam.model.iam_model import Identity as IamIdentity, Identity, IamLocalView


class Identity(IamIdentity):
    def __init__(self):
        super().__init__()
        self.hub_admin = None

    def from_dict(self, the_dict: dict) -> "Identity":
        super().from_dict(the_dict)
        if "hub_admin" in the_dict:
            self.hub_admin = True if the_dict["hub_admin"] else False

        return self

    def to_dict(self) -> dict:
        the_dict = super().to_dict()
        the_dict["hub_admin"] = self.hub_admin
        return the_dict


class OiaLocalView(IamLocalView):
    def _create_identity(self) -> Identity:
        return Identity()
