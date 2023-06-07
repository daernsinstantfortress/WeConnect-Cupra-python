import argparse
import logging

from weconnect_cupra import weconnect_cupra
from weconnect_cupra.service import Service


def main():
    """ Simple example showing how to retrieve all vehciles from the account """
    parser = argparse.ArgumentParser(
        prog='allVehciles',
        description='Example retrieving all vehciles in the account')
    parser.add_argument('-u', '--username', help='Username of Cupra app id', required=True)
    parser.add_argument('-p', '--password', help='Password of Cupra app id', required=True)
    parser.add_argument('-d', '--debug', help='Turn on debug logging', default=False, action='store_true')
    parser.add_argument('--service', help='Service to connect to. One of WeConnect, MyCupra', required=True)

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    print('#  Initialize WeConnect')
    weConnect = weconnect_cupra.WeConnect(username=args.username, password=args.password,
        updateAfterLogin=False, loginOnInit=False,
        service=Service(args.service))

    print('#  Login')
    weConnect.login()
    print('#  update')
    weConnect.update()
    print('#  Report')
    for _, vehicle in weConnect.vehicles.items():
        print(vehicle)
    print('#  done')


if __name__ == '__main__':
    main()
