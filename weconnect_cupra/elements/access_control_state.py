from enum import Enum

class AccessControlState:

    class OverallState(Enum):
        SAFE = 'safe'
        UNSAFE = 'unsafe'
        INVALID = 'invalid'
        UNKNOWN = 'unknown overall state'

    class EngineState(Enum):
        ON = 'on'
        OFF = 'off'

    class LightsState(Enum):
        ON = 'on'
        OFF = 'off'

    class OpenState(Enum):
        OPEN = 'open'
        CLOSED = 'closed'
        UNSUPPORTED = 'unsupported'
        INVALID = 'invalid'
        UNKNOWN = 'unknown open state'

    class LockState(Enum):
        LOCKED = 'locked'
        UNLOCKED = 'unlocked'
        UNKNOWN = 'unknown lock state'

    # class WindowOpenState(Enum,):
    #     OPEN = 'open'
    #     CLOSED = 'closed'
    #     UNSUPPORTED = 'unsupported'
    #     INVALID = 'invalid'
    #     UNKNOWN = 'unknown open state'            