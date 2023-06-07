"""Unit tests for Cupra service"""

from weconnect import weconnect
from weconnect.api.cupra.elements.climatization_settings import ClimatizationSettings
from weconnect.api.cupra.elements.climatization_status import ClimatizationStatus
from weconnect.api.cupra.elements.enums import ClimatizationState
from weconnect.api.cupra.elements.odometer_measurement import OdometerMeasurement
from weconnect.service import Service
from weconnect.addressable import AddressableAttribute, AddressableDict, ChangeableAttribute
from weconnect.api.cupra.elements.battery_status import BatteryStatus
from weconnect.api.cupra.elements.charging_settings import ChargingSettings
from weconnect.api.cupra.elements.charging_status import ChargingStatus
from weconnect.api.cupra.elements.vehicle import Vehicle
from weconnect.api.cupra.domain import Domain


def test_vehicles_element_minimal_construction_not_charging():
    # Given
    range_value = 280.0
    charge_level = 80.0
    mileage_km = 1451.0
    charging_remaining_time = 0
    target_charge = 100
    target_temperature_k = 295.15
    climate_remaining_time = 10

    class MockFetcher:
        base_url = 'https://example.com'
        user_id = 'USERID'

        def fetchData(self, url, force=None):
            # url: str = f'{self.fetcher.base_url}/v2/users/{self.fetcher.user_id}/vehicles/{self.vin.value}/mycar'
            return {
                "engines": {
                    "primary": {
                        "type": "EV",
                        "fuelType": "EV",
                        "range": {"value": range_value, "unit": "Km"},
                        "level": charge_level
                    },
                    "secondary": {
                        "type": None,
                        "fuelType": None,
                        "range": None,
                        "level": None
                    }
                },
                "measurements": {
                    "mileageKm": mileage_km
                },
                "services": {
                    "charging": {
                        "status": "NotReadyForCharging",
                        "targetPct": target_charge,
                        "chargeMode": "manual",
                        "active": False,
                        "remainingTime": charging_remaining_time,
                        "progressBarPct": 100.0
                    },
                    "climatisation": {
                        "status": "Off",
                        "targetTemperatureKelvin": target_temperature_k,
                        "active": False,
                        "remainingTime": climate_remaining_time,
                        "progressBarPct": 0.0
                    }
                }
            }
    fetcher = MockFetcher()
    vehicleDict = {
        'vin': 'VIN',
        'userRole': Vehicle.User.Role.PRIMARY_USER.value,
        'enrollmentStatus': Vehicle.User.EnrollmentStatus.COMPLETED.value,
        'userRoleStatus': Vehicle.User.UserRoleStatus.ENABLED.value,
        'vehicleNickname': 'CUPRA Born',
    }
    parent: AddressableDict[str, Vehicle] = AddressableDict(localAddress='xxx', parent=None)
    vehicle = Vehicle(
        fetcher=fetcher,
        vin='VINVINVINVINVIN',
        parent=parent,
        fromDict=vehicleDict,
        fixAPI=True,
        updateCapabilities=True,
        updatePictures=False,
        selective=None,
        enableTracker=False)
    # When
    # Note: update() is called in the constructor
    # Then
    assert vehicle.vin.value == vehicleDict['vin']
    assert vehicle.role.value.value == vehicleDict['userRole']
    assert vehicle.enrollmentStatus.value.value == vehicleDict['enrollmentStatus']
    assert vehicle.userRoleStatus.value.value == vehicleDict['userRoleStatus']
    assert vehicle.nickname.value == vehicleDict['vehicleNickname']
    # We don't have these for Cupra
    # assert vehicle.model.value == vehicleDict['model']
    # assert vehicle.devicePlatform.value == vehicleDict['devicePlatform']
    # assert vehicle.brandCode.value == vehicleDict['brandCode']
    assert vehicle.domains[Domain.MEASUREMENTS.value]['mileageKm'].odometer.value == mileage_km
    charging_status: ChargingStatus = vehicle.domains[Domain.CHARGING.value]['chargingStatus']
    assert charging_status.chargingState.value == ChargingStatus.ChargingState.NOT_READY_FOR_CHARGING
    assert charging_status.chargeMode.value == ChargingStatus.ChargeMode.MANUAL
    assert charging_status.remainingChargingTimeToComplete_min.value == charging_remaining_time
    # We don't have these for Cupra
    # charging_status.chargePower_kW
    # charging_status.chargeRate_kmph
    # charging_status.chargeType
    # charging_status.chargingSettings
    battery_status: BatteryStatus = vehicle.domains[Domain.CHARGING.value]['batteryStatus']
    assert battery_status.cruisingRangeElectric_km.value == range_value
    assert battery_status.currentSOC_pct.value == charge_level

    charging_settings: ChargingSettings = vehicle.domains[Domain.CHARGING.value]['chargingSettings']
    assert charging_settings.targetSOC_pct.value == target_charge

    climatization_settings: ClimatizationSettings = vehicle.domains[Domain.CLIMATISATION.value]['climatisationSettings']
    assert climatization_settings.targetTemperature_K.value == target_temperature_k
    assert climatization_settings.targetTemperature_C.value == target_temperature_k - 273.15
    assert climatization_settings.targetTemperature_F.value == 1.8 * (target_temperature_k - 273) + 32

    climatization_status: ClimatizationStatus = vehicle.domains[Domain.CLIMATISATION.value]['climatisationStatus']
    assert climatization_status.climatisationState.value == ClimatizationState.OFF
    # Note when fixApi == True, then this should be 0 if climatisationState == ClimatizationStatus.ClimatizationState.OFF
    assert climatization_status.remainingClimatisationTime_min.value == 0


