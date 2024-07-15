from __future__ import annotations
from typing import Dict, List, Any, Optional
from enum import Enum
import logging

from weconnect_cupra.addressable import AddressableObject, AddressableAttribute, AddressableDict, AddressableList
from weconnect_cupra.api.cupra.elements.odometer_measurement import OdometerMeasurement
from weconnect_cupra.api.cupra.elements.parking_position import ParkingPosition
from weconnect_cupra.elements.error import Error
from weconnect_cupra.elements.window_heating_status import WindowHeatingStatus
from weconnect_cupra.errors import APICompatibilityError, APIError
from weconnect_cupra.util import toBool
from weconnect_cupra.api.cupra.domain import Domain
from weconnect_cupra.fetch import Fetcher
from weconnect_cupra.elements.plug_status import PlugStatus
from weconnect_cupra.api.cupra.elements.climatization_status import ClimatizationStatus
from weconnect_cupra.api.cupra.elements.climatization_settings import ClimatizationSettings
from weconnect_cupra.api.cupra.elements.charging_settings import ChargingSettings
from weconnect_cupra.api.cupra.elements.controls import Controls
from weconnect_cupra.api.cupra.elements.generic_capability import GenericCapability
from weconnect_cupra.api.cupra.elements.charging_status import ChargingStatus
from weconnect_cupra.api.cupra.elements.helpers.request_tracker import RequestTracker
from weconnect_cupra.api.cupra.elements.battery_status import BatteryStatus
from weconnect_cupra.api.cupra.elements.access_status import AccessStatus
from weconnect_cupra.api.cupra.elements.connection_status import ConnectionStatus


LOG: logging.Logger = logging.getLogger("weconnect_cupra")


class DomainDict(AddressableDict):
    def __init__(self, **kwargs):
        self.error: Error = Error(localAddress='error', parent=self)
        super().__init__(**kwargs)

    def updateError(self, fromDict: Dict[str, Any]):
        if 'error' in fromDict:
            self.error.update(fromDict['error'])
        else:
            self.error.reset()

    def hasError(self) -> bool:
        return self.error.enabled


