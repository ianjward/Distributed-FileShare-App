from twisted.protocols.amp import AMP, Command, Unicode, String, Integer, Float


class Sum(Command):
    arguments = [('a'.encode(), Integer()),
                 ('b'.encode(), Integer())]
    response = [('total'.encode(), Integer())]


class SeedFile(Command):
    arguments = [('encoded_file'.encode(), String()),
                 ('sender_ip'.encode(), Unicode())]
