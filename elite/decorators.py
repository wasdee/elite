from functools import wraps

from . import ansi
from .config import ConfigError
from .elite import Elite, EliteError, EliteRuntimeError
from .printer import Printer


def automate():
    def decorator(main):
        @wraps(main)
        def decorated_function():
            try:
                # Create our objects
                printer = Printer()
                elite = Elite(printer=printer)

                # Header
                printer.header()

                # Run the main Elite entrypoint
                main(elite, printer)

                # Summary
                printer.heading('Summary')
                elite.summary()

            # A config issue was encountered
            except ConfigError as e:
                print()
                print(f'{ansi.RED}Config Error: {e}{ansi.ENDC}')

            except EliteRuntimeError as e:
                print()
                print(f'{ansi.RED}Elite Runtime Error: {e}{ansi.ENDC}')

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
                # Summary
                printer.heading('Summary')
                elite.summary()

            # Footer
            finally:
                printer.footer()

        return decorated_function

    return decorator
