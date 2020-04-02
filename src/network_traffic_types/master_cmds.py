from twisted.protocols.amp import AMP, Command, Unicode, String, Integer, Float


class Sum(Command):
    arguments = [('a'.encode(), Integer()),
                 ('b'.encode(), Integer())]
    response = [('total'.encode(), Integer())]


