from .elite import EliteState
from . import ansi


class Printer(object):
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
        # Overwrite output when the task completes
        if state != EliteState.RUNNING:
            print(f'\r{ansi.CLEAR_LINE}', end='', flush=True)

        # Print the task being executed
        newline = state != EliteState.RUNNING
        self._print_task(state, action, args, result, newline)

    def summary(
        self, total_tasks, ok_tasks, changed_tasks, failed_tasks,
        changed_task_info, failed_task_info
    ):
        """
        Displays a final summary after execution of all tasks have completed.

        :param total_tasks: The total number of tasks executed.
        :param ok_tasks: The number of unchanged OK tasks.
        :param changed_tasks: The number of tasks that caused changes to occur.
        :param failed_tasks: The number of failed tasks.
        :param changed_task_info: A tuple containing information relating on each changes made.
        :param failed_task_info: A tuple containing information relating to each failed task.
        """
        # Display any tasks that caused changes.
        if changed_task_info:
            self.info('Changed task info:')
            for action, args, result in changed_task_info:
                self._print_task(
                    EliteState.CHANGED, action, args, result, newline=True
                )

        # Display any failed tasks.
        if failed_task_info:
            self.info('Failed task info:')
            for action, args, result in failed_task_info:
                self._print_task(
                    EliteState.FAILED, action, args, result, newline=True
                )

        # Display all totals
        self.info('Totals:')
        print(f"{ansi.GREEN}{'ok':^10}{ansi.ENDC}{ok_tasks:4}")
        print(f"{ansi.YELLOW}{'changed':^10}{ansi.ENDC}{changed_tasks:4}")
        print(f"{ansi.RED}{'failed':^10}{ansi.ENDC}{failed_tasks:4}")
        print(f"{'total':^10}{total_tasks:4}")

    def _print_task(self, state, action, args, result, newline=False):
        """
        Displays a particular task along with the related message upon failure.

        :param state: The state of the task which is an enum of type EliteStatus.
        :param action: The action being called.
        :param args: The arguments sent to the action.
        :param result: The result of the execution or None when the task is still running.
        :param newline: Whether or not to end the output with a newline.
        """
        # Prettify arguments for printing
        print_args_strs = [f'{k}={repr(v)}' for k, v in args.items() if v is not None]
        print_args = f" {' '.join(print_args_strs)}" if print_args_strs else ''

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

        # Display the status in the appropriate colour
        print(f'{print_colour}{print_state:^10}{ansi.ENDC}', end='', flush=True)

        # Display the action details
        print(f'{ansi.BLUE}{action}:{ansi.ENDC}', end='', flush=True)

        # Display the action parameters and arguments
        print(f'{ansi.YELLOW}', end='', flush=True)
        # TODO: re-instate sudo printing
        # if settings.get('sudo', False):
        #     print(' (sudo)', end='', flush=True)
        print(f'{print_args}{ansi.ENDC}', end='', flush=True)

        # Display the changed or failure message if necessary
        if state == EliteState.FAILED:
            print()
            print(
                f"{ansi.BLUE}{'':^10}message:{ansi.ENDC} "
                f"{ansi.YELLOW}{result['message']}{ansi.ENDC}",
                end='', flush=True
            )

        # Display a new line if required
        if newline:
            print()
