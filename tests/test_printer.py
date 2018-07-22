from elite import ansi
from elite.elite import EliteResponse, EliteState


def test_header(capsys, printer):
    printer.header()
    out, err = capsys.readouterr()
    assert out == ansi.HIDE_CURSOR


def test_footer(capsys, printer):
    printer.footer()
    out, err = capsys.readouterr()
    assert out == ansi.SHOW_CURSOR + '\n'


def test_heading(capsys, printer):
    printer.heading('My Heading')
    out, err = capsys.readouterr()
    assert out == (
        '\n' +
        ansi.BOLD + ansi.UNDERLINE + 'My Heading' + ansi.ENDC + '\n'
    )


def test_info(capsys, printer):
    printer.info('My Info')
    out, err = capsys.readouterr()
    assert out == (
        '\n' +
        ansi.BOLD + 'My Info' + ansi.ENDC + '\n' +
        '\n'
    )


def test_action_running(capsys, printer):
    printer.action(EliteState.RUNNING, 'brew', args={'name': 'htop', 'state': 'latest'})
    out, err = capsys.readouterr()
    assert out == (
        ansi.WHITE + ' running  ' + ansi.ENDC +
        ansi.BLUE + 'brew: ' + ansi.ENDC +
        ansi.YELLOW + "name='htop' state='latest'" + ansi.ENDC
    )


def test_action_ok(capsys, printer):
    printer.action(EliteState.RUNNING, 'brew', args={'name': 'htop', 'state': 'latest'})
    printer.action(
        EliteState.OK, 'brew', args={'name': 'htop', 'state': 'latest'},
        response=EliteResponse(changed=True, ok=True)
    )
    out, err = capsys.readouterr()
    assert out == (
        ansi.WHITE + ' running  ' + ansi.ENDC +
        ansi.BLUE + 'brew: ' + ansi.ENDC +
        ansi.YELLOW + "name='htop' state='latest'" + ansi.ENDC +
        '\r' +
        ansi.GREEN + '    ok    ' + ansi.ENDC +
        ansi.BLUE + 'brew: ' + ansi.ENDC +
        ansi.YELLOW + "name='htop' state='latest'" + ansi.ENDC + '\n'
    )


def test_action_changed(capsys, printer):
    printer.action(EliteState.RUNNING, 'brew', args={'name': 'htop', 'state': 'latest'})
    printer.action(
        EliteState.CHANGED, 'brew', args={'name': 'htop', 'state': 'latest'},
        response=EliteResponse(changed=True, ok=True)
    )
    out, err = capsys.readouterr()
    assert out == (
        ansi.WHITE + ' running  ' + ansi.ENDC +
        ansi.BLUE + 'brew: ' + ansi.ENDC +
        ansi.YELLOW + "name='htop' state='latest'" + ansi.ENDC +
        '\r' +
        ansi.YELLOW + ' changed  ' + ansi.ENDC +
        ansi.BLUE + 'brew: ' + ansi.ENDC +
        ansi.YELLOW + "name='htop' state='latest'" + ansi.ENDC + '\n'
    )


def test_action_failed(capsys, printer):
    failed_message = 'unable to find a package matching the name provided'

    printer.action(EliteState.RUNNING, 'brew', args={'name': 'htop', 'state': 'latest'})
    printer.action(
        EliteState.FAILED, 'brew', args={'name': 'htop', 'state': 'latest'},
        response=EliteResponse(changed=False, ok=False, failed_message=failed_message)
    )
    out, err = capsys.readouterr()
    assert out == (
        ansi.WHITE + ' running  ' + ansi.ENDC +
        ansi.BLUE + 'brew: ' + ansi.ENDC +
        ansi.YELLOW + "name='htop' state='latest'" + ansi.ENDC +
        '\r' +
        ansi.RED + '  failed  ' + ansi.ENDC +
        ansi.BLUE + 'brew: ' + ansi.ENDC +
        ansi.YELLOW + "name='htop' state='latest'" + ansi.ENDC + '\n' +
        '          ' + ansi.BLUE + 'message: ' + ansi.ENDC +
        ansi.YELLOW + failed_message + ansi.ENDC + '\n'
    )


