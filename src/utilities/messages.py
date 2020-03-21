import pickle
import socket


# Returns internet facing IP. Might not work without internet? But works on both linux and Windows while others did not.
def get_local_ip_address():
    internet = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    internet.connect(("8.8.8.8", 80))
    return internet.getsockname()[0]


class Message:
    def __init__(self, msg_type: str):
        super().__init__()
        self.mType = msg_type
        self.sender_ip = get_local_ip_address()

    def encode_msg(self):
        return pickle.dumps(self)


class AuthenticationResponse(Message):
    def __init__(self, share_password: str, username:str, user_password: str):
        super().__init__("AUTH_SYN")
        self.share_password = share_password
        self.username = username
        self.user_password = user_password
        self.sender = get_local_ip_address()


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


class UpdateMasterListMsg(Message):
    def __init__(self, mstr_dict:dict):
        super().__init__("MSTR_UPDTE")
        self.master_dict = mstr_dict


def decode_msg(msg) -> Message:
    return pickle.loads(msg)
