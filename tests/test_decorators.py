import pytest
from elite.config import ConfigError
from elite.decorators import automate
from tests import helpers


def test_automate_normal(capsys, monkeypatch):
    helpers.patch_root_runtime(monkeypatch)

    @automate()
    def main(elite, printer):  # pylint: disable=unused-argument
        pass

    # Disabling parameter checks as pylint has a bug with relation to decorators
    # https://github.com/PyCQA/pylint/issues/259
    # pylint: disable=no-value-for-parameter
    main()
    captured = capsys.readouterr()
    assert 'Summary' in captured.out


def test_automate_elite_config_error(capsys, monkeypatch):
    helpers.patch_root_runtime(monkeypatch)

    @automate()
    def main(elite, printer):  # pylint: disable=unused-argument
        raise ConfigError('the top level of your config must contain key-value pairs')

    with pytest.raises(SystemExit) as exc_info:
        # pylint: disable=no-value-for-parameter
        main()

    captured = capsys.readouterr()
    assert 'Config Error: the top level of your config must contain key-value pairs' in captured.out
    assert exc_info.value.code == 1


def test_automate_elite_runtime_error_non_root(capsys):
    @automate()
    def main(elite, printer):  # pylint: disable=unused-argument
        pass

    with pytest.raises(SystemExit) as exc_info:
        # pylint: disable=no-value-for-parameter
        main()

    captured = capsys.readouterr()
    assert (
        'Elite Runtime Error: elite must be run using sudo via a regular user account' in
        captured.out
    )
    assert exc_info.value.code == 1


def test_automate_elite_error(capsys, monkeypatch):
    helpers.patch_root_runtime(monkeypatch)

    @automate()
    def main(elite, printer):  # pylint: disable=unused-argument
        elite.fail('boo')

    with pytest.raises(SystemExit) as exc_info:
        # pylint: disable=no-value-for-parameter
        main()

    captured = capsys.readouterr()
    assert 'Summary' in captured.out
    assert exc_info.value.code == 1


def test_automate_ctrl_c(capsys, monkeypatch):
    helpers.patch_root_runtime(monkeypatch)

    @automate()
    def main(elite, printer):  # pylint: disable=unused-argument
        raise KeyboardInterrupt

    with pytest.raises(SystemExit) as exc_info:
        # pylint: disable=no-value-for-parameter
        main()

    captured = capsys.readouterr()
    assert 'Processing aborted as requested by keyboard interrupt.' in captured.out
    assert exc_info.value.code == 1
