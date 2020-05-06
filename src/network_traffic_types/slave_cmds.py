from twisted.protocols.amp import AMP, Command, Unicode, String, Integer, Float, Boolean


class RequestAuth(Command):
    arguments = []
    response = [
        ('share_password'.encode(), Unicode()),
        ('username'.encode(), Unicode()),
        ('user_password'.encode(), Unicode()),
        ('sender_ip'.encode(), Unicode()),
        ('sender_port'.encode(), Integer())]


class DeleteSlaveFile(Command):
    arguments = [('file_name'.encode(), Unicode())]


class AuthAccepted(Command):
    arguments = []
    response = []


class OpenTransferServer(Command):
    arguments = []
    # response = ['opened_status', Boolean()]

