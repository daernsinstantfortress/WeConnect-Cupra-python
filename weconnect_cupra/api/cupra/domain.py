from enum import Enum


class Domain(Enum):
    ALL = 'all'
    ALL_CAPABLE = 'allCapable'
    USER_CAPABILITIES = 'userCapabilities'
    MEASUREMENTS = 'measurements'

    # Standard domains from VW api
    CHARGING = 'charging'
    CLIMATISATION = 'climatisation'
    PARKING = 'parking'
    ACCESS = 'access'
    STATUS = 'status'

    def __str__(self):
        return self.value
