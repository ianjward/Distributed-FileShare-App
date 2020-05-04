from twisted.protocols.amp import AMP, Command, Unicode, String, Integer, Float


class ServeChunks(Command):
    arguments = [('encoded_file'.encode(), String()),
                 ('sender_ip'.encode(), Unicode())]


class ReceiveChunk(Command):
    arguments = [('chunk'.encode(), String())]


class InitiateServe(Command):
    arguments = [('encoded_file'.encode(), String())]


class ClientServeChunks(Command):
    arguments = [('encoded_file'.encode(), String()),
                 ('sender_ip'.encode(), Unicode())]


class ClientReceiveChunk(Command):
    arguments = [('chunk'.encode(), String())]