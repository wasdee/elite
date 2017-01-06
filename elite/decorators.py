from functools import wraps

from .ansible import Ansible, AnsibleError
from .config import Config
from .printer import Printer
from .utils import build_absolute_path
from . import ansi


def elite(config_path, module_search_paths=[]):
    def decorator(main):
        @wraps(main)
        def decorated_function():
            try:
                # Setup Ansible and our configuration
                module_search_paths_abs = [
                    build_absolute_path(msp) for msp in module_search_paths
                ]

                # Create our objects
                printer = Printer()
                ansible = Ansible(printer=printer, module_search_paths=module_search_paths_abs)
                config = Config(build_absolute_path(config_path))

                # Header
                printer.header()

                # Run the main Ansible entrypoint
                main(ansible, config, printer)

            # A task failed to run
            except AnsibleError as e:
                print()
                print(f'{ansi.RED}Failed: {e}{ansi.ENDC}')

            # User has hit Ctrl+C
            except KeyboardInterrupt:
                print()
                print()
                print(
                    f'{ansi.RED}Processing aborted as requested by keyboard interrupt.{ansi.ENDC}'
                )

            # Footer
            finally:
                ansible.cleanup()
                printer.footer()

        return decorated_function

    return decorator
