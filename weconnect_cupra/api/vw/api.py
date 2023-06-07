from __future__ import annotations
from typing import List, Tuple, Optional
import logging
import locale

from weconnect_cupra.addressable import AddressableDict, AddressableObject
from weconnect_cupra.errors import RetrievalError
from weconnect_cupra.api.vw.domain import Domain
from weconnect_cupra.api.vw.elements.vehicle import Vehicle
from weconnect_cupra.api.vw.elements.charging_station import ChargingStation
from weconnect_cupra.fetch import Fetcher


LOG = logging.getLogger("weconnect_cupra")


class VwApi:
    def __init__(self, weconnect_cupra: AddressableObject, fetcher: Fetcher, enableTracker: bool = False, fixAPI: bool = True):
        self.base_url = 'https://mobileapi.apps.emea.vwapps.io'
        self.__vehicles: AddressableDict[str, Vehicle] = AddressableDict(localAddress='vehicles', parent=weconnect_cupra)
        self.__stations: AddressableDict[str, ChargingStation] = AddressableDict(localAddress='chargingStations', parent=weconnect_cupra)
        self.__fetcher: Fetcher = fetcher
        self.__enableTracker: bool = enableTracker
        self.fixAPI: bool = fixAPI

        # Used for charging station support
        # Public api used by weconnect_cupra-mqtt
        self.latitude: Optional[float] = None
        # Public api used by weconnect_cupra-mqtt
        self.longitude: Optional[float] = None
        # Public api used by weconnect_cupra-mqtt
        self.searchRadius: Optional[int] = None
        self.market: Optional[str] = None
        self.useLocale: Optional[str] = locale.getlocale()[0]


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
        self.updateChargingStations(force=force)
        return (self.__vehicles, self.__stations)

    def updateVehicles(self, updateCapabilities: bool = True, updatePictures: bool = True, force: bool = False,  # noqa: C901
                       selective: Optional[list[Domain]] = None) -> None:
        url = f'{self.base_url}/vehicles'
        data = self.__fetcher.fetchData(url, force)
        if data is not None:
            if 'data' in data and data['data']:
                vins: List[str] = []
                for vehicleDict in data['data']:
                    if 'vin' not in vehicleDict:
                        break
                    vin: str = vehicleDict['vin']
                    vins.append(vin)
                    try:
                        if vin not in self.__vehicles:
                            vehicle = Vehicle(fetcher=self.__fetcher, vin=vin, parent=self.__vehicles, fromDict=vehicleDict, fixAPI=self.fixAPI,
                                              updateCapabilities=updateCapabilities, updatePictures=updatePictures, selective=selective,
                                              enableTracker=self.__enableTracker)
                            self.__vehicles[vin] = vehicle
                        else:
                            self.__vehicles[vin].update(fromDict=vehicleDict, updateCapabilities=updateCapabilities, updatePictures=updatePictures,
                                                        selective=selective)
                    except RetrievalError as retrievalError:
                        LOG.error('Failed to retrieve data for VIN %s: %s', vin, retrievalError)
                # delete those vins that are not anymore available
                for vin in [vin for vin in self.__vehicles if vin not in vins]:
                    del self.__vehicles[vin]

    def updateChargingStations(self, force: bool = False) -> None:  # noqa: C901 # pylint: disable=too-many-branches
        if self.latitude is not None and self.longitude is not None:
            url: str = f'{self.base_url}/charging-stations/v2?latitude={self.latitude}&longitude={self.longitude}'
            if self.market is not None:
                url += f'&market={self.market}'
            if self.useLocale is not None:
                url += f'&locale={self.useLocale}'
            if self.searchRadius is not None:
                url += f'&searchRadius={self.searchRadius}'
            if self.__fetcher.user_id is not None:
                url += f'&userId={self.__fetcher.user_id}'
            data = self.__fetcher.fetchData(url, force)
            if data is not None:
                if 'chargingStations' in data and data['chargingStations']:
                    ids: List[str] = []
                    for stationDict in data['chargingStations']:
                        if 'id' not in stationDict:
                            break
                        stationId: str = stationDict['id']
                        ids.append(stationId)
                        if stationId not in self.__stations:
                            station: ChargingStation = ChargingStation(weConnect=self, stationId=stationId, parent=self.__stations, fromDict=stationDict,
                                                                       fixAPI=self.fixAPI)
                            self.__stations[stationId] = station
                        else:
                            self.__stations[stationId].update(fromDict=stationDict)
                    # delete those vins that are not anymore available
                    for stationId in [stationId for stationId in ids if stationId not in self.__stations]:
                        del self.__stations[stationId]

    def getChargingStations(self, latitude, longitude, searchRadius=None, market=None, useLocale=None,  # noqa: C901
                            force=False) -> AddressableDict[str, ChargingStation]:
        chargingStationMap: AddressableDict[str, ChargingStation] = AddressableDict(localAddress='', parent=None)
        url: str = f'{self.base_url}/charging-stations/v2?latitude={latitude}&longitude={longitude}'
        if market is not None:
            url += f'&market={market}'
        if useLocale is not None:
            url += f'&locale={useLocale}'
        if searchRadius is not None:
            url += f'&searchRadius={searchRadius}'
        if self.__fetcher.user_id is not None:
            url += f'&userId={self.__fetcher.user_id}'
        data = self.__fetcher.fetchData(url, force)
        if data is not None:
            if 'chargingStations' in data and data['chargingStations']:
                for stationDict in data['chargingStations']:
                    if 'id' not in stationDict:
                        break
                    stationId: str = stationDict['id']
                    station: ChargingStation = ChargingStation(weConnect=self, stationId=stationId, parent=chargingStationMap, fromDict=stationDict,
                                                               fixAPI=self.fixAPI)
                    chargingStationMap[stationId] = station
        return chargingStationMap

    def setChargingStationSearchParameters(self, latitude: float, longitude: float, searchRadius: Optional[int] = None, market: Optional[str] = None,
                                           useLocale: Optional[str] = locale.getlocale()[0]) -> None:
        self.latitude = latitude
        self.longitude = longitude
        self.searchRadius = searchRadius
        self.market = market
        self.useLocale = useLocale