def test_action_overlap(capsys, printer):
    message = (
        'this is truly a very very long message that will exceed the 80 characters that we have '
        'in our terminal and spill over into the next line which should cause the cursor to '
        'to move up to the starting line when printing the ok message'
    )

    printer.action(EliteState.RUNNING, 'info', args={'message': message})
    printer.action(
        EliteState.OK, 'info', args={'message': message},
        response=EliteResponse(changed=True, ok=True)
    )
    out, err = capsys.readouterr()

    # The final length of the line is as follows:
    # (status) 10 + (action name) 6 + (message) 230 = 246 => 4 lines (for an 80 x 24 terminal)
    #
    # As such, the cursor will be on line 4, so we move it to the left using a \r and up 3 lines
    # to reach the first line of output.
    assert out == (
        ansi.WHITE + ' running  ' + ansi.ENDC +
        ansi.BLUE + 'info: ' + ansi.ENDC +
        ansi.YELLOW + f"message='{message}'" + ansi.ENDC +
        '\r' + ansi.move_up(3) +
        ansi.GREEN + '    ok    ' + ansi.ENDC +
        ansi.BLUE + 'info: ' + ansi.ENDC +
        ansi.YELLOW + f"message='{message}'" + ansi.ENDC + '\n'
    )


def test_action_output_larger_than_terminal(capsys, printer):
    # Ensure that the message is larger than 80 x 24
    message = 'o' * (80 * 25)

    printer.action(EliteState.RUNNING, 'info', args={'message': message})
    printer.action(
        EliteState.OK, 'info', args={'message': message},
        response=EliteResponse(changed=True, ok=True)
    )
    out, err = capsys.readouterr()

    # The first line of output also contains the status and action name, so we subtract those
    # from the width of the first line of the message:
    # (terminal char width) 80 - (status) 10 - (action name) 6 - (args with quote) 9 = 55
    #
    # The last line of output will lose the last 3 characters in place of ...
    cropped_message = 'o' * (55 + 80 * 22 + 77) + '...'

    assert out == (
        ansi.WHITE + ' running  ' + ansi.ENDC +
        ansi.BLUE + 'info: ' + ansi.ENDC +
        ansi.YELLOW + f"message='{cropped_message}" + ansi.ENDC +
        '\r' + ansi.move_up(23) +
        ansi.GREEN + '    ok    ' + ansi.ENDC +
        ansi.BLUE + 'info: ' + ansi.ENDC +
        ansi.YELLOW + f"message='{message}'" + ansi.ENDC + '\n'
    )


def test_summary(capsys, printer):
    actions = {
        EliteState.OK: [
            ('brew', {'name': 'htop', 'state': 'latest'}, EliteResponse(changed=False, ok=True)),
            ('cask', {'name': 'skype', 'state': 'present'}, EliteResponse(changed=False, ok=True))
        ],
        EliteState.CHANGED: [
            (
                'tap', {'name': 'homebrew/cask', 'state': 'present'},
                EliteResponse(changed=True, ok=True)
            ),
            ('cask', {'name': 'forklift', 'state': 'latest'}, EliteResponse(changed=True, ok=True)),
            ('cask', {'name': 'slack', 'state': 'latest'}, EliteResponse(changed=True, ok=True))
        ],
        EliteState.FAILED: [
            (
                'brew', {'name': 'sheepsay', 'state': 'present'},
                EliteResponse(
                    changed=False, ok=False,
                    failed_message='unable to find a package matching the name provided'
                )
            )
        ]
    }

    printer.summary(actions)
    out, err = capsys.readouterr()

    assert out == (
        # Changed actions
        '\n' +
        ansi.BOLD + 'Changed Actions' + ansi.ENDC + '\n' +
        '\n' +
        # tap: homebrew/cask
        ansi.YELLOW + ' changed  ' + ansi.ENDC +
        ansi.BLUE + 'tap: ' + ansi.ENDC +
        ansi.YELLOW + f"name='homebrew/cask' state='present'" + ansi.ENDC + '\n' +
        # cask: forklift
        ansi.YELLOW + ' changed  ' + ansi.ENDC +
        ansi.BLUE + 'cask: ' + ansi.ENDC +
        ansi.YELLOW + f"name='forklift' state='latest'" + ansi.ENDC + '\n' +
        # cask: slack
        ansi.YELLOW + ' changed  ' + ansi.ENDC +
        ansi.BLUE + 'cask: ' + ansi.ENDC +
        ansi.YELLOW + f"name='slack' state='latest'" + ansi.ENDC + '\n' +

        # Failed actions
        '\n' +
        ansi.BOLD + 'Failed Actions' + ansi.ENDC + '\n' +
        '\n' +
        # brew: sheepsay
        ansi.RED + '  failed  ' + ansi.ENDC +
        ansi.BLUE + 'brew: ' + ansi.ENDC +
        ansi.YELLOW + f"name='sheepsay' state='present'" + ansi.ENDC + '\n' +
        '          ' + ansi.BLUE + 'message: ' + ansi.ENDC +
        ansi.YELLOW + 'unable to find a package matching the name provided' + ansi.ENDC + '\n'

        # Totals
        '\n' +
        ansi.BOLD + 'Totals' + ansi.ENDC + '\n' +
        '\n' +
        ansi.GREEN + '    ok    ' + ansi.ENDC + '   2' + '\n' +
        ansi.YELLOW + ' changed  ' + ansi.ENDC + '   3' + '\n' +
        ansi.RED + '  failed  ' + ansi.ENDC + '   1' + '\n' +
        '  total   ' + '   6' + '\n'
    )


