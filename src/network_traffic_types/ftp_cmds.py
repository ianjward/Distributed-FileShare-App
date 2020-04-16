from twisted.protocols.amp import AMP, Command, Unicode, String, Integer, Float


class ServeChunks(Command):
    arguments = [('encoded_file'.encode(), String()),
                 ('sender_ip'.encode(), Unicode())]


class ReceiveChunk(Command):
    arguments = [('chunk'.encode(), String())]
