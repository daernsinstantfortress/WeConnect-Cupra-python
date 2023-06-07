import argparse
import logging

from weconnect_cupra import weconnect_cupra
from weconnect_cupra.service import Service
from weconnect_cupra.elements.control_operation import ControlOperation

def main():
    """ Simple example showing how to start climatization in a vehicle by providing the VIN as a parameter """
    parser = argparse.ArgumentParser(
        prog='climatization',
        description='Example starting climatizaton')
    parser.add_argument('-u', '--username', help='Username of Volkswagen id', required=True)
    parser.add_argument('-p', '--password', help='Password of Volkswagen id', required=True)
    parser.add_argument('--service', help='Service to connect to. One of WeConnect, MyCupra', required=True)
    parser.add_argument('--vin', help='VIN of the vehicle to set climatization', required=True)
    parser.add_argument('--state', help='Climatization state. One of start, stop', required=False)

    args = parser.parse_args()

    # logging.basicConfig(level=logging.DEBUG)

    # Construct based on service
    print('#  Initialize')
    service = Service(args.service)
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
            if "climatisation" in vehicle.domains \
                    and "climatisationStatus" in vehicle.domains["climatisation"] \
                    and vehicle.domains["climatisation"]["climatisationStatus"].enabled:
                print(vehicle.domains["climatisation"]["climatisationStatus"])

            if "climatisation" in vehicle.domains \
                    and "climatisationSettings" in vehicle.domains["climatisation"] \
                    and vehicle.domains["climatisation"]["climatisationSettings"].enabled:
                print(vehicle.domains["climatisation"]["climatisationSettings"])
            
            if args.state:
                if vehicle.controls.climatizationControl is not None and vehicle.controls.climatizationControl.enabled:
                    print('#  set climatization')
                    vehicle.controls.climatizationControl.value = ControlOperation(value=args.state)
                else:
                    print('# Climatization not supported')

    print('#  done')

if __name__ == '__main__':
    main()