def test_summary_no_changed(capsys, printer):
    actions = {
        EliteState.OK: [
            ('brew', {'name': 'htop', 'state': 'latest'}, EliteResponse(changed=False, ok=True)),
            ('cask', {'name': 'skype', 'state': 'present'}, EliteResponse(changed=False, ok=True))
        ],
        EliteState.CHANGED: [],
        EliteState.FAILED: []
    }

    printer.summary(actions)
    out, err = capsys.readouterr()

    assert out == (
        # Totals
        '\n' +
        ansi.BOLD + 'Totals' + ansi.ENDC + '\n' +
        '\n' +
        ansi.GREEN + '    ok    ' + ansi.ENDC + '   2' + '\n' +
        ansi.YELLOW + ' changed  ' + ansi.ENDC + '   0' + '\n' +
        ansi.RED + '  failed  ' + ansi.ENDC + '   0' + '\n' +
        '  total   ' + '   2' + '\n'
    )


def test_summary_no_ok(capsys, printer):
    actions = {
        EliteState.OK: [],
        EliteState.CHANGED: [
            ('cask', {'name': 'slack', 'state': 'latest'}, EliteResponse(changed=True, ok=True))
        ],
        EliteState.FAILED: [
            (
                'brew', {'name': 'sheepsay', 'state': 'present'},
                EliteResponse(
                    changed=False, ok=False,
                    failed_message='unable to find a package matching the name provided'
                )
            )
        ]
    }

    printer.summary(actions)
    out, err = capsys.readouterr()

    assert out == (
        # Changed actions
        '\n' +
        ansi.BOLD + 'Changed Actions' + ansi.ENDC + '\n' +
        '\n' +
        # cask: slack
        ansi.YELLOW + ' changed  ' + ansi.ENDC +
        ansi.BLUE + 'cask: ' + ansi.ENDC +
        ansi.YELLOW + f"name='slack' state='latest'" + ansi.ENDC + '\n' +

        # Failed actions
        '\n' +
        ansi.BOLD + 'Failed Actions' + ansi.ENDC + '\n' +
        '\n' +
        # brew: sheepsay
        ansi.RED + '  failed  ' + ansi.ENDC +
        ansi.BLUE + 'brew: ' + ansi.ENDC +
        ansi.YELLOW + f"name='sheepsay' state='present'" + ansi.ENDC + '\n' +
        '          ' + ansi.BLUE + 'message: ' + ansi.ENDC +
        ansi.YELLOW + 'unable to find a package matching the name provided' + ansi.ENDC + '\n'

        # Totals
        '\n' +
        ansi.BOLD + 'Totals' + ansi.ENDC + '\n' +
        '\n' +
        ansi.GREEN + '    ok    ' + ansi.ENDC + '   0' + '\n' +
        ansi.YELLOW + ' changed  ' + ansi.ENDC + '   1' + '\n' +
        ansi.RED + '  failed  ' + ansi.ENDC + '   1' + '\n' +
        '  total   ' + '   2' + '\n'
    )