def test_vehicles_element_minimal_construction_charging():
    # Given
    range_value = 250.0
    charge_level = 78.0
    mileage_km = 1471.0
    charging_remaining_time = 355
    target_charge = 78.0
    status_charging = "Charging"

    class MockFetcher:
        base_url = 'https://example.com'
        user_id = 'USERID'
        index = -1

        def fetchData(self, url, force=None):
            # url: str = f'{self.fetcher.base_url}/v2/users/{self.fetcher.user_id}/vehicles/{self.vin.value}/mycar'
            responses = [{
                "engines": {
                    "primary": {
                        "type": "EV",
                        "fuelType": "EV",
                        "range": {"value": range_value, "unit": "Km"},
                        "level": charge_level
                    },
                    "secondary": {
                        "type": None,
                        "fuelType": None,
                        "range": None,
                        "level": None
                    }
                },
                "measurements": {
                    "mileageKm": mileage_km
                },
                "services": {
                    "charging": {
                        "status": status_charging,
                        "targetPct": target_charge,
                        "chargeMode": "manual",
                        "active": True,
                        "remainingTime": charging_remaining_time,
                        "progressBarPct": 100.0
                    },
                    "climatisation": {
                        "status": "Off",
                        "targetTemperatureKelvin": 295.15,
                        "active": False,
                        "remainingTime": 0,
                        "progressBarPct": 0.0
                    }
                }
            },
                {
                'settings': {
                    "targetSoc_pct": 78
                }
            },
                {
                'status': {
                    'status': None,
                    'charging': {
                        'remainingChargingTimeToComplete_min': 355,
                        "chargeMode": ChargingStatus.ChargeMode.MANUAL,
                        "chargePower_kW": 0.0,
                        "chargeRate_kmph": 0.0
                    }
                }
            } ]
            self.index += 1
            return responses[self.index]
    fetcher = MockFetcher()
    vehicleDict = {
        'vin': 'VIN',
        'userRole': Vehicle.User.Role.PRIMARY_USER.value,
        'enrollmentStatus': Vehicle.User.EnrollmentStatus.COMPLETED.value,
        'userRoleStatus': Vehicle.User.UserRoleStatus.ENABLED.value,
        'vehicleNickname': 'CUPRA Born',
    }
    parent: AddressableDict[str, Vehicle] = AddressableDict(localAddress='xxx', parent=None)
    vehicle = Vehicle(
        fetcher=fetcher,
        vin='VINVINVINVINVIN',
        parent=parent,
        fromDict=vehicleDict,
        fixAPI=True,
        updateCapabilities=True,
        updatePictures=False,
        selective=None,
        enableTracker=False)
    # When
    # Note: update() is called in the constructor
    # Then
    assert vehicle.vin.value == vehicleDict['vin']
    assert vehicle.role.value.value == vehicleDict['userRole']
    assert vehicle.enrollmentStatus.value.value == vehicleDict['enrollmentStatus']
    assert vehicle.userRoleStatus.value.value == vehicleDict['userRoleStatus']
    assert vehicle.nickname.value == vehicleDict['vehicleNickname']
    # We don't have these for Cupra
    # assert vehicle.model.value == vehicleDict['model']
    # assert vehicle.devicePlatform.value == vehicleDict['devicePlatform']
    # assert vehicle.brandCode.value == vehicleDict['brandCode']
    assert vehicle.domains[Domain.MEASUREMENTS.value]['mileageKm'].odometer.value == mileage_km
    charging_status: ChargingStatus = vehicle.domains[Domain.CHARGING.value]['chargingStatus']
    assert charging_status.chargingState.value == ChargingStatus.ChargingState.CHARGING
    assert charging_status.chargeMode.value == ChargingStatus.ChargeMode.MANUAL
    assert charging_status.remainingChargingTimeToComplete_min.value == charging_remaining_time
    # We don't have these for Cupra
    # charging_status.chargePower_kW
    # charging_status.chargeRate_kmph
    # charging_status.chargeType
    # charging_status.chargingSettings
    battery_status: BatteryStatus = vehicle.domains[Domain.CHARGING.value]['batteryStatus']
    assert battery_status.cruisingRangeElectric_km.value == range_value
    assert battery_status.currentSOC_pct.value == charge_level

    charging_settings: ChargingSettings = vehicle.domains[Domain.CHARGING.value]['chargingSettings']
    assert charging_settings.targetSOC_pct.value == target_charge


