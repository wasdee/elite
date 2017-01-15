#!/usr/bin/env python3
import argparse
import os
import json
import subprocess
from time import sleep

import yaml

from ..libraries.dock_builder import get_dock_plist_path, DockBuilder


# Colours
BOLD = '\033[1m'
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
ENDC = '\033[0m'


def main():
    # Create the argument parser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    # Create the parser for the build sub-command
    build_parser = subparsers.add_parser(
        'build', help='build the dock plist using the config provided'
    )
    build_parser.add_argument('config_path', help='the file path of the config to use')

    # Create the parser for the extract sub-command
    extract_parser = subparsers.add_parser(
        'extract', help='extract the dock plist into a config file'
    )
    extract_parser.add_argument(
        '-f', '--format', choices=['json', 'yaml'], default='yaml',
        help='the format to extract your config to'
    )
    extract_parser.add_argument('config_path', help='the file path to extract the config to')

    # Create the parser for the compare sub-command
    compare_parser = subparsers.add_parser(
        'compare', help='compare the dock plist with the config'
    )
    compare_parser.add_argument('config_path', help='the file path of the config to compare')

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.error('please specify an action to perform')

    print()
    print(f'{BOLD}Dock Builder{ENDC}')
    print()

    # Determine the location of the Dock plist file
    dock_plist_path = get_dock_plist_path()

    print(f'{BLUE}Using Dock plist {dock_plist_path}{ENDC}')

    # Build
    if args.command == 'build':
        with open(args.config_path) as f:
            config = yaml.load(f)

        print(f'{BLUE}Rebuilding the Dock plist{ENDC}')
        dock_builder = DockBuilder(
            dock_plist_path, config.get('app_layout', []), config.get('other_layout', [])
        )
        dock_builder.build()

        # Restart the Dock so that the new plist file can be utilised
        print(f'{BLUE}Restarting the Dock to apply the new plist{ENDC}')
        subprocess.call(['killall', 'Dock'])

        print(
            f'{GREEN}Successfully build the Dock layout defined in {args.config_path}{ENDC}'
        )

    # Extract
    elif args.command == 'extract':
        dock_builder = DockBuilder(dock_plist_path)
        dock_builder.extract()

        layout = {
            'app_layout': dock_builder.app_layout,
            'other_layout': dock_builder.other_layout
        }

        with open(args.config_path, 'w') as f:
            if args.format == 'yaml':
                f.write(yaml.safe_dump(layout, default_flow_style=False, explicit_start=True))
            else:
                json.dump(layout, f, indent=2)

        print(f'{GREEN}Successfully wrote Dock config to {args.config_path}{ENDC}')

    # Compare
    elif args.command == 'compare':
        with open(args.config_path) as f:
            config = yaml.load(f)

        dock_builder = DockBuilder(dock_plist_path)
        dock_builder.extract()

        extracted_layout = {
            'app_layout': dock_builder.app_layout,
            'other_layout': dock_builder.other_layout
        }

        dock_builder = DockBuilder(
            dock_plist_path, config.get('app_layout', []), config.get('other_layout', [])
        )
        config_layout = {
            'app_layout': dock_builder.app_layout,
            'other_layout': dock_builder.other_layout
        }

        if config_layout == extracted_layout:
            print(f'{GREEN}The configuration provided is identical to the current layout{ENDC}')
        else:
            print(f'{RED}The configuration provided is different to the current layout{ENDC}')
            print()
            exit(1)

    print()


if __name__ == '__main__':
    main()
