import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.package_choices import PackageChoices

from .helpers import CommandMapping, build_run


def test_path_inexistent(tmpdir):
    p = tmpdir.join('Damage 1.5.0 Installer Mac.pkg')

    package_choices = PackageChoices(p.strpath)
    with pytest.raises(ActionError):
        package_choices.process()


def test_xml_invalid(tmpdir, monkeypatch):
    kp = tmpdir.join('Damage 1.5.0 Installer Mac.pkg').ensure()
    cp = tmpdir.join('choices')

    monkeypatch.setattr(PackageChoices, 'run', build_run(
        fixture_subpath='package_choices',
        command_mappings=[
            CommandMapping(
                command=[
                    'installer', '-showChoicesAfterApplyingChangesXML', cp.strpath,
                    '-package', kp.strpath, '-target', '/'
                ],
                stdout_filename='installer_show_choices_xml_invalid.stdout'
            )
        ]
    ))
    monkeypatch.setattr('tempfile.mkstemp', lambda: (11, cp.strpath))

    package_choices = PackageChoices(kp.strpath)
    with pytest.raises(ActionError):
        package_choices.process()


def test_normal(tmpdir, monkeypatch):
    kp = tmpdir.join('Damage 1.5.0 Installer Mac.pkg').ensure()
    cp = tmpdir.join('choices')

    monkeypatch.setattr(PackageChoices, 'run', build_run(
        fixture_subpath='package_choices',
        command_mappings=[
            CommandMapping(
                command=[
                    'installer', '-showChoicesAfterApplyingChangesXML', cp.strpath,
                    '-package', kp.strpath, '-target', '/'
                ],
                stdout_filename='installer_show_choices_xml.stdout'
            )
        ]
    ))
    monkeypatch.setattr('tempfile.mkstemp', lambda: (11, cp.strpath))

    package_choices = PackageChoices(kp.strpath)
    assert package_choices.process() == ActionResponse(changed=False, data={
        'choices': [
            {
                'attributeSetting': False,
                'choiceAttribute': 'visible',
                'choiceIdentifier': 'Damage_FactoryContent'
            },
            {
                'attributeSetting': False,
                'choiceAttribute': 'enabled',
                'choiceIdentifier': 'Damage_FactoryContent'
            },
            {
                'attributeSetting': 1,
                'choiceAttribute': 'selected',
                'choiceIdentifier': 'Damage_FactoryContent'
            },
            {
                'attributeSetting': True,
                'choiceAttribute': 'visible',
                'choiceIdentifier': 'Damage_Library'
            },
            {
                'attributeSetting': False,
                'choiceAttribute': 'enabled',
                'choiceIdentifier': 'Damage_Library'
            },
            {
                'attributeSetting': 1,
                'choiceAttribute': 'selected',
                'choiceIdentifier': 'Damage_Library'
            },
            {
                'attributeSetting': '/Users/Shared',
                'choiceAttribute': 'customLocation',
                'choiceIdentifier': 'Damage_Library'
            }
        ]
    })
