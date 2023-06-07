from enum import Enum

class Service(Enum):
    WE_CONNECT = 'WeConnect'
    WE_CHARGE = 'WeCharge'
    MY_CUPRA = 'MyCupra'

    def __str__(self) -> str:
        return self.value
