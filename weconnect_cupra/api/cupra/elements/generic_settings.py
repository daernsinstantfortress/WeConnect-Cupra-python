from enum import Enum
import logging
import json

import requests

from weconnect_cupra.addressable import AddressableLeaf, ChangeableAttribute, AliasChangeableAttribute
from weconnect_cupra.elements.generic_status import GenericStatus
from weconnect_cupra.elements.error import Error
from weconnect_cupra.errors import SetterError
from weconnect_cupra.api.cupra.domain import Domain

LOG = logging.getLogger("weconnect_cupra")


class GenericSettings(GenericStatus):
    def valueChanged(self, element, flags):  # noqa: C901
        del element
        if flags & AddressableLeaf.ObserverEvent.VALUE_CHANGED \
                and not flags & AddressableLeaf.ObserverEvent.UPDATED_FROM_SERVER:

            # Action can be one of 'climatisation' or 'charging'
            action = self.id.partition('Settings')[0]

            # Valid Cupra Born use cases
            #
            # /vehicles/{vin}}/charging/requests/settings
            # {"maxChargeCurrentAC":"maximum","autoUnlockPlugWhenCharged":"off","targetSoc_pct":90.0}
            #   ChargingSettings.targetSOC_pct              -> targetSoc_pct
            #   ChargingSettings.maxChargeCurrentAC         -> maxChargeCurrentAC
            #   ChargingSettings.autoUnlockPlugWhenCharged  -> autoUnlockPlugWhenCharged
            #
            # /vehicles/{vin}}/climatisation/requests/settings
            # {"climatizationAtUnlock":false,"climatisationWithoutExternalPower":false,"windowHeatingEnabled":false,"targetTemperature_K":293.15,"carCapturedTimestamp":"2022-11-06T15:25:50Z","zoneFrontLeftEnabled":false,"zoneFrontRightEnabled":true}
            #   ClimatizationSettings.climatizationAtUnlock-> climatizationAtUnlock
            #   ClimatizationSettings.climatisationWithoutExternalPower -> climatisationWithoutExternalPower
            #   ClimatizationSettings.windowHeatingEnabled -> windowHeatingEnabled
            #   ClimatizationSettings.targetTemperature_K -> targetTemperature_K
            #   ClimatizationSettings.zoneFrontLeftEnabled -> zoneFrontLeftEnabled
            #   ClimatizationSettings.zoneFrontRightEnabled -> zoneFrontRightEnabled

            # Get current state from api
            settingsDict = self.vehicle.fetcher.fetchData(f'https://ola.prod.code.seat.cloud.vwgroup.com/vehicles/{self.vehicle.vin.value}/{action}/settings')['settings']

            # Figure out state
            for child in self.getLeafChildren():
                if isinstance(child, ChangeableAttribute) and not isinstance(child, AliasChangeableAttribute):
                    property_name = child.getLocalAddress()
                    # HACK map some names to support Cupra Born
                    property_name = 'targetSoc_pct' if property_name == 'targetSOC_pct' else property_name
                    if isinstance(child.value, Enum):  # pylint: disable=no-member # this is a fales positive
                        settingsDict[property_name] = child.value.value  # pylint: disable=no-member # this is a fales positive
                    else:
                        settingsDict[property_name] = child.value  # pylint: disable=no-member # this is a fales positive

            # Put new state to API
            putResponse = self.vehicle.fetcher.put(
                f'https://ola.prod.code.seat.cloud.vwgroup.com/vehicles/{self.vehicle.vin.value}/{action}/requests/settings',
                json=settingsDict,
                headers={
                    "accept": '*/*',
                    "user-agent": "CUPRAApp%20-%20Store/20220207 CFNetwork/1240.0.4 Darwin/20.6.0",
                    "Content-Type": "application/json",
                    "accept-language": "de-de",
                    "Accept-Encoding": "gzip, deflate"
                }
            )

            if putResponse.status_code != requests.codes['ok']:
                errorDict = putResponse.json()
                if errorDict is not None and 'error' in errorDict:
                    error = Error(localAddress='error', parent=self, fromDict=errorDict['error'])
                    if error is not None:
                        message = ''
                        if error.message.enabled and error.message.value is not None:
                            message += error.message.value
                        if error.info.enabled and error.info.value is not None:
                            message += ' - ' + error.info.value
                        if error.retry.enabled and error.retry.value is not None:
                            if error.retry.value:
                                message += ' - Please retry in a moment'
                            else:
                                message += ' - No retry possible'
                        raise SetterError(f'Could not set value ({message})')
                    else:
                        raise SetterError(f'Could not set value ({putResponse.status_code})')
                raise SetterError(f'Could not not set value ({putResponse.status_code})')

            responseDict = putResponse.json()
            if 'data' in responseDict and 'requestID' in responseDict['data']:
                if self.vehicle.requestTracker is not None:
                    self.vehicle.requestTracker.trackRequest(responseDict['data']['requestID'], Domain.ALL, 20, 120)
