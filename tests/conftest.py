import os
import shutil

import pytest
from elite import ansi
from elite.printer import Printer


@pytest.fixture
def printer(monkeypatch, request):
    def fin():
        """Ensure that the cursor is shown when printer unit tests complete."""
        print(ansi.SHOW_CURSOR, end='', flush=True)
    request.addfinalizer(fin)

    monkeypatch.setattr(shutil, 'get_terminal_size', lambda: os.terminal_size((80, 24)))
    return Printer()
