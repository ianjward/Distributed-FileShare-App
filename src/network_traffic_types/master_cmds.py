from twisted.protocols.amp import AMP, Command, Unicode, String, Integer, Float, Boolean


class UpdateFile(Command):
    arguments = [('encoded_file'.encode(), String()),
                 ('sender_ip'.encode(), Unicode())]
    response = [('ips'.encode(), Unicode()),
                ('chnks'.encode(), Unicode()),
                ('actn'.encode(), Unicode())]


class Test(Command):
    arguments = [('encoded_file'.encode(), String()),
                 ('sender_ip'.encode(), Unicode())]
    response = [('ips'.encode(), Unicode()),
                ('chnks'.encode(), Unicode()),
                ('actn'.encode(), Unicode())]


class PullFile(Command):
    arguments = [('encoded_file'.encode(), String()),
                 ('sender_ip'.encode(), Unicode())]
    response = [('ips'.encode(), Unicode()),
                ('chnks'.encode(), Unicode()),
                ('actn'.encode(), Unicode())]


class PushFile(Command):
    arguments = [('encoded_file'.encode(), String()),
                 ('sender_ip'.encode(), Unicode())]
    response = [('ips'.encode(), Unicode()),
                ('chnks'.encode(), Unicode()),
                ('actn'.encode(), Unicode())]


class DeleteFile(Command):
    arguments = [('file_name'.encode(), Unicode())]


class SeedFile(Command):
    arguments = [('encoded_file'.encode(), String()),
                 ('sender_ip'.encode(), Unicode())]


class GetFileList(Command):
    response = [('files'.encode(), Unicode())]


class CreateMasterFile(Command):
    arguments = [('encoded_file'.encode(), String()),
                 ('sender_ip'.encode(), Unicode())]


class CheckTrackingFile(Command):
    arguments = [('file_name'.encode(), Unicode())]
    response = [('is_tracking'.encode(), Unicode())]