def test_construct_weconnect_like_ha_integration():
    # When
    weconnect.WeConnect(
        username="username",
        password="password",
        service=Service('MyCupra'),
        updateAfterLogin=False,
        loginOnInit=False,
    )
    # Then just make sure we did construction without an error
    assert True


def test_climate_status():
    # Given
    class MockFetcher:
        called = False

        def post(self, url, *args):
            self.called = url

        def fetchData(self, url, force=None):
            return {
                'settings': {}
            }

    class MockVehicle:
        fetcher = MockFetcher()
        vin: AddressableAttribute[str] = AddressableAttribute(
            localAddress='vin', parent=None, value='VINVINVIN', valueType=str)
    vehicle = MockVehicle()
    climate_dict = {
    }
    climate = ClimatizationStatus(
        vehicle=vehicle,
        parent=None,
        statusId='climatisationStatus',
        fromDict=climate_dict,
    )
    # When
    climate.climatisationState.value = ClimatizationState.COOLING
    # Then
    assert climate.climatisationState.value == ClimatizationState.COOLING
    assert vehicle.fetcher.called


def test_changeable_attribute():
    # Given
    class MockResponse:
        status_code = 200

        def json(self):
            return {}

    class MockFetcher:
        called = False
        put_called = False

        def post(self, url, *args):
            self.called = url

        def fetchData(self, url, force=None):
            return {
                'settings': {}
            }

        def put(self, url, json, headers, *args):
            self.put_called = url
            return MockResponse()

    class MockVehicle:
        fetcher = MockFetcher()
        vin: AddressableAttribute[str] = AddressableAttribute(
            localAddress='vin', parent=None, value='VINVINVIN', valueType=str)
    vehicle = MockVehicle()
    climate_dict = {

    }
    climate = ClimatizationSettings(
        vehicle=vehicle,
        parent=None,
        statusId='climatisationSettings',
        fromDict=climate_dict,
    )
    # When
    climate.targetTemperature_K.value = 100
    # Then
    assert climate.targetTemperature_K.value == 100
    # There doesn't seem to be a way to set temp via the api
    assert vehicle.fetcher.called == False

def test_odometer_measurement():
    class MockVehicle:
        fetcher = None
        vin: AddressableAttribute[str] = AddressableAttribute(
            localAddress='vin', parent=None, value='VINVINVIN', valueType=str)
    vehicle = MockVehicle()
    od = OdometerMeasurement(vehicle=vehicle, parent=None, statusId='odometer')
    od.update(999)
    assert od.odometer.value == 999