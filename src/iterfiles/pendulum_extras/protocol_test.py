from pendulum import Date
from .protocol_pendulum import Date as DateP


class TestDateProto(Date, DateP):
    pass
