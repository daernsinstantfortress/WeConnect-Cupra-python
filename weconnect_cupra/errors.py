from __future__ import annotations
from typing import Dict, List, Set, Tuple, Callable, Any, Optional
import logging

from weconnect_cupra.weconnect_errors import ErrorEventType
from weconnect_cupra.addressable import AddressableLeaf, AddressableObject, AddressableDict


LOG = logging.getLogger("weconnect_cupra")


class RetrievalError(Exception):
    pass


class SetterError(Exception):
    pass


class ControlError(SetterError):
    pass


class AuthentificationError(Exception):
    pass


class TemporaryAuthentificationError(AuthentificationError):
    pass


class APICompatibilityError(Exception):
    pass


class APIError(Exception):
    pass

class ErrorBus:

    def __init__(self):
        self.__errorObservers: Set[Tuple[Callable[[Optional[Any], ErrorEventType], None], ErrorEventType]] = set()

    def addErrorObserver(self, observer: Callable, errortype: ErrorEventType) -> None:
        self.__errorObservers.add((observer, errortype))
        # LOG.debug('%s: Error event observer added for type: %s', self.getGlobalAddress(), errortype)

    def removeErrorObserver(self, observer: Callable, errortype: Optional[ErrorEventType] = None) -> None:
        self.__errorObservers = filter(lambda observerEntry: observerEntry[0] == observer
                                       or (errortype is not None and observerEntry[1] == errortype), self.__errorObservers)

    def getErrorObservers(self, errortype) -> List[Any]:
        return [observerEntry[0] for observerEntry in self.getErrorObserverEntries(errortype)]

    def getErrorObserverEntries(self, errortype: ErrorEventType) -> List[Any]:
        observers: Set[Tuple[Callable, ErrorEventType]] = set()
        for observerEntry in self.__errorObservers:
            observer, observertype = observerEntry
            del observer
            if errortype & observertype:
                observers.add(observerEntry)
        return observers

    def notifyError(self, element, errortype: ErrorEventType, detail: str, message: str = None) -> None:
        observers: List[Callable] = self.getErrorObservers(errortype)
        for observer in observers:
            observer(element=element, errortype=errortype, detail=detail, message=message)
        # LOG.debug('%s: Notify called for errors with type: %s for %d observers', self.getGlobalAddress(), errortype, len(observers))
