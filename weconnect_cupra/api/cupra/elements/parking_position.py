import logging

from weconnect_cupra.addressable import AddressableAttribute
from weconnect_cupra.elements.generic_status import GenericStatus

LOG = logging.getLogger("weconnect_cupra")


class ParkingPosition(GenericStatus):
    def __init__(
        self,
        vehicle,
        parent,
        statusId,
        fromDict=None,
        fixAPI=True,
    ):
        self.latitude = AddressableAttribute(localAddress='latitude', parent=self, value=None, valueType=float)
        self.longitude = AddressableAttribute(localAddress='longitude', parent=self, value=None, valueType=float)
        super().__init__(vehicle=vehicle, parent=parent, statusId=statusId, fromDict=fromDict, fixAPI=fixAPI)

    def update(self, fromDict, ignoreAttributes=None):
        ignoreAttributes = ignoreAttributes or []
        LOG.debug('Update ParkingPosition from dict')

        if 'lat' in fromDict and 'lon' in fromDict:
            self.latitude.fromDict(fromDict, 'lat')
            self.longitude.fromDict(fromDict, 'lon')
        else:
            self.latitude.enabled = False
            self.longitude.enabled = False
            self.enabled = False

        super().update(fromDict=fromDict, ignoreAttributes=(ignoreAttributes + ['lat', 'lon']))

    def __str__(self):
        string = super().__str__()
        if self.latitude.enabled:
            string += f'\n\tLatitude: {self.latitude.value}'
        if self.longitude.enabled:
            string += f'\n\tLongitude: {self.longitude.value}'
        return string
