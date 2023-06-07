from enum import Enum
from weconnect_cupra.elements.control_operation import ControlInputEnum


class MaximumChargeCurrent(ControlInputEnum,):
    MAXIMUM = 'maximum'
    REDUCED = 'reduced'
    INVALID = 'invalid'
    UNKNOWN = 'unknown'

    @classmethod
    def allowedValues(cls):
        return [MaximumChargeCurrent.MAXIMUM, MaximumChargeCurrent.REDUCED]


class UnlockPlugState(ControlInputEnum,):
    OFF = 'off'
    ON = 'on'
    PERMANENT = 'permanent'
    UNKNOWN = 'unknown'

    @classmethod
    def allowedValues(cls):
        return [UnlockPlugState.OFF, UnlockPlugState.ON]

class ClimatizationState(Enum,):
    OFF = 'off'
    ON = 'on'
    HEATING = 'heating'
    COOLING = 'cooling'
    VENTILATION = 'ventilation'
    INVALID = 'invalid'
    UNKNOWN = 'Unknown Climatization State'
