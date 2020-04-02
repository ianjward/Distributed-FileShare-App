from twisted.protocols.amp import AMP, Command, Unicode, String, Integer, Float


class RequestAuth(Command):
    arguments = []
    response = [
        ('share_password'.encode(), Unicode()),
        ('username'.encode(), Unicode()),
        ('user_password'.encode(), Unicode())]


class AuthAccepted(Command):
    arguments = []
    response = []
