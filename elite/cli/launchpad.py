#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from time import sleep

from ruamel.yaml import YAML

from ..libraries.launchpad_builder import LaunchpadBuilder, get_launchpad_db_dir


# Configure YAML parsing to be safe by default
yaml = YAML(typ='safe')

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
        'build', help='build the launchpad db using the config provided'
    )
    build_parser.add_argument(
        '--skip-db-rebuild', dest='skip_db_rebuild', default=False, action='store_true',
        help='do not rebuild the db before building it again'
    )
    build_parser.add_argument('config_path', help='the file path of the config to use')

    # Create the parser for the extract sub-command
    extract_parser = subparsers.add_parser(
        'extract', help='extract the launchpad db into a config file'
    )
    extract_parser.add_argument(
        '-f', '--format', choices=['json', 'yaml'], default='yaml',
        help='the format to extract your config to'
    )
    extract_parser.add_argument('config_path', help='the file path to extract the config to')

    # Create the parser for the compare sub-command
    compare_parser = subparsers.add_parser(
        'compare', help='compare the launchpad db with the config'
    )
    compare_parser.add_argument('config_path', help='the file path of the config to compare')

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.error('please specify an action to perform')

    print()
    print(f'{BOLD}Launchpad Builder{ENDC}')
    print()

    # Determine the location of the SQLite Launchpad database
    launchpad_db_dir = get_launchpad_db_dir()
    launchpad_db_path = os.path.join(launchpad_db_dir, 'db')

    print(f'{BLUE}Using Launchpad database {launchpad_db_path}{ENDC}')

    # Build
    if args.command == 'build':
        with open(args.config_path) as f:
            config = yaml.load(f)

        # Re-build the user's database if requested
        if not args.skip_db_rebuild:
            # Delete original Launchpad database and rebuild it for a fresh start
            print(f'{BLUE}Deleting Launchpad database files to perform database rebuild{ENDC}')
            for launchpad_db_file in ['db', 'db-shm', 'db-wal']:
                try:
                    os.remove(os.path.join(launchpad_db_dir, launchpad_db_file))
                except OSError:
                    pass

            # Restart the Dock to get a freshly built database to work from
            print(f'{BLUE}Restarting the Dock to build a fresh Launchpad databases{ENDC}')
            subprocess.call(['/usr/bin/killall', 'Dock'])
            sleep(3)

        print(f'{BLUE}Rebuilding the Launchpad database{ENDC}')
        launchpad_builder = LaunchpadBuilder(
            launchpad_db_path, config['widget_layout'], config['app_layout']
        )
        launchpad_builder.build()

        # Report any missing items which were defined in the layout but not in the db
        if launchpad_builder.missing_widgets:
            print(f'{RED}Missing widgets found and skipped:{ENDC}')
            for missing_widget in launchpad_builder.missing_widgets:
                print(f'{RED}- {missing_widget}{ENDC}')

        if launchpad_builder.missing_apps:
            print(f'{RED}Missing apps found and skipped:{ENDC}')
            for missing_app in launchpad_builder.missing_apps:
                print(f'{RED}- {missing_app}{ENDC}')

        # Report any extra widgets or apps found that weren't in the layout
        if launchpad_builder.extra_widgets:
            print(f'{RED}Extra widgets found and added to the last page:{ENDC}')
            for extra_widget in launchpad_builder.extra_widgets:
                print(f'{RED}- {extra_widget}{ENDC}')

        if launchpad_builder.extra_apps:
            print(f'{RED}Extra apps found and added to the last page:{ENDC}')
            for extra_app in launchpad_builder.extra_apps:
                print(f'{RED}- {extra_app}{ENDC}')

        # Restart the Dock to that Launchpad can read our new and updated database
        print(f'{BLUE}Restarting the Dock to apply the new database{ENDC}')
        subprocess.call(['/usr/bin/killall', 'Dock'])

        print(
            f'{GREEN}Successfully build the Launchpad layout defined in {args.config_path}{ENDC}'
        )

    # Extract
    elif args.command == 'extract':
        launchpad_builder = LaunchpadBuilder(launchpad_db_path)
        launchpad_builder.extract()

        layout = {
            'widget_layout': launchpad_builder.widget_layout,
            'app_layout': launchpad_builder.app_layout
        }

        with open(args.config_path, 'w') as f:
            if args.format == 'yaml':
                f.write(yaml.safe_dump(layout, default_flow_style=False, explicit_start=True))
            else:
                json.dump(layout, f, indent=2)

        print(f'{GREEN}Successfully wrote Launchpad config to {args.config_path}{ENDC}')

    # Compare
    elif args.command == 'compare':
        with open(args.config_path) as f:
            config = yaml.load(f)

        launchpad_builder = LaunchpadBuilder(launchpad_db_path)
        launchpad_builder.extract()

        layout = {
            'widget_layout': launchpad_builder.widget_layout,
            'app_layout': launchpad_builder.app_layout
        }

        if config == layout:
            print(f'{GREEN}The configuration provided is identical to the current layout{ENDC}')
        else:
            print(f'{RED}The configuration provided is different to the current layout{ENDC}')
            print()
            sys.exit(1)

    print()


if __name__ == '__main__':
    main()
