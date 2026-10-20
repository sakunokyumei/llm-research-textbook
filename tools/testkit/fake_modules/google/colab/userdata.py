"""Stand-in for google.colab.userdata (Colab secrets)."""


class SecretNotFoundError(Exception):
    pass


def get(name):
    raise SecretNotFoundError(name)
