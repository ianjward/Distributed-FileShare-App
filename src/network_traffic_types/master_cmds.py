from twisted.protocols.amp import AMP, Command, Unicode, String, Integer, Float


class UpdateFile(Command):
    arguments = [('encoded_file'.encode(), String()),
                 ('sender_ip'.encode(), Unicode())]
    response = [('ips'.encode(), String()),
                ('chnks'.encode(), String()),
                ('actn'.encode(), String())]


class SeedFile(Command):
    arguments = [('encoded_file'.encode(), String()),
                 ('sender_ip'.encode(), Unicode())]
