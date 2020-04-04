from twisted.protocols.amp import AMP, Command, Unicode, String, Integer, Float


class UpdateFile(Command):
    arguments = [('encoded_file'.encode(), String()),
                 ('sender_ip'.encode(), Unicode())]
    response = [('update_ips'.encode(), Unicode())]


class SeedFile(Command):
    arguments = [('encoded_file'.encode(), String()),
                 ('sender_ip'.encode(), Unicode())]
