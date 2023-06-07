import logging

from weconnect_cupra.addressable import AddressableAttribute
from weconnect_cupra.elements.generic_status import GenericStatus

LOG = logging.getLogger("weconnect_cupra")


class OdometerMeasurement(GenericStatus):
    def __init__(
        self,
        vehicle,
        parent,
        statusId,
        fromDict=None,
        fixAPI=True,
    ):
        self.odometer = AddressableAttribute(
            localAddress='odometer', parent=self, value=None, valueType=int)
        super().__init__(vehicle=vehicle, parent=parent, statusId=statusId, fromDict=fromDict, fixAPI=fixAPI)

    def update(self, fromDict, ignoreAttributes=None):
        ignoreAttributes = ignoreAttributes or []
        LOG.debug(f'Odometer measurement from dict: {fromDict}')

        # Cupra
        if isinstance(fromDict, int) or isinstance(fromDict, float):
            self.set(fromDict)
            self.odometer.enabled = True
        elif 'value' in fromDict:
            if 'odometer' in fromDict['value']:
                self.set(fromDict['value']['odometer'])
                # odometer = int(fromDict['value']['odometer'])
                # if self.fixAPI and odometer == 0x7FFFFFFF:
                #     odometer = None
                #     LOG.info('%s: Attribute odometer was error value 0x7FFFFFFF. Setting error state instead'
                #              ' of 2147483647 km.', self.getGlobalAddress())
                # self.odometer.setValueWithCarTime(odometer, lastUpdateFromCar=None, fromServer=True)
            else:
                self.odometer.enabled = False
        else:
            self.odometer.enabled = False

        super().update(fromDict=fromDict, ignoreAttributes=(
            ignoreAttributes + ['odometer']))

    def set(self, value):
        odometer = int(value)
        if self.fixAPI and odometer == 0x7FFFFFFF:
            odometer = None
            LOG.info('%s: Attribute odometer was error value 0x7FFFFFFF. Setting error state instead'
                        ' of 2147483647 km.', self.getGlobalAddress())
        self.odometer.setValueWithCarTime(odometer, lastUpdateFromCar=None, fromServer=True)
        
    def __str__(self):
        string = super().__str__()
        if self.odometer.enabled:
            string += f'\n\tOdometer: {self.odometer.value}km'
        return string
