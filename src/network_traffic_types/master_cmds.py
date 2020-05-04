from twisted.protocols.amp import AMP, Command, Unicode, String, Integer, Float


class UpdateFile(Command):
    arguments = [('encoded_file'.encode(), String()),
                 ('sender_ip'.encode(), Unicode())]
    response = [('ips'.encode(), Unicode()),
                ('chnks'.encode(), Unicode()),
                ('actn'.encode(), Unicode())]


class SeedFile(Command):
    arguments = [('encoded_file'.encode(), String()),
                 ('sender_ip'.encode(), Unicode())]


class GetFileList(Command):
    response = [('files'.encode(), Unicode())]
