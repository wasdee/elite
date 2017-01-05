from .ansible import AnsibleState
from . import ansi


def print_task(state, module, raw_params, args, settings, result, newline=False):
    # Prepare raw_params for printing
    print_raw_params = f' {raw_params}' if raw_params else ''

    # Prettify arguments for printing
    print_args_strs = [
        f'{k}={repr(v)}' for k, v in args.items() if k != '_raw_params' and v is not None
    ]
    print_args = f" {' '.join(print_args_strs)}" if print_args_strs else ''

    # Determine the output colour and state text
    if state == AnsibleState.RUNNING:
        print_colour = ansi.WHITE
        print_state = 'running'
    elif state == AnsibleState.FAILED:
        print_colour = ansi.RED
        print_state = 'failed'
    elif state == AnsibleState.CHANGED:
        print_colour = ansi.YELLOW
        print_state = 'changed'
    else:
        print_colour = ansi.GREEN
        print_state = 'ok'

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

    if newline:
        print()


def header():
    print(ansi.HIDE_CURSOR, end='', flush=True)


def footer():
    print(ansi.SHOW_CURSOR, end='', flush=True)
    print()


def heading(text):
    print()
    print(f'{ansi.BOLD}{ansi.UNDERLINE}{text}{ansi.ENDC}')


def info(text):
    print()
    print(f'{ansi.BOLD}{text}{ansi.ENDC}')
    print()


def summary(
    total_tasks, ok_tasks,
    changed_tasks, changed_task_info, failed_tasks, failed_task_info
):
    if changed_task_info:
        info('Changed task info:')
        for module, raw_params, args, settings, result in changed_task_info:
            print_task(
                AnsibleState.CHANGED, module, raw_params, args, settings, result, newline=True
            )

    if failed_task_info:
        info('Failed task info:')
        for module, raw_params, args, settings, result in failed_task_info:
            print_task(
                AnsibleState.FAILED, module, raw_params, args, settings, result, newline=True
            )

    info('Totals:')
    print(f'{ansi.GREEN}  ok{ansi.ENDC}       {ok_tasks}')
    print(f'{ansi.YELLOW}  changed{ansi.ENDC}  {changed_tasks}')
    print(f'{ansi.RED}  failed{ansi.ENDC}   {failed_tasks}')
    print(f'  total    {total_tasks}')


def progress(state, module, raw_params, args, settings, result):
    # if settings.get('quiet', False) or (result and not result.get('changed', True)):
    #     return

    # Overwrite output when the task completes
    if state != AnsibleState.RUNNING:
        print(f'\r{ansi.CLEAR_LINE}', end='', flush=True)

    print_task(state, module, raw_params, args, settings, result)

    # If a result has been printed, we may move to the next line
    if state != AnsibleState.RUNNING:
        print()
