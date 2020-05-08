import pickle
import socket  # Wonder why pycharm thinks this isn't used...it is!
import src.utilities.networking


# Messages used only by the broadcast node as they are not AMP
class Message:
    def __init__(self, msg_type: str):
        super().__init__()
        self.mType = msg_type
        self.sender_ip = self.get_local_ip()

    def encode_msg(self):
        return pickle.dumps(self)

    def get_local_ip(self):
        return src.utilities.networking.get_local_ip_address()


def decode_msg(msg) -> Message:
    return pickle.loads(msg)


# Msg for requesting all share ips
class RequestMastersMsg(Message):
    def __init__(self):
        super().__init__("REQST_MSTRS")


# Msg send out all share ips
class MasterListMsg(Message):
    def __init__(self, mstr_dict:dict):
        super().__init__("MSTR_LIST")
        self.master_dict = mstr_dict


# Msg to update the broadcast share ips
class MasterUpdateMsg(Message):
    def __init__(self, mstr_dict:dict):
        super().__init__("MSTR_UPDTE")
        self.master_dict = mstr_dict
