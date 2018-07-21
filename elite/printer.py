import math
import shutil

from . import ansi
from .elite import EliteState


class Printer:
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
        print(ansi.BOLD + ansi.UNDERLINE + text + ansi.ENDC)

    def info(self, text):
        """
        Prints task information within a section.

        :param text: the text to display
        """
        print()
        print(ansi.BOLD + text + ansi.ENDC)
        print()

    def progress(self, state, action, args, response):
        """
        Displays task progress while tasks are both running and completing execution.

        :param state: The state of the task which is an enum of type EliteStatus.
        :param action: The action being called.
        :param args: The arguments sent to the action.
        :param response: The response of the execution or None when the task is still running.
        """
        self._print_task(state, action, args, response)

    def summary(self, tasks):
        """
        Displays a final summary after execution of all tasks have completed.

        :param tasks: a dict containing a state to task list mapping
        """
        # Display any tasks that caused changes or failed.
        for state, text in [
            (EliteState.CHANGED, 'Changed task info:'),
            (EliteState.FAILED, 'Failed task info:')
        ]:
            if not tasks[state]:
                continue

            self.info(text)
            for action, args, response in tasks[state]:
                self._print_task(state, action, args, response)

        # Display all totals
        self.info('Totals:')
        for state in [EliteState.OK, EliteState.CHANGED, EliteState.FAILED]:
            state_name = state.name.lower()
            state_colour = self._state_colour(state)
            total = len(tasks[state])
            print(state_colour + f'{state_name:^10}' + ansi.ENDC + f'{total:4}')

        grand_total = (
            len(tasks[EliteState.OK]) +
            len(tasks[EliteState.CHANGED]) +
            len(tasks[EliteState.FAILED])
        )
        print(f"{'total':^10}{grand_total:4}")

    def _state_colour(self, state):
        if state == EliteState.RUNNING:
            return ansi.WHITE
        elif state == EliteState.FAILED:
            return ansi.RED
        elif state == EliteState.CHANGED:
            return ansi.YELLOW
        else:
            return ansi.GREEN

    def _print_task(self, state, action, args, response):
        """
        Displays a particular task along with the related message upon failure.

        :param state: The state of the task which is an enum of type EliteStatus.
        :param action: The action being called.
        :param args: The arguments sent to the action.
        :param response: The response of the execution or None when the task is still running.
        """
        # Determine the output colour and state text
        state_name = state.name.lower()
        state_colour = self._state_colour(state)

        # Prettify arguments and action for printing
        print_args = ''
        print_action = action

        non_empty_args = {k: v for k, v in args.items() if v is not None}
        if non_empty_args:
            print_args = ' '.join(f'{k}={repr(v)}' for k, v in non_empty_args.items())
            print_action += ': '

        # Determine the max characters we can print
        if state == EliteState.RUNNING:
            terminal_size = shutil.get_terminal_size()
            max_chars = terminal_size.columns * terminal_size.lines

            print_status = ''
            print_chars = 0

            for colour, text in [
                (state_colour, f'{state_name:^10}'),
                (ansi.BLUE, print_action),
                (ansi.YELLOW, print_args)
            ]:
                print_chars += len(text)

                # We have reached the maximum characters possible to print in the terminal so we
                # crop the text and stop processing further text.
                if print_chars > max_chars:
                    chop_chars = print_chars - max_chars + 3
                    print_status += colour + text[:-chop_chars] + '...' + ansi.ENDC
                    break
                else:
                    print_status += colour + text + ansi.ENDC

            print(print_status, end='', flush=True)
            self.overlap_lines = math.ceil(print_chars / terminal_size.columns) - 1
        else:
            # Display the current action and its details
            if self.overlap_lines is not None:
                # Move to the very left of the last line
                print('\r', end='', flush=True)
                # Move up to the line we wish to start printing from
                print(ansi.move_up(self.overlap_lines), end='', flush=True)

            print(
                state_colour + f'{state_name:^10}' + ansi.ENDC +
                ansi.BLUE + print_action + ansi.ENDC +
                ansi.YELLOW + print_args + ansi.ENDC
            )

            # Display the changed or failure message if necessary
            if state == EliteState.FAILED and response.failed_message is not None:
                print(
                    f"{'':^10}" +
                    ansi.BLUE + 'message: ' + ansi.ENDC +
                    ansi.YELLOW + response.failed_message + ansi.ENDC
                )

            # Reset the number of lines to overlap
            self.overlap_lines = None
