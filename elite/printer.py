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
        Prints information within a section.

        :param text: the text to display
        """
        print()
        print(ansi.BOLD + text + ansi.ENDC)
        print()

    def _state_colour(self, state):
        if state == EliteState.RUNNING:
            return ansi.WHITE
        elif state == EliteState.FAILED:
            return ansi.RED
        elif state == EliteState.CHANGED:
            return ansi.YELLOW
        else:
            return ansi.GREEN

    def action(self, state, action, args, response=None):
        """
        Displays progress while actions are running and also completing execution along with
        related message upon failure.

        :param state: the state of the action which is an enum of type EliteStatus
        :param action: the action being called
        :param args: the arguments sent to the action
        :param response: the response of the execution or None when the action is still running
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
                    print_chars = max_chars
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

    def summary(self, actions):
        """
        Displays a final summary after execution of all actions have completed.

        :param actions: a dict containing a state to action list mapping
        """
        # Display any actions that caused changes or failed.
        for state, text in [
            (EliteState.CHANGED, 'Changed Actions'),
            (EliteState.FAILED, 'Failed Actions')
        ]:
            if not actions[state]:
                continue

            self.info(text)
            for action, args, response in actions[state]:
                self.action(state, action, args, response)

        # Display all totals
        self.info('Totals')
        for state in [EliteState.OK, EliteState.CHANGED, EliteState.FAILED]:
            state_name = state.name.lower()
            state_colour = self._state_colour(state)
            total = len(actions[state])
            print(state_colour + f'{state_name:^10}' + ansi.ENDC + f'{total:4}')

        grand_total = (
            len(actions[EliteState.OK]) +
            len(actions[EliteState.CHANGED]) +
            len(actions[EliteState.FAILED])
        )
        print(f"{'total':^10}{grand_total:4}")
