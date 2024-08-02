import datetime


class Token:
    def __init__(self, access_token, expires_in: int):
        self.access_token: str = access_token
        self.expires_in: int = expires_in
        self.creation_time: datetime.datetime = datetime.datetime.now()

    def __str__(self):
        return f"valid for {self.expires_in_actual()} access_token: {self.access_token}  "

    def expires_in_actual(self) -> int:
        d = datetime.datetime.now() - self.creation_time
        return self.expires_in - d.seconds

