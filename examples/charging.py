import argparse
import logging

from weconnect_cupra import weconnect_cupra
from weconnect_cupra.service import Service


def main():
    """ Simple example showing how to start climatization in a vehicle by providing the VIN as a parameter """
    parser = argparse.ArgumentParser(
        prog='climatization',
        description='Example starting climatizaton')
    parser.add_argument('-u', '--username', help='Username of Volkswagen id', required=True)
    parser.add_argument('-p', '--password', help='Password of Volkswagen id', required=True)
    parser.add_argument('-d', '--debug', help='Turn on debug logging', default=False, action='store_true')
    parser.add_argument('--service', help='Service to connect to. One of WeConnect, MyCupra', required=True)
    parser.add_argument('--vin', help='VIN of the vehicle to set charging', required=True)
    # Properties that modify car state
    parser.add_argument('--state', help='Charging state. One of start, stop', required=False)
    parser.add_argument('--target-soc', help='Target state of charge for car', required=False)
    parser.add_argument('--auto-unlock-plug-when-charged', help='Auto unlock plug when charged. One of permanent or off', required=False)
    parser.add_argument('--max-charge-current-ac', help='Set max charge current level. One of maximum or reduced', required=False)

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    # Construct based on service
    print('#  Initialize')
    service = Service(args.service)
    if service == Service.WE_CONNECT:
        from weconnect_cupra.elements.control_operation import ControlOperation
        from weconnect_cupra.api.vw.domain import Domain
        from weconnect_cupra.api.vw.elements.enums import MaximumChargeCurrent, UnlockPlugState
    elif service == Service.MY_CUPRA:
        from weconnect_cupra.elements.control_operation import ControlOperation
        from weconnect_cupra.api.cupra.domain import Domain
        from weconnect_cupra.api.cupra.elements.enums import MaximumChargeCurrent, UnlockPlugState
    weConnect = weconnect_cupra.WeConnect(username=args.username, password=args.password,
        updateAfterLogin=False, loginOnInit=False,
        service=service)

    print('#  Login')
    weConnect.login()
    print('#  Update')
    weConnect.update()

    print('#  Report')
    for vin, vehicle in weConnect.vehicles.items():
        if vin == args.vin:

            if "charging" in vehicle.domains \
                and 'chargingSettings' in vehicle.domains["charging"] \
                and vehicle.domains["charging"]["chargingSettings"].enabled:
                print(vehicle.domains["charging"]["chargingSettings"])

            if "charging" in vehicle.domains \
                and 'chargingStatus' in vehicle.domains["charging"] \
                and vehicle.domains["charging"]["chargingStatus"].enabled:
                print(vehicle.domains["charging"]["chargingStatus"])

            if "charging" in vehicle.domains \
                and 'batteryStatus' in vehicle.domains["charging"] \
                and vehicle.domains["charging"]["batteryStatus"].enabled:
                print(vehicle.domains["charging"]["batteryStatus"])

            # Maybe change charging state
            if args.state:
                if vehicle.controls.chargingControl is not None and vehicle.controls.chargingControl.enabled:
                    print('#  set charging')
                    vehicle.controls.chargingControl.value = ControlOperation(value=args.state)
                else:
                    print('# Charging not supported')
                
            # Maybe change target SoC
            if args.target_soc:
                if 'charging' in vehicle.domains \
                        and vehicle.domains['charging']["chargingSettings"].enabled \
                        and vehicle.domains['charging']["chargingSettings"].targetSOC_pct.enabled:
                    print('#  set charging Target SoC')
                    vehicle.domains['charging']["chargingSettings"].targetSOC_pct.value = float(args.target_soc)
                else:
                    print('# Charging not supported')

            # Maybe change autoUnlockPlugWhenCharged
            if args.auto_unlock_plug_when_charged:
                if 'charging' in vehicle.domains \
                        and vehicle.domains['charging']["chargingSettings"].enabled \
                        and vehicle.domains['charging']["chargingSettings"].autoUnlockPlugWhenCharged.enabled:
                    print('#  set autoUnlockPlugWhenCharged')
                    vehicle.domains['charging']["chargingSettings"].autoUnlockPlugWhenCharged.value = UnlockPlugState(args.auto_unlock_plug_when_charged)
                else:
                    print('# Charging not supported')

            # Maybe change maxChargeCurrentAC
            if args.max_charge_current_ac:
                if 'charging' in vehicle.domains \
                        and vehicle.domains['charging']["chargingSettings"].enabled \
                        and vehicle.domains['charging']["chargingSettings"].maxChargeCurrentAC.enabled:
                    print('#  set maxChargeCurrentAC')
                    vehicle.domains['charging']["chargingSettings"].maxChargeCurrentAC.value = MaximumChargeCurrent(args.max_charge_current_ac)
                else:
                    print('# Charging not supported')

    print('#  done')

if __name__ == '__main__':
    main()
