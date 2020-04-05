from twisted.protocols.amp import AMP, Command, Unicode, String, Integer, Float


class ServeFile(Command):
    arguments = [('encoded_file'.encode(), String()),
                 ('chunks_needed'.encode(), Unicode())]
    # response = [('update_ips'.encode(), Unicode())]