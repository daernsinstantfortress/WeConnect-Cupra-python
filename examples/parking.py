import argparse
import logging

from weconnect_cupra import weconnect_cupra
from weconnect_cupra.service import Service


def main():
    """ Simple example showing how to get parking position"""
    parser = argparse.ArgumentParser(
        prog='climatization',
        description='Example starting climatizaton')
    parser.add_argument('-u', '--username', help='Username of Volkswagen id', required=True)
    parser.add_argument('-p', '--password', help='Password of Volkswagen id', required=True)
    parser.add_argument('-d', '--debug', help='Turn on debug logging', default=False, action='store_true')
    parser.add_argument('--service', help='Service to connect to. One of WeConnect, MyCupra', required=True)
    parser.add_argument('--vin', help='VIN of the vehicle to set charging', required=True)

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

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

            if "parking" in vehicle.domains \
                and 'parkingPosition' in vehicle.domains["parking"] \
                and vehicle.domains["parking"]["parkingPosition"].enabled:
                print(vehicle.domains["parking"]["parkingPosition"])

    print('#  done')

if __name__ == '__main__':
    main()
