import pickle
from src.utilities.network_utilities import get_local_ip_address


class Message:
    def __init__(self, msg_type: str):
        super().__init__()
        self.mType = msg_type

    def encode_msg(self):
        return pickle.dumps(self)


class AuthenticationResponse(Message):
    def __init__(self, share_password: str, username:str, user_password: str):
        super().__init__("AUTH_SYN")
        self.share_password = share_password
        self.username = username
        self.user_password = user_password
        self.sender = get_local_ip_address()


class AuthenticationRequest(Message):
    def __init__(self):
        super().__init__("AUTH_REQ")


class PushFileMsg(Message):
    def __init__(self):
        super().__init__('PUSH_FILE')
        self.file_name = None
        self.data = None


def decode_msg(msg) -> Message:
    return pickle.loads(msg)