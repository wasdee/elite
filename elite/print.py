from .ansible import AnsibleState
from . import ansi


def header():
    print(ansi.HIDE_CURSOR, end='', flush=True)


def footer():
    print(ansi.SHOW_CURSOR, end='', flush=True)
    print()


def heading(heading):
    print()
    print(f'{ansi.BOLD}{heading}{ansi.ENDC}')
    print()


def progress(state, module, raw_params, args, settings, result):
    # if settings.get('quiet', False) or (result and not result.get('changed', True)):
    #     return

    # Prepare raw_params for printing
    print_raw_params = f' {raw_params}' if raw_params else ''

    # Prettify arguments for printing
    print_args_strs = [
        f'{k}={repr(v)}' for k, v in args.items() if k != '_raw_params' and v is not None
    ]
    print_args = f" {' '.join(print_args_strs)}" if print_args_strs else ''

    # Overwrite output when the task completes
    # if state != AnsibleState.RUNNING:
        # print(f'\r{ansi.CLEAR_LINE}', end='', flush=True)
        # print()

    # Determine the output colour and state text
    if state == AnsibleState.RUNNING:
        print_colour = ansi.WHITE
        print_state = 'running'
    elif state == AnsibleState.FAILED:
        print_colour = ansi.RED
        print_state = 'failed'
    else:
        print_colour = ansi.GREEN
        print_state = 'changed' if result["changed"] else 'ok'

    # Display the status in the appropriate colour
    print(f'{print_colour}{print_state:^10}{ansi.ENDC}', end='', flush=True)

    # Display the module details
    print(f'{ansi.BLUE}{module}:{ansi.ENDC}', end='', flush=True)

    # Display the module parameters and arguments
    print(f'{ansi.YELLOW}', end='', flush=True)
    if settings.get('sudo', False):
        print(' (sudo)', end='', flush=True)
    print(f'{print_raw_params}{print_args}{ansi.ENDC}', end='', flush=True)

    # Failed message
    if state == AnsibleState.FAILED:
        print()
        print(
            f"{ansi.BLUE}{'':^10}msg:{ansi.ENDC} {ansi.YELLOW}{result['msg']}{ansi.ENDC}",
            end='', flush=True
        )

    # If a result has been printed, we may move to the next line
    # if state != AnsibleState.RUNNING:
    print('')
