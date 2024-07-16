from enum import Enum
import logging

from weconnect_cupra.addressable import AddressableAttribute
from weconnect_cupra.api.cupra.elements.enums import ClimatizationState
from weconnect_cupra.elements.generic_status import GenericStatus

LOG = logging.getLogger("weconnect_cupra")


class ClimatizationStatus(GenericStatus):
    def __init__(
        self,
        vehicle,
        parent,
        statusId,
        fromDict=None,
        fixAPI=True,
    ):
        self.remainingClimatisationTime_min = AddressableAttribute(
            localAddress='remainingClimatisationTimeInMinutes', parent=self, value=None, valueType=int)
        self.climatisationState = AddressableAttribute(localAddress='climatisationState', value=None, parent=self,
                                                       valueType=ClimatizationState)
        super().__init__(vehicle=vehicle, parent=parent, statusId=statusId, fromDict=fromDict, fixAPI=fixAPI)

    def update(self, fromDict, ignoreAttributes=None):
        ignoreAttributes = ignoreAttributes or []
        LOG.debug('Update Climatization status from dict')

        # Cupra
        if 'value' not in fromDict:
            fromDict['value'] = fromDict

        if 'value' in fromDict:
            self.climatisationState.fromDict(fromDict['value'], 'climatisationState')
            if 'remainingClimatisationTimeInMinutes' in fromDict['value']:
                remainingTime = int(fromDict['value']['remainingClimatisationTimeInMinutes'])
                if self.fixAPI and remainingTime != 0 and self.climatisationState.value == ClimatizationState.OFF:
                    remainingTime = 0
                    LOG.debug('%s: Attribute remainingClimatisationTimeInMinutes is %s while climatisationState is %s. Setting 0 instead',
                              self.getGlobalAddress(), fromDict['value']['remainingClimatisationTimeInMinutes'], self.climatisationState.value)
                self.remainingClimatisationTime_min.setValueWithCarTime(remainingTime, lastUpdateFromCar=None, fromServer=True)
            else:
                self.remainingClimatisationTime_min.enabled = False
        else:
            self.remainingClimatisationTime_min.enabled = False
            self.climatisationState.enabled = False

        super().update(fromDict=fromDict, ignoreAttributes=(
            ignoreAttributes + ['remainingClimatisationTimeInMinutes', 'climatisationState']))

    def __str__(self):
        string = super().__str__()
        if self.climatisationState.enabled:
            string += f'\n\tState: {self.climatisationState.value.value}'  # pylint: disable=no-member
        if self.remainingClimatisationTime_min.enabled:
            string += f'\n\tRemaining Climatization Time: {self.remainingClimatisationTime_min.value} min'
        return string
