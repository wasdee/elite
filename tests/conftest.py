import os

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

    monkeypatch.setattr('shutil.get_terminal_size', lambda: os.terminal_size((80, 24)))
    return Printer()


@pytest.fixture
def elite(monkeypatch, printer):  # pylint: disable=redefined-outer-name
    helpers.patch_root_runtime(monkeypatch)
    return Elite(printer)
