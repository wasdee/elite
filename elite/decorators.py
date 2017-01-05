import os
from functools import wraps

from .ansible import Ansible, AnsibleError
from .config import Config
from .print import header, footer, heading, info, progress, summary
from . import ansi


def build_relative_path(path):
    return os.path.join(os.path.dirname(__file__), os.pardir, path)


def elite(config_path, module_search_paths=[]):
    def decorator(main):
        @wraps(main)
        def decorated_function():
            try:
                # Setup Ansible and our configuration
                module_search_paths_abs = [
                    build_relative_path(msp) for msp in module_search_paths
                ]
                ansible = Ansible(
                    callback=progress, heading=heading, info=info,
                    summary=summary,
                    module_search_paths=module_search_paths_abs
                )
                config = Config(build_relative_path(config_path))

                # Header
                header()

                # Run the main Ansible entrypoint
                main(ansible, config)

            # A task failed to run
            except AnsibleError as e:
                print()
                print(f'{ansi.RED}Failed: {e}{ansi.ENDC}')

            # User has hit Ctrl+C
            except KeyboardInterrupt:
                print()

            # Footer
            finally:
                ansible.cleanup()
                footer()

        return decorated_function

    return decorator
