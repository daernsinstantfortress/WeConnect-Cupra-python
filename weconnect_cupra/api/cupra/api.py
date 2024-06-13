from __future__ import annotations
from typing import Dict, List, Set, Tuple, Callable, Any, Optional
import logging
from datetime import datetime

from weconnect_cupra.addressable import AddressableObject, AddressableDict
from weconnect_cupra.fetch import Fetcher
from weconnect_cupra.addressable import AddressableDict
from weconnect_cupra.errors import RetrievalError
from weconnect_cupra.api.cupra.domain import Domain
from weconnect_cupra.api.cupra.elements.vehicle import Vehicle
from weconnect_cupra.api.cupra.elements.charging_station import ChargingStation


LOG = logging.getLogger("weconnect_cupra")


class CupraApi:
    def __init__(self, weconnect_cupra: AddressableObject, fetcher: Fetcher, enableTracker: bool = False, fixAPI: bool = True):
        # https://github.com/evcc-io/evcc/blob/7abee00aa98a29d46d9d3c2a7a16a601558129b7/vehicle/seat/cupra/api.go
        self.base_url = 'https://ola.prod.code.seat.cloud.vwgroup.com'
        self.__vehicles: AddressableDict[str, Vehicle] = AddressableDict(localAddress='vehicles', parent=weconnect_cupra)
        self.__stations: AddressableDict[str, ChargingStation] = AddressableDict(localAddress='chargingStations', parent=weconnect_cupra)
        self.__fetcher: Fetcher = fetcher
        self.__enableTracker: bool = enableTracker
        self.fixAPI: bool = fixAPI

    @property
    def vehicles(self) -> AddressableDict[str, Vehicle]:
        return self.__vehicles

    @property
    def stations(self) -> AddressableDict[str, ChargingStation]:
        return self.__stations

    def update(self, updateCapabilities: bool = True, updatePictures: bool = True, force: bool = False,
               selective: Optional[list[Domain]] = None) -> \
            Tuple[AddressableDict[str, Vehicle], AddressableDict[str, ChargingStation]]:
        self.updateVehicles(updateCapabilities=updateCapabilities, updatePictures=updatePictures, force=force, selective=selective)
        return (self.__vehicles, self.__stations)

    def updateVehicles(self, updateCapabilities: bool = True, updatePictures: bool = True, force: bool = False,  # noqa: C901
                       selective: Optional[list[Domain]] = None) -> None:
        url = f'{self.base_url}/v2/users/{self.__fetcher.user_id}/garage/vehicles'
        data = self.__fetcher.fetchData(url, force)
        if data is not None and 'vehicles' in data and data['vehicles']:
            vins: List[str] = []
            for vehicleDict in data['vehicles']:
                if 'vin' not in vehicleDict:
                    break
                vin: str = vehicleDict['vin']
                vins.append(vin)
                try:
                    if vin not in self.__vehicles:
                        vehicle = Vehicle(
                            fetcher=self.__fetcher,
                            vin=vin,
                            parent=self.__vehicles,
                            fromDict=vehicleDict,
                            fixAPI=self.fixAPI,
                            updateCapabilities=updateCapabilities,
                            updatePictures=updatePictures,
                            selective=selective,
                            enableTracker=self.__enableTracker)
                        self.__vehicles[vin] = vehicle
                    else:
                        self.__vehicles[vin].update(
                            fromDict=vehicleDict,
                            updateCapabilities=updateCapabilities,
                            updatePictures=updatePictures,
                            selective=selective)
                except RetrievalError as retrievalError:
                    LOG.error('Failed to retrieve data for VIN %s: %s', vin, retrievalError)
                    LOG.error(retrievalError)
            # delete those vins that are not anymore available
            for vin in [vin for vin in self.__vehicles if vin not in vins]:
                del self.__vehicles[vin]
