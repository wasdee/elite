from functools import wraps

from .elite import Elite, EliteError
from .config import Config
from .printer import Printer
from .utils import build_absolute_path
from . import ansi


def elite_main(config_path, action_search_paths=[]):
    def decorator(main):
        @wraps(main)
        def decorated_function():
            try:
                # Setup Elite and our configuration
                action_search_paths_abs = [build_absolute_path(msp) for msp in action_search_paths]

                # Create our objects
                printer = Printer()
                elite = Elite(printer=printer, action_search_paths=action_search_paths_abs)
                config = Config(build_absolute_path(config_path))

                # Header
                printer.header()

                # Run the main Elite entrypoint
                main(elite, config, printer)

                # Summary
                printer.heading('Summary')
                elite.summary()

            # A task failed to run
            except EliteError as e:
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
                printer.footer()

        return decorated_function

    return decorator
