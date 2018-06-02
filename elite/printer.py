import math
import shutil

from .elite import EliteState
from . import ansi


class Printer(object):
    def __init__(self):
        # Track the number of lines we must move upwards to overlap text
        self.overlap_lines = None

    def header(self):
        """Prints the master header which hides the cursor."""
        print(ansi.HIDE_CURSOR, end='', flush=True)

    def footer(self):
        """Prints the master footer which shows the cursor and prints a new line to end output."""
        print(ansi.SHOW_CURSOR, end='', flush=True)
        print()

    def heading(self, text):
        """
        Prints a section heading.  It is expected that this will be followed by info.

        :param text: the text to display
        """
        print()
        print(f'{ansi.BOLD}{ansi.UNDERLINE}{text}{ansi.ENDC}')

    def info(self, text):
        """
        Prints task information within a section.

        :param text: the text to display
        """
        print()
        print(f'{ansi.BOLD}{text}{ansi.ENDC}')
        print()

    def progress(self, state, action, args, result):
        """
        Displays task progress while tasks are both running and completing execution.

        :param state: The state of the task which is an enum of type EliteStatus.
        :param action: The action being called.
        :param args: The arguments sent to the action.
        :param result: The result of the execution or None when the task is still running.
        """
        self._print_task(state, action, args, result)

    def summary(self, ok_tasks, changed_tasks, failed_tasks):
        """
        Displays a final summary after execution of all tasks have completed.

        :param ok_tasks: A list of tuples containing information relating on successful tasks.
        :param changed_tasks: A list of tuples containing information relating on each
                              changes made.
        :param failed_tasks: A list of tuples containing information relating to each failed task.
        """
        # Display any tasks that caused changes.
        if changed_tasks:
            self.info('Changed task info:')
            for action, args, result in changed_tasks:
                self._print_task(EliteState.CHANGED, action, args, result)

        # Display any failed tasks.
        if failed_tasks:
            self.info('Failed task info:')
            for action, args, result in failed_tasks:
                self._print_task(EliteState.FAILED, action, args, result)

        # Display all totals
        total_tasks = len(ok_tasks) + len(changed_tasks) + len(failed_tasks)
        self.info('Totals:')
        print(f"{ansi.GREEN}{'ok':^10}{ansi.ENDC}{len(ok_tasks):4}")
        print(f"{ansi.YELLOW}{'changed':^10}{ansi.ENDC}{len(changed_tasks):4}")
        print(f"{ansi.RED}{'failed':^10}{ansi.ENDC}{len(failed_tasks):4}")
        print(f"{'total':^10}{total_tasks:4}")

    def _print_task(self, state, action, args, result):
        """
        Displays a particular task along with the related message upon failure.

        :param state: The state of the task which is an enum of type EliteStatus.
        :param action: The action being called.
        :param args: The arguments sent to the action.
        :param result: The result of the execution or None when the task is still running.
        """
        # Determine the output colour and state text
        if state == EliteState.RUNNING:
            print_colour = ansi.WHITE
            print_state = 'running'
        elif state == EliteState.FAILED:
            print_colour = ansi.RED
            print_state = 'failed'
        elif state == EliteState.CHANGED:
            print_colour = ansi.YELLOW
            print_state = 'changed'
        else:
            print_colour = ansi.GREEN
            print_state = 'ok'

        # Prettify arguments and action for printing
        print_args_strs = [f'{k}={repr(v)}' for k, v in args.items() if v is not None]
        print_args = ' '.join(print_args_strs) if print_args_strs else ''
        print_action = f'{action}: ' if print_args else action

        # Determine the max characters we can print
        if state == EliteState.RUNNING:
            terminal_size = shutil.get_terminal_size()
            max_chars = terminal_size.columns * terminal_size.lines

            print_status = ''
            print_chars = 0

            for colour, text in [
                (print_colour, f'{print_state:^10}'),
                (ansi.BLUE, print_action),
                (ansi.YELLOW, print_args)
            ]:
                print_chars += len(text)

                # We have reached the maximum characters possible to print in the terminal so we
                # crop the text and stop processing further text.
                if print_chars > max_chars:
                    chop_chars = print_chars - max_chars + 3
                    print_status += f'{colour}{text[:-chop_chars]}...{ansi.ENDC}'
                    break
                else:
                    print_status += f'{colour}{text}{ansi.ENDC}'

            print(print_status, end='', flush=True)
            self.overlap_lines = math.ceil(print_chars / terminal_size.columns) - 1
        else:
            # Display the current action and its details
            if self.overlap_lines is not None:
                # Move to the very left of the last line
                print('\r', end='', flush=True)
                # Move up to the line we wish to start printing from
                print(ansi.move_up(self.overlap_lines), end='', flush=True)

            print_status = (
                f'{print_colour}{print_state:^10}{ansi.ENDC}'
                f'{ansi.BLUE}{print_action}{ansi.ENDC}'
                f'{ansi.YELLOW}{print_args}{ansi.ENDC}'
            )
            print(print_status)

            # Display the changed or failure message if necessary
            if state == EliteState.FAILED:
                print(
                    f"{ansi.BLUE}{'':^10}message:{ansi.ENDC} "
                    f"{ansi.YELLOW}{result['message']}{ansi.ENDC}"
                )

            # Reset the number of lines to overlap
            self.overlap_lines = None
