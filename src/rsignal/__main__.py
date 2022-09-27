import argparse

import yaml

from . import RSignalServer

parser = argparse.ArgumentParser(prog='RSignal', description='RSignal command line interface.')
parser.set_defaults(which='service')
parser.add_argument('-c', '--config', metavar='File', type=str, required=False, help='Path to the configuration file.')

subparsers = parser.add_subparsers(help='sub-command help')

runserver_parser = subparsers.add_parser('runserver', help='Run server manually.')
runserver_parser.set_defaults(which='runserver')
runserver_parser.add_argument('-i', '--host', metavar='[Host Address]', type=str, required=False, default='localhost', help='Host address')
runserver_parser.add_argument('-p', '--port', metavar='[Port Number]', type=int, required=False, default=5555, help='Port number')
runserver_parser.add_argument('-l', '--log-level', metavar='[log-level]', type=bool, required=False, default=True, help='Log level includes: [debug | info | warn | error | fatal | critical]')
runserver_parser.add_argument('-cert', '--certificate', metavar='[file]', type=str, required=False, default=None, help='Certificate file')
runserver_parser.add_argument('-k', '--key', metavar='[file]', type=str, required=False, default=None, help='Key file')

args = parser.parse_args()

match args.which:
    case 'runserver':
        ssl_context = (args.certificate, args.key) if args.certificate and args.key else None
        server = RSignalServer(args.host, args.port, ssl_context=ssl_context)
        server.run()
    case 'service':
        if args.config is not None:
            with open(args.config, "r") as stream:
                try:
                    configuration = yaml.safe_load(stream)
                except yaml.YAMLError as exc:
                    print(exc)
            server = RSignalServer(
                host=configuration.get("host"),
                port=configuration.get("port"),
                ssl_context=(configuration.get("certificate"), configuration.get("key")) if configuration.get("certificate") and configuration.get("key") else None
            )
            server.run()
    case other:
        parser.print_help()
