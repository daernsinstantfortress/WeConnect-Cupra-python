from enum import Enum
import logging

from weconnect_cupra.addressable import AddressableAttribute
from weconnect_cupra.elements.generic_status import GenericStatus
from weconnect_cupra.elements.connection_state import ConnectionState

LOG = logging.getLogger("weconnect_cupra")


class ConnectionStatus(GenericStatus):
    def __init__(
        self,
        vehicle,
        parent,
        statusId,
        fromDict=None,
        fixAPI=True,
    ):
        self.connectionState = AddressableAttribute(
            localAddress='mode', 
            value=None, 
            parent=self, 
            valueType=ConnectionState.ConnectionState
        )

        super().__init__(vehicle=vehicle, parent=parent, statusId=statusId, fromDict=fromDict, fixAPI=fixAPI)

    def update(self, fromDict, ignoreAttributes=None):  # noqa: C901
        ignoreAttributes = ignoreAttributes or []

        self.connectionState.fromDict(fromDict, self.connectionState.localAddress)

    def __str__(self):
        string = super().__str__()
        string += f'\n\tConnection state: {self.connectionState.value.value}'
        return string


