from enum import Enum
import logging

from weconnect_cupra.addressable import AddressableObject, AddressableAttribute, AddressableDict
from weconnect_cupra.elements.generic_status import GenericStatus
from weconnect_cupra.elements.access_control_state import AccessControlState

LOG = logging.getLogger("weconnect_cupra")


class AccessStatus(GenericStatus):
    def __init__(
        self,
        vehicle,
        parent,
        statusId,
        fromDict=None,
        fixAPI=True,
    ):
        self.overallStatus = AddressableAttribute(localAddress='overallStatus', parent=self, value=None, valueType=AccessControlState.OverallState)
        self.doorLockStatus = AddressableAttribute(localAddress='doorLockStatus', parent=self, value=None, valueType=AccessControlState.LockState)
        self.engineStatus = AddressableAttribute(localAddress='overallStatus', parent=self, value=None, valueType=AccessControlState.EngineState)
        self.lightsStatus = AddressableAttribute(localAddress='overallStatus', parent=self, value=None, valueType=AccessControlState.LightsState)
        self.doors = AddressableDict(localAddress='doors', parent=self)
        self.windows = AddressableDict(localAddress='windows', parent=self)
        super().__init__(vehicle=vehicle, parent=parent, statusId=statusId, fromDict=fromDict, fixAPI=fixAPI)

    def update(self, fromDict, ignoreAttributes=None):  # noqa: C901
        ignoreAttributes = ignoreAttributes or []
        LOG.debug('Update access status from dict')

        # Cupra
        if 'value' not in fromDict:
            fromDict['value'] = fromDict

        if 'value' in fromDict:
            # self.overallStatus.fromDict(fromDict['value'], 'overallStatus')

            if 'doors' in fromDict['value'] and fromDict['value']['doors'] is not None:
                for doorName in fromDict['value']['doors']:

                    doorDict = fromDict['value']['doors'][doorName]

                    if 'name' not in doorDict:
                        doorDict['name'] = doorName

                    if 'name' in doorDict:
                        if doorDict['name'] in self.doors:
                            self.doors[doorDict['name']].update(fromDict=doorDict)
                        else:
                            self.doors[doorDict['name']] = AccessStatus.Door(fromDict=doorDict, parent=self.doors)
                # for doorName in [doorName for doorName in self.doors.keys()
                #                  if doorName not in [door['name'] for door in fromDict['value']['doors'] if 'name' in door]]:
                #     # del self.doors[doorName]
                #     LOG.debug('deleted something here')
            else:
                self.doors.clear()
                self.doors.enabled = False

            if 'trunk' in fromDict['value']:
                doorDict = fromDict['value']['trunk']

                if 'name' not in doorDict:
                    doorDict['name'] = 'trunk'

                if 'name' in doorDict:
                    if doorDict['name'] in self.doors:
                        self.doors[doorDict['name']].update(fromDict=doorDict)
                    else:
                        self.doors[doorDict['name']] = AccessStatus.Door(fromDict=doorDict, parent=self.doors)

            if 'hood' in fromDict['value']:
                doorDict = fromDict['value']['hood']

                if 'name' not in doorDict:
                    doorDict['name'] = 'hood'

                if 'name' in doorDict:
                    if doorDict['name'] in self.doors:
                        self.doors[doorDict['name']].update(fromDict=doorDict)
                    else:
                        self.doors[doorDict['name']] = AccessStatus.Door(fromDict=doorDict, parent=self.doors)

            if 'windows' in fromDict['value'] and fromDict['value']['windows'] is not None:
                for windowName in fromDict['value']['windows']:

                    windowDict = { 'name' : windowName, 'status' : fromDict['value']['windows'][windowName] }

                    if 'name' in windowDict:
                        if windowDict['name'] in self.windows:
                            self.windows[windowDict['name']].update(fromDict=windowDict)
                        else:
                            self.windows[windowDict['name']] = AccessStatus.Window(fromDict=windowDict, parent=self.windows)
                # for windowName in [windowName for windowName in self.windows.keys()
                #                    if windowName not in [window['name']
                #                    for window in fromDict['value']['windows'] if 'name' in window]]:
                #     del self.doors[windowName]
            else:
                self.windows.clear()
                self.windows.enabled = False

            fromDict['value']['overallStatus'] = AccessControlState.OverallState.SAFE
            fromDict['value']['doorLockStatus'] = AccessControlState.LockState.LOCKED

            for doorName in self.doors.keys():
                door = self.doors[doorName]
                if door.lockState.value == AccessControlState.LockState.UNLOCKED:
                    fromDict['value']['doorLockStatus'] = AccessControlState.LockState.UNLOCKED

                if (door.openState.value == AccessControlState.OpenState.OPEN) or (door.lockState.value == AccessControlState.LockState.UNLOCKED):
                    fromDict['value']['overallStatus'] = AccessControlState.OverallState.UNSAFE

            for windowName in self.windows.keys():
                window = self.windows[windowName]
                if (window.openState.value == AccessControlState.OpenState.OPEN):
                    fromDict['value']['overallStatus'] = AccessControlState.OverallState.UNSAFE

            self.overallStatus.fromDict(fromDict['value'], 'overallStatus')
            self.doorLockStatus.fromDict(fromDict['value'], 'doorLockStatus')

            if 'engine' in fromDict['value']:
                self.engineStatus.fromDict(fromDict['value'], 'engine')

            if 'lights' in fromDict['value']:
                self.lightsStatus.fromDict(fromDict['value'], 'lights')

        else:
            self.overallStatus.enabled = False
            self.doors.clear()
            self.doors.enabled = False
            self.windows.clear()
            self.windows.enabled = False
            self.engineStatus.enabled = False
            self.lightsStatus.enabled = False

        super().update(fromDict=fromDict, ignoreAttributes=(ignoreAttributes + ['overallStatus', 'doors', 'windows']))

    def __str__(self):
        string = super().__str__()
        if self.overallStatus is not None and self.overallStatus.enabled:
            string += f'\n\tOverall Status: {self.overallStatus.value.value}'
        if len(self.doors) > 0:
            string += f'\n\tDoors: {len(self.doors)} items'
            for door in self.doors.values():
                string += f'\n\t\t{door}'
        if len(self.windows) > 0:
            string += f'\n\tWindows: {len(self.windows)} items'
            for window in self.windows.values():
                string += f'\n\t\t{window}'
        if self.engineStatus is not None and self.engineStatus.enabled:
            string += f'\n\tEngine: {self.engineStatus.value.value}'
        if self.lightsStatus is not None and self.lightsStatus.enabled:
            string += f'\n\tLights: {self.lightsStatus.value.value}'
        if self.doorLockStatus is not None and self.doorLockStatus.enabled:
            string += f'\n\tDoor locks: {self.doorLockStatus.value.value}'
        if self.overallStatus is not None and self.overallStatus.enabled:
            string += f'\n\tOverall Status: {self.overallStatus.value.value}'

        return string


    class Door(AddressableObject):
        def __init__(
            self,
            parent,
            fromDict=None,
        ):
            super().__init__(localAddress=None, parent=parent)
            self.openState = AddressableAttribute(
                localAddress='openState', parent=self, value=None, valueType=AccessControlState.OpenState)
            self.lockState = AddressableAttribute(
                localAddress='lockState', parent=self, value=None, valueType=AccessControlState.LockState)
            if fromDict is not None:
                self.update(fromDict)

        def update(self, fromDict):
            LOG.debug('Update door from dict')

            if 'name' in fromDict:
                self.id = fromDict['name']
                self.localAddress = self.id
            else:
                LOG.error('Door is missing name attribute')

            if 'locked' in fromDict:
                if fromDict['locked'] == "true":
                    self.lockState.setValueWithCarTime(
                        AccessControlState.LockState.LOCKED, lastUpdateFromCar=None, fromServer=True)
                elif fromDict['locked'] == "false":
                    self.lockState.setValueWithCarTime(
                        AccessControlState.LockState.UNLOCKED, lastUpdateFromCar=None, fromServer=True)
                else:
                    self.lockState.setValueWithCarTime(
                        AccessControlState.LockState.UNKNOWN, lastUpdateFromCar=None, fromServer=True)
            else:
                self.lockState.setValueWithCarTime(
                    AccessControlState.LockState.UNKNOWN, lastUpdateFromCar=None, fromServer=True)


            if 'open' in fromDict:
                if fromDict['open'] == "true":
                    self.openState.setValueWithCarTime(
                        AccessControlState.OpenState.OPEN, lastUpdateFromCar=None, fromServer=True)
                elif fromDict['open'] == "false":
                    self.openState.setValueWithCarTime(
                        AccessControlState.OpenState.CLOSED, lastUpdateFromCar=None, fromServer=True)
                else:
                    self.openState.setValueWithCarTime(
                        AccessControlState.OpenState.UNKNOWN, lastUpdateFromCar=None, fromServer=True)
            else:
                self.openState.setValueWithCarTime(
                    AccessControlState.OpenState.UNKNOWN, lastUpdateFromCar=None, fromServer=True)

            # Fudge because the Cupra Born always returns that the hood is unlocked, so we force it locked
            if self.id == 'hood':
                if self.openState.value == AccessControlState.OpenState.OPEN: 
                    self.lockState.setValueWithCarTime(
                        AccessControlState.LockState.UNLOCKED, lastUpdateFromCar=None, fromServer=True)
                else:
                    self.lockState.setValueWithCarTime(
                        AccessControlState.LockState.LOCKED, lastUpdateFromCar=None, fromServer=True)


            for key, value in {key: value for key, value in fromDict.items() if key not in ['locked', 'open', 'name']}.items():
                LOG.warning('%s: Unknown attribute %s with value %s', self.getGlobalAddress(), key, value)

        def __str__(self):
            returnString = f'{self.id}: '
            if self.openState.enabled:
                returnString += f'{self.openState.value.value}'  # pylint: disable=no-member
            if self.lockState.enabled:
                returnString += f', {self.lockState.value.value}'  # pylint: disable=no-member
            return returnString

    class Window(AddressableObject):
        def __init__(
            self,
            parent,
            fromDict=None,
        ):
            super().__init__(localAddress=None, parent=parent)
            self.openState = AddressableAttribute(
                localAddress='openState', parent=self, value=None, valueType=AccessControlState.OpenState)
            if fromDict is not None:
                self.update(fromDict)

        def update(self, fromDict):
            LOG.debug('Update window from dict')

            if 'name' in fromDict:
                self.id = fromDict['name']
                self.localAddress = self.id
            else:
                LOG.error('Window is missing name attribute')

            if 'status' in fromDict and fromDict['status']:
                if 'open' in fromDict['status']:
                    self.openState.setValueWithCarTime(
                        AccessControlState.OpenState.OPEN, lastUpdateFromCar=None, fromServer=True)
                elif 'closed' in fromDict['status']:
                    self.openState.setValueWithCarTime(
                        AccessControlState.OpenState.CLOSED, lastUpdateFromCar=None, fromServer=True)
                elif 'unsupported' in fromDict['status']:
                    self.openState.setValueWithCarTime(AccessControlState.OpenState.UNSUPPORTED, lastUpdateFromCar=None)
                elif 'invalid' in fromDict['status']:
                    self.openState.setValueWithCarTime(AccessControlState.OpenState.INVALID, lastUpdateFromCar=None)
                else:
                    self.openState.setValueWithCarTime(
                        AccessControlState.OpenState.UNKNOWN, lastUpdateFromCar=None, fromServer=True)
                    LOG.warning('No unsupported window status: %s was provided, please report this as a bug', fromDict['status'])
            else:
                self.openState.enabled = False

            for key, value in {key: value for key, value in fromDict.items() if key not in ['name', 'status']}.items():
                LOG.warning('%s: Unknown attribute %s with value %s', self.getGlobalAddress(), key, value)

        def __str__(self):
            return f'{self.id}: {self.openState.value.value}'  # pylint: disable=no-member
