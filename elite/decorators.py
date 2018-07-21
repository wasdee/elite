from functools import wraps

from . import ansi
from .config import ConfigError, load_config
from .elite import Elite, EliteError
from .printer import Printer
from .utils import build_absolute_path


def automate(config_path):
    def decorator(main):
        @wraps(main)
        def decorated_function():
            try:
                # Create our objects
                printer = Printer()
                elite = Elite(printer=printer)
                config = load_config(build_absolute_path(config_path))

                # Header
                printer.header()

                # Run the main Elite entrypoint
                main(elite, config, printer)

                # Summary
                printer.heading('Summary')
                elite.summary()

            # A config issue was encountered
            except ConfigError as e:
                print()
                print(f'{ansi.RED}Config Error: {e}{ansi.ENDC}')

            # A task failed to run
            except EliteError:
                # Summary
                printer.heading('Summary')
                elite.summary()

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
