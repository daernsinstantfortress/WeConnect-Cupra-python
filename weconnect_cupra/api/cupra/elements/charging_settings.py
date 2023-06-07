import logging

from weconnect_cupra.addressable import AddressableLeaf, ChangeableAttribute
from weconnect_cupra.api.cupra.elements.generic_settings import GenericSettings
from weconnect_cupra.api.cupra.elements.enums import UnlockPlugState, MaximumChargeCurrent

LOG = logging.getLogger("weconnect_cupra")


class ChargingSettings(GenericSettings):
    def __init__(
        self,
        vehicle,
        parent,
        statusId,
        fromDict=None,
        fixAPI=True,
    ):
        self.maxChargeCurrentAC = ChangeableAttribute(
            localAddress='maxChargeCurrentAC', parent=self, value=None, valueType=MaximumChargeCurrent)
        self.autoUnlockPlugWhenCharged = ChangeableAttribute(localAddress='autoUnlockPlugWhenCharged', value=None,
                                                             parent=self, valueType=UnlockPlugState)
        self.autoUnlockPlugWhenChargedAC = ChangeableAttribute(localAddress='autoUnlockPlugWhenChargedAC', value=None,
                                                               parent=self, valueType=UnlockPlugState)
        self.targetSOC_pct = ChangeableAttribute(localAddress='targetSOC_pct', value=None, parent=self, valueType=float)
        
        super().__init__(vehicle=vehicle, parent=parent, statusId=statusId, fromDict=fromDict, fixAPI=fixAPI)

        self.maxChargeCurrentAC.addObserver(self.valueChanged, AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                            priority=AddressableLeaf.ObserverPriority.INTERNAL_MID)
        self.autoUnlockPlugWhenCharged.addObserver(self.valueChanged, AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                   priority=AddressableLeaf.ObserverPriority.INTERNAL_MID)
        self.autoUnlockPlugWhenChargedAC.addObserver(self.valueChanged, AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                     priority=AddressableLeaf.ObserverPriority.INTERNAL_MID)
        self.targetSOC_pct.addObserver(self.valueChanged, AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                       priority=AddressableLeaf.ObserverPriority.INTERNAL_MID)

    def update(self, fromDict, ignoreAttributes=None):
        ignoreAttributes = ignoreAttributes or []
        LOG.debug('Update Charging settings from dict')

        # Cupra
        if 'value' not in fromDict:
            fromDict['value'] = fromDict

        if 'value' in fromDict:
            self.maxChargeCurrentAC.fromDict(fromDict['value'], 'maxChargeCurrentAC')
            self.autoUnlockPlugWhenCharged.fromDict(fromDict['value'], 'autoUnlockPlugWhenCharged')
            self.autoUnlockPlugWhenChargedAC.fromDict(fromDict['value'], 'autoUnlockPlugWhenChargedAC')
            # Apparently different for Cupra. targetSOC_pct -> targetSoc_pct
            self.targetSOC_pct.fromDict(fromDict['value'], 'targetSoc_pct')
        else:
            self.maxChargeCurrentAC.enabled = False
            self.autoUnlockPlugWhenCharged.enabled = False
            self.autoUnlockPlugWhenChargedAC.enabled = False
            self.targetSOC_pct.enabled = False

        super().update(fromDict=fromDict, ignoreAttributes=(ignoreAttributes
                                                            + [
                                                                'maxChargeCurrentAC',
                                                                'autoUnlockPlugWhenCharged',
                                                                'autoUnlockPlugWhenChargedAC',
                                                                'targetSOC_pct'
                                                            ]))

    def __str__(self):
        string = super().__str__()
        if self.maxChargeCurrentAC.enabled:
            string += f'\n\tMaximum Charge Current AC: {self.maxChargeCurrentAC.value.value}'  # pylint: disable=no-member # this is a fales positive
        if self.autoUnlockPlugWhenCharged.enabled:
            string += f'\n\tAuto Unlock When Charged: {self.autoUnlockPlugWhenCharged.value.value}'  # pylint: disable=no-member # this is a fales positive
        if self.autoUnlockPlugWhenChargedAC.enabled:
            string += f'\n\tAuto Unlock When Charged AC: {self.autoUnlockPlugWhenChargedAC.value.value}'  # pylint: disable=no-member # this is a fales positive
        if self.targetSOC_pct.enabled:
            string += f'\n\tTarget SoC: {self.targetSOC_pct.value} %'
        return string
