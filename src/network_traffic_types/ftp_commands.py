from twisted.protocols.amp import AMP, Command, Unicode, String, Integer, Float


class ServeFile(Command):
    arguments = [('encoded_file'.encode(), String()),
                 ('chunk_needed'.encode(), Integer())]
    response = [('chunk'.encode(), String())]
