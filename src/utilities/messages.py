import pickle
import socket  # Wonder why pycharm thinks this isn't used...it is!
import src.utilities.networking


get_local_ip = lambda: src.utilities.networking.get_local_ip_address()


class Message:
    def __init__(self, msg_type: str):
        super().__init__()
        self.mType = msg_type
        self.sender_ip = get_local_ip()

    def encode_msg(self):
        return pickle.dumps(self)


def decode_msg(msg) -> Message:
    return pickle.loads(msg)


class AuthenticationResponse(Message):
    def __init__(self, share_password: str, username:str, user_password: str):
        super().__init__("AUTH_SYN")
        self.share_password = share_password
        self.username = username
        self.user_password = user_password
        self.sender = get_local_ip()


class AuthNeededMsg(Message):
    def __init__(self):
        super().__init__("AUTH_REQ")


class PushFileMsg(Message):
    def __init__(self):
        super().__init__('PUSH_FILE')
        self.file_name = None
        self.data = None


class RequestMastersMsg(Message):
    def __init__(self):
        super().__init__("REQST_MSTRS")


class MasterListMsg(Message):
    def __init__(self, mstr_dict:dict):
        super().__init__("MSTR_LIST")
        self.master_dict = mstr_dict


class MasterUpdateMsg(Message):
    def __init__(self, mstr_dict:dict):
        super().__init__("MSTR_UPDTE")
        self.master_dict = mstr_dict

