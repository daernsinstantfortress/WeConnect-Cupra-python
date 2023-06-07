from enum import Enum
import logging

from weconnect_cupra.addressable import AddressableAttribute
from weconnect_cupra.elements.generic_status import GenericStatus

LOG = logging.getLogger("weconnect_cupra")


class EngineState(GenericStatus):
    def __init__(
        self,
        vehicle,
        parent,
        statusId,
        fromDict=None,
        fixAPI=True,
    ):
        self.type = AddressableAttribute(
            localAddress='type', 
            value=None, 
            parent=self, 
            valueType=EngineState.EngineType
        )
        self.fuelType = AddressableAttribute(
            localAddress='fuelType', 
            value=None, 
            parent=self, 
            valueType=EngineState.FuelType
        )
        self.level = AddressableAttribute(
            localAddress='level', 
            value=None, 
            parent=self, 
            valueType=float)
        self.range = AddressableAttribute(
            localAddress='range', 
            value=None, 
            parent=self, 
            valueType=float)
        self.rangeUnit = AddressableAttribute(
            localAddress='range', 
            value=None, 
            parent=self, 
            valueType=str)

        super().__init__(vehicle=vehicle, parent=parent, statusId=statusId, fromDict=fromDict, fixAPI=fixAPI)

    def update(self, fromDict, ignoreAttributes=None):  # noqa: C901
        ignoreAttributes = ignoreAttributes or []

        self.type.fromDict(fromDict, self.type.localAddress)
        self.fuelType.fromDict(fromDict, self.fuelType.localAddress)
        self.level.fromDict(fromDict, self.level.localAddress)
        self.range.setValueWithCarTime(fromDict[self.range.localAddress].get('value'))
        self.rangeUnit.setValueWithCarTime(fromDict[self.range.localAddress].get('unit'))

    def __str__(self):
        string = super().__str__()
        string += f'\n\tEngine Type: {self.type.value}'
        string += f'\n\tFuel Type: {self.fuelType.value}'
        string += f'\n\tFuel Level: {self.level.value}'
        string += f'\n\tRange: {self.range.value} {self.rangeUnit.value}'
        return string

    class EngineType(Enum,):
        EV = 'EV'

    class FuelType(Enum,):
        EV = 'EV'
