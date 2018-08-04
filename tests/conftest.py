import os
import pwd
import shutil

import pytest
from elite import ansi
from elite.elite import Elite
from elite.printer import Printer
from tests import helpers


@pytest.fixture
def printer(monkeypatch, request):
    def fin():
        """Ensure that the cursor is shown when printer unit tests complete."""
        print(ansi.SHOW_CURSOR, end='', flush=True)
    request.addfinalizer(fin)

    monkeypatch.setattr(shutil, 'get_terminal_size', lambda: os.terminal_size((80, 24)))
    return Printer()


# pylint: disable=redefined-outer-name
@pytest.fixture
def elite(monkeypatch, printer):
    monkeypatch.setattr(os, 'getuid', lambda: 0)
    monkeypatch.setattr(os, 'getgid', lambda: 0)
    monkeypatch.setattr(os, 'getcwd', lambda: '/Users/fots/Documents/Development/macbuild/elite')
    monkeypatch.setattr(pwd, 'getpwuid', helpers.getpwuid)

    monkeypatch.setenv('SUDO_USER', 'fots')
    monkeypatch.setenv('SUDO_UID', '501')
    monkeypatch.setenv('SUDO_GID', '20')
    monkeypatch.setenv('LOGNAME', 'root')
    monkeypatch.setenv('USER', 'root')
    monkeypatch.setenv('USERNAME', 'root')
    monkeypatch.setenv('SHELL', '/bin/sh')
    monkeypatch.setenv('MAIL', '/var/mail/root')

    return Elite(printer)
