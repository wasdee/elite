import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.package_choices import PackageChoices

from .helpers import CommandMapping, build_run


def test_path_inexistent(tmpdir):
    p = tmpdir.join('onedrive--18.091.9506.0004.pkg')

    package_choices = PackageChoices(p.strpath)
    with pytest.raises(ActionError):
        package_choices.process()


def test_xml_invalid(tmpdir, monkeypatch):
    p = tmpdir.join('onedrive--18.091.9506.0004.pkg').ensure()

    monkeypatch.setattr(PackageChoices, 'run', build_run(
        fixture_subpath='package_choices',
        command_mappings=[
            CommandMapping(
                command=[
                    'installer', '-showChoicesXML', '-package', p.strpath, '-target', '/'
                ],
                stdout_filename='installer_show_choices_xml_invalid.stdout'
            )
        ]
    ))

    package_choices = PackageChoices(p.strpath)
    with pytest.raises(ActionError):
        package_choices.process()


def test_normal(tmpdir, monkeypatch):
    p = tmpdir.join('onedrive--18.091.9506.0004.pkg').ensure()

    monkeypatch.setattr(PackageChoices, 'run', build_run(
        fixture_subpath='package_choices',
        command_mappings=[
            CommandMapping(
                command=[
                    'installer', '-showChoicesXML', '-package', p.strpath, '-target', '/'
                ],
                stdout_filename='installer_show_choices_xml.stdout'
            )
        ]
    ))

    package_choices = PackageChoices(p.strpath)
    assert package_choices.process() == ActionResponse(changed=False, data={
        'choices': [
            {
                'childItems': [
                    {
                        'childItems': [
                            {
                                'childItems': [],
                                'choiceIdentifier': 'com.microsoft.OneDrive',
                                'choiceIsEnabled': True,
                                'choiceIsSelected': 1,
                                'choiceIsVisible': False,
                                'choiceSizeInKilobytes': 80609,
                                'pathsOfActivePackagesInChoice': [
                                    'file://localhost/Users/fots/Library/Caches/Homebrew/Cask/'
                                    'onedrive--18.091.9506.0004.pkg#OneDrive.pkg'
                                ]
                            }
                        ],
                        'choiceIdentifier': 'default',
                        'choiceIsEnabled': True,
                        'choiceIsSelected': 1,
                        'choiceIsVisible': True,
                        'choiceSizeInKilobytes': 0,
                        'pathsOfActivePackagesInChoice': []
                    }
                ],
                'choiceIdentifier': '__ROOT_CHOICE_IDENT_Microsoft OneDrive',
                'choiceIsEnabled': True,
                'choiceIsSelected': 1,
                'choiceIsVisible': True,
                'choiceSizeInKilobytes': 0,
                'choiceTitle': 'Microsoft OneDrive',
                'pathsOfActivePackagesInChoice': []
            }
        ]
    })