class Vehicle(AddressableObject):  # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        fetcher: Fetcher,
        vin: str,
        parent: AddressableDict[str, Vehicle],
        fromDict: Dict[str, Any],
        fixAPI: bool = True,
        updateCapabilities: bool = True,
        updatePictures: bool = True,
        selective: Optional[list[Domain]] = None,
        enableTracker: bool = False
    ) -> None:
        self.fetcher: Fetcher = fetcher
        super().__init__(localAddress=vin, parent=parent)

        # Public API properties
        self.vin: AddressableAttribute[str] = AddressableAttribute(
            localAddress='vin', parent=self, value=None, valueType=str)
        self.role: AddressableAttribute[Vehicle.User.Role] = AddressableAttribute(
            localAddress='role', parent=self, value=None, valueType=Vehicle.User.Role)
        self.enrollmentStatus: AddressableAttribute[Vehicle.User.EnrollmentStatus] = AddressableAttribute(
            localAddress='enrollmentStatus', parent=self, value=None, valueType=Vehicle.User.EnrollmentStatus)
        self.userRoleStatus: AddressableAttribute[Vehicle.User.UserRoleStatus] = AddressableAttribute(
            localAddress='userRoleStatus', parent=self, value=None, valueType=Vehicle.User.UserRoleStatus)
        self.model: AddressableAttribute[str] = AddressableAttribute(
            localAddress='model', parent=self, value=None, valueType=str)
        self.devicePlatform: AddressableAttribute[Vehicle.DevicePlatform] = AddressableAttribute(
            localAddress='devicePlatform', parent=self, value=None, valueType=Vehicle.DevicePlatform)
        self.nickname: AddressableAttribute[str] = AddressableAttribute(
            localAddress='nickname', parent=self, value=None, valueType=str)
        self.brandCode: AddressableAttribute[Vehicle.BrandCode] = AddressableAttribute(
            localAddress='brandCode', parent=self, value=None, valueType=Vehicle.BrandCode)
        self.capabilities: AddressableDict[str, GenericCapability] = AddressableDict(
            localAddress='capabilities', parent=self)
        self.domains: AddressableDict[str, DomainDict] = AddressableDict(
            localAddress='domains', parent=self)
        self.images: AddressableAttribute[Dict[str, str]] = AddressableAttribute(
            localAddress='images', parent=self, value=None, valueType=dict)
        self.tags: AddressableAttribute[List[str]] = AddressableAttribute(
            localAddress='tags', parent=self, value=None, valueType=list)
        self.coUsers: AddressableList[Vehicle.User] = AddressableList(
            localAddress='coUsers', parent=self)
        self.controls: Controls = Controls(
            localAddress='controls', vehicle=self, parent=self)

        self.fixAPI: bool = fixAPI
        self.requestTracker: Optional[RequestTracker] = None
        if enableTracker:
            self.requestTracker = RequestTracker(self)

        self.update(fromDict, updateCapabilities=updateCapabilities, updatePictures=updatePictures, selective=selective)

    def enableTracker(self) -> None:
        if self.requestTracker is None:
            self.requestTracker = RequestTracker(self)

    def disableTracker(self) -> None:
        if self.requestTracker is not None:
            self.requestTracker.clear()
        self.requestTracker = None

    def statusExists(self, domain: str, status: str) -> bool:
        if domain in self.domains and status in self.domains[domain]:
            return True
        return False

    def assign_properties_to_domain(self, klass, properties: dict, domain_value: str, settings_key: str) -> DomainDict:
        if not properties:
            return
        if domain_value not in self.domains:
            self.domains[domain_value] = DomainDict(localAddress=domain_value, parent=self.domains)
            self.domains[domain_value].enabled = True
        # Create a settings object
        if settings_key in self.domains[domain_value]:
            LOG.debug('Status %s exists, updating it', settings_key)
            self.domains[domain_value][settings_key].update(fromDict=properties)
            self.domains[domain_value][settings_key].enabled = True
        else:
            LOG.debug('Status %s does not exist, creating it', settings_key)
            self.domains[domain_value][settings_key] = klass(vehicle=self,
                                                             parent=self.domains[domain_value],
                                                             statusId=settings_key,
                                                             fixAPI=self.fixAPI,
                                                             fromDict=properties)
            # We also have to call update(), not just pass fromDict to constructor
            self.domains[domain_value][settings_key].update(fromDict=properties)
            self.domains[domain_value][settings_key].enabled = True

    def update(  # noqa: C901  # pylint: disable=too-many-branches
        self,
        fromDict: Dict[str, Any] = {},
        updateCapabilities: bool = True,
        updatePictures: bool = True,
        force: bool = False,
        selective: Optional[list[Domain]] = None
    ) -> None:
        if fromDict is not None:
            LOG.debug('Create /update vehicle')

             # Set basic vehicle properties
            self.vin.fromDict(fromDict, 'vin')
            self.role.fromDict(fromDict, 'userRole')
            self.enrollmentStatus.fromDict(fromDict, 'enrollmentStatus')
            self.userRoleStatus.fromDict(fromDict, 'userRoleStatus')
            self.model.fromDict(fromDict, 'model')
            self.devicePlatform.fromDict(fromDict, 'devicePlatform')
            self.nickname.fromDict(fromDict, 'vehicleNickname')
            self.brandCode.fromDict(fromDict, 'brandCode')

            # Update capabilities
            if updateCapabilities:
                capabilities_dict = self.fetcher.fetchData(
                    f'https://ola.prod.code.seat.cloud.vwgroup.com/v1/vehicles/{self.vin.value}/capabilities')
                if 'capabilities' in capabilities_dict and capabilities_dict['capabilities'] is not None:
                    for capDict in capabilities_dict['capabilities']:
                        if 'id' in capDict:
                            if capDict['id'] in self.capabilities:
                                self.capabilities[capDict['id']].update(fromDict=capDict)
                            else:
                                self.capabilities[capDict['id']] = GenericCapability(
                                    capabilityId=capDict['id'],
                                    parent=self.capabilities,
                                    fromDict=capDict,
                                    fixAPI=self.fixAPI)
                    for capabilityId in [capabilityId for capabilityId in self.capabilities.keys()
                            if capabilityId not in [capability['id']
                            for capability in capabilities_dict['capabilities'] if 'id' in capability]]:
                        del self.capabilities[capabilityId]
                else:
                    self.capabilities.clear()
                    self.capabilities.enabled = False

            if 'images' in fromDict:
                self.images.setValueWithCarTime(fromDict['images'], lastUpdateFromCar=None, fromServer=True)
            else:
                self.images.enabled = False

            if 'tags' in fromDict:
                self.tags.setValueWithCarTime(fromDict['tags'], lastUpdateFromCar=None, fromServer=True)
            else:
                self.tags.enabled = False

            if 'coUsers' in fromDict and fromDict['coUsers'] is not None:
                for user in fromDict['coUsers']:
                    if 'id' in user:
                        usersWithId = [x for x in self.coUsers if x.id.value == user['id']]
                        if len(usersWithId) > 0:
                            usersWithId[0].update(fromDict=user)
                        else:
                            self.coUsers.append(Vehicle.User(localAddress=str(len(self.coUsers)), parent=self.coUsers, fromDict=user))
                    else:
                        raise APICompatibilityError('User is missing id field')
                # Remove all users that are not in list anymore
                for user in [user for user in self.coUsers if user.id.value not in [x['id'] for x in fromDict['coUsers']]]:
                    self.coUsers.remove(user)
            else:
                self.coUsers.enabled = False
                self.coUsers.clear()

        self.updateStatus(updateCapabilities=updateCapabilities, force=force, selective=selective)

    def updateStatus(self, updateCapabilities: bool = True, force: bool = False,  # noqa: C901 # pylint: disable=too-many-branches
                selective: Optional[list[Domain]] = None):
        """Update vehicle status and settings domains, as well as controls, following calls to API"""

        if self.vin.value is None:
            raise APIError('VIN value is not set')

        charging_settings_dict = self.fetcher.fetchData(
            f'https://ola.prod.code.seat.cloud.vwgroup.com/vehicles/{self.vin.value}/charging/settings')['settings'] #same
        charging_status_dict = self.fetcher.fetchData(
            f'https://ola.prod.code.seat.cloud.vwgroup.com/vehicles/{self.vin.value}/charging/status')['status'] # same
        climatization_status_dict = self.fetcher.fetchData(
            f'https://ola.prod.code.seat.cloud.vwgroup.com/v1/vehicles/{self.vin.value}/climatisation/status') # changed
        climatization_settings_dict = self.fetcher.fetchData(
            f'https://ola.prod.code.seat.cloud.vwgroup.com/v2/vehicles/{self.vin.value}/climatisation/settings') # changed
        connection_dict = self.fetcher.fetchData(
            f'https://ola.prod.code.seat.cloud.vwgroup.com/vehicles/{self.vin.value}/connection')['connection']


        jobs = {
            Domain.CHARGING: {
                'chargingSettings': (ChargingSettings, charging_settings_dict),
                'chargingStatus': (ChargingStatus, charging_status_dict['charging']),
                'batteryStatus': (BatteryStatus, charging_status_dict['battery']),
                'plugStatus': (PlugStatus, charging_status_dict['plug'])
            },
            Domain.CLIMATISATION: {
                'climatisationStatus': (ClimatizationStatus, climatization_status_dict['climatisationStatus']),
                'windowHeatingStatus': (WindowHeatingStatus, climatization_status_dict['windowHeatingStatus']),
                'climatisationSettings': (ClimatizationSettings, climatization_settings_dict)
            },
            Domain.STATUS: {
                'connectionStatus': (ConnectionStatus, connection_dict)
            }
          
        }

        for domain_enum, domain_props in jobs.items():
            for prop_name, prop_config in domain_props.items():
                self.assign_properties_to_domain(
                    klass=prop_config[0],
                    properties=prop_config[1],
                    domain_value=domain_enum.value,
                    settings_key=prop_name)

        if 'parkingPosition' in self.capabilities and not self.capabilities['parkingPosition'].status.value:
            try:
                parking_position_dict = self.fetcher.fetchData(
                    f'https://ola.prod.code.seat.cloud.vwgroup.com/v1/vehicles/{self.vin.value}/parkingposition')
                
                self.assign_properties_to_domain(
                    klass=ParkingPosition,
                    properties=parking_position_dict,
                    domain_value=Domain.PARKING.value,
                    settings_key='parkingPosition')
            except:
                # This can fire when the vehicle is driving, so suppress it
                LOG.debug('Failed to get parking position')

        if 'state' in self.capabilities and not self.capabilities['state'].status.value:
            try:
                mileage_dict = self.fetcher.fetchData(
                    f'https://ola.prod.code.seat.cloud.vwgroup.com/v1/vehicles/{self.vin.value}/mileage') 
                
                self.assign_properties_to_domain(
                    klass=OdometerMeasurement,
                    properties=mileage_dict,
                    domain_value=Domain.MEASUREMENTS.value,
                    settings_key='odometerStatus')

                status_dict = self.fetcher.fetchData(
                    f'https://ola.prod.code.seat.cloud.vwgroup.com/v2/vehicles/{self.vin.value}/status') #same

                self.assign_properties_to_domain(
                    klass=AccessStatus,
                    properties=status_dict,
                    domain_value=Domain.ACCESS.value,
                    settings_key='accessStatus')                

            except:
                LOG.warn('Failed to get vehicle status')

        # Controls
        self.controls.update()

    def __str__(self) -> str:  # noqa: C901
        returnString: str = ''
        if self.vin.enabled and self.vin.value is not None:
            returnString += f'VIN:               {self.vin.value}\n'
        if self.model.enabled and self.model.value is not None:
            returnString += f'Model:             {self.model.value}\n'
        if self.devicePlatform.enabled and self.devicePlatform.value is not None:
            returnString += f'Device Platform:   {self.devicePlatform.value.value}\n'
        if self.nickname.enabled and self.nickname.value is not None:
            returnString += f'Nickname:          {self.nickname.value}\n'
        if self.brandCode.enabled and self.brandCode.value is not None:
            returnString += f'Brand Code:        {self.brandCode.value.value}\n'
        if self.role.enabled and self.role.value is not None:
            returnString += f'Role:              {self.role.value.value}\n'  # pylint: disable=no-member
        if self.enrollmentStatus.enabled and self.enrollmentStatus.value is not None:
            returnString += f'Enrollment Status: {self.enrollmentStatus.value.value}\n'  # pylint: disable=no-member
        if self.userRoleStatus.enabled and self.userRoleStatus.value is not None:
            returnString += f'User Role Status:  {self.userRoleStatus.value.value}\n'  # pylint: disable=no-member
        if self.coUsers.enabled:
            returnString += f'Co-Users: {len(self.coUsers)} items\n'
            for coUser in self.coUsers:
                if coUser.enabled:
                    returnString += ''.join(['\t' + line for line in str(coUser).splitlines(True)]) + '\n'
        if self.tags.enabled and self.tags.value:
            returnString += 'Tags:               ' + ', '.join(self.tags.value) + '\n'
        if self.capabilities.enabled:
            returnString += f'Capabilities: {len(self.capabilities)} items\n'
            for capability in self.capabilities.values():
                if capability.enabled:
                    returnString += ''.join(['\t' + line for line in str(capability).splitlines(True)]) + '\n'
        if self.domains.enabled:
            returnString += f'Domains: {len(self.domains)} items\n'
            for domain in self.domains:
                returnString += f'[{domain}] Elements: {len(self.domains[domain])} items\n'
                for status in self.domains[domain].values():
                    if status.enabled:
                        returnString += ''.join(['\t' + line for line in str(status).splitlines(True)]) + '\n'
                if self.domains[domain].hasError():
                    returnString += ''.join(['\t' + line for line in f'Error: {self.domains[domain].error}'.splitlines(True)]) + '\n'
        return returnString

    class Badge(Enum):
        CHARGING = 'charging'
        CONNECTED = 'connected'
        COOLING = 'cooling'
        HEATING = 'heating'
        LOCKED = 'locked'
        PARKING = 'parking'
        UNLOCKED = 'unlocked'
        VENTILATING = 'ventilating'
        WARNING = 'warning'

    class DevicePlatform(Enum,):
        MBB = 'MBB'
        MBB_ODP = 'MBB_ODP'
        MBB_OFFLINE = 'MBB_OFFLINE'
        WCAR = 'WCAR'
        UNKNOWN = 'UNKNOWN'

    class BrandCode(Enum,):
        V = 'V'
        UNKNOWN = 'unknown brand code'

    class User(AddressableObject):
        def __init__(
            self,
            localAddress: str,
            parent: AddressableObject,
            fromDict: Dict[str, str] = {},
        ) -> None:
            super().__init__(localAddress=localAddress, parent=parent)
            self.id: AddressableAttribute[str] = AddressableAttribute(localAddress='id', parent=self, value=None, valueType=str)
            self.role: AddressableAttribute[Vehicle.User.Role] = AddressableAttribute(localAddress='role', parent=self, value=None, valueType=Vehicle.User.Role)
            self.roleReseted: AddressableAttribute[bool] = AddressableAttribute(localAddress='roleReseted', parent=self, value=None, valueType=bool)
            self.enrollmentStatus: AddressableAttribute[Vehicle.User.EnrollmentStatus] = AddressableAttribute(
                localAddress='enrollmentStatus', parent=self,
                value=None,
                valueType=Vehicle.User.EnrollmentStatus)

            if fromDict is not None:
                self.update(fromDict)

        def update(self, fromDict) -> None:
            LOG.debug('Update User from dict')

            if 'id' in fromDict:
                self.id.setValueWithCarTime(fromDict['id'], lastUpdateFromCar=None, fromServer=True)
            else:
                self.id.enabled = False

            if 'role' in fromDict and fromDict['role']:
                try:
                    self.role.setValueWithCarTime(Vehicle.User.Role(fromDict['role']), lastUpdateFromCar=None, fromServer=True)
                except ValueError:
                    self.role.setValueWithCarTime(Vehicle.User.Role.UNKNOWN, lastUpdateFromCar=None, fromServer=True)
                    LOG.debug('An unsupported role: %s was provided, please report this as a bug', fromDict['role'])
            else:
                self.role.enabled = False

            if 'roleReseted' in fromDict:
                self.roleReseted.setValueWithCarTime(toBool(fromDict['roleReseted']), lastUpdateFromCar=None, fromServer=True)
            else:
                self.roleReseted.enabled = False

            if 'enrollmentStatus' in fromDict and fromDict['enrollmentStatus']:
                try:
                    self.enrollmentStatus.setValueWithCarTime(Vehicle.User.EnrollmentStatus(fromDict['enrollmentStatus']), lastUpdateFromCar=None,
                                                              fromServer=True)
                except ValueError:
                    self.enrollmentStatus.setValueWithCarTime(Vehicle.User.EnrollmentStatus.UNKNOWN, lastUpdateFromCar=None, fromServer=True)
                    LOG.debug('An unsupported target operation: %s was provided, please report this as a bug', fromDict['enrollmentStatus'])
            else:
                self.enrollmentStatus.enabled = False

        def __str__(self) -> str:
            returnValue: str = ''
            if self.id.enabled and self.id.value is not None:
                returnValue += f'Id: {self.id.value}, '
            if self.role.enabled and self.role.value is not None:
                returnValue += f' Role: {self.role.value.value}, '  # pylint: disable=no-member
            if self.roleReseted.enabled and self.roleReseted.value is not None:
                returnValue += f' Reseted: {self.roleReseted.value}, '
            if self.enrollmentStatus.enabled and self.enrollmentStatus.value is not None:
                returnValue += f' Enrollment Status: {self.enrollmentStatus.value.value}'  # pylint: disable=no-member
            return returnValue

        class Role(Enum,):
            PRIMARY_USER = 'PRIMARY_USER'
            SECONDARY_USER = 'SECONDARY_USER'
            GUEST_USER = 'GUEST_USER'
            CDIS_UNKNOWN_USER = 'CDIS_UNKNOWN_USER'
            UNKNOWN = 'UNKNOWN'

            def __str__(self) -> str:
                return self.value

        class EnrollmentStatus(Enum,):
            STARTED = 'started'
            NOT_STARTED = 'not_started'
            COMPLETED = 'completed'
            GDC_MISSING = 'gdc_missing'
            INACTIVE = 'inactive'
            UNKNOWN = 'unknown'

        class UserRoleStatus(Enum,):
            ENABLED = 'ENABLED'
            DISABLED_HMI = 'DISABLED_HMI'
            DISABLED_SPIN = 'DISABLED_SPIN'
            DISABLED_PU_SPIN_RESET = 'DISABLED_PU_SPIN_RESET'
            CDIS_UNKNOWN_USER = 'CDIS_UNKNOWN_USER'
            UNKNOWN = 'UNKNOWN'
