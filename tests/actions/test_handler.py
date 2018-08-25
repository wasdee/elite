from unittest import mock

import pytest
from elite.actions import ActionError, ActionResponse
from elite.actions.handler import Handler


kLSRolesAll = 4294967295


def test_invalid_content_type_url_scheme_empty_combination():
    with pytest.raises(ValueError):
        Handler(path='/Applications/Sublime Text.app')


def test_invalid_content_type_empty_after_init():
    handler = Handler(path='/Applications/Sublime Text.app', content_type='public.plain-text')
    with pytest.raises(ValueError):
        handler.content_type = None


def test_invalid_url_scheme_empty_after_init():
    handler = Handler(path='/Applications/Safari.app', url_scheme='http')
    with pytest.raises(ValueError):
        handler.url_scheme = None


def test_invalid_content_type_url_scheme_combination():
    with pytest.raises(ValueError):
        Handler(
            path='/Applications/Safari.app',
            content_type='public.plain-text',
            url_scheme='http'
        )


def test_invalid_content_type_after_init():
    handler = Handler(path='/Applications/Safari.app', url_scheme='http')
    with pytest.raises(ValueError):
        handler.content_type = 'public.plain-text'


def test_invalid_url_scheme_after_init():
    handler = Handler(path='/Applications/Sublime Text.app', content_type='public.plain-text')
    with pytest.raises(ValueError):
        handler.url_scheme = 'public.plain-text'


@mock.patch('elite.actions.handler.NSBundle')
def test_invalid_bundle_path(bundle_mock):
    bundle_mock.bundleWithPath_.return_value = None

    handler = Handler(path='/Applications/Boo.app', content_type='public.plain-text')
    with pytest.raises(ActionError):
        handler.process()

    assert bundle_mock.bundleWithPath_.call_args == mock.call('/Applications/Boo.app')


@mock.patch('elite.actions.handler.LSCopyDefaultRoleHandlerForContentType')
@mock.patch('elite.actions.handler.NSBundle')
def test_invalid_content_type(bundle_mock, copy_content_type_mock):
    bundle_mock.bundleWithPath_().bundleIdentifier.return_value = 'com.sublimetext.3'
    copy_content_type_mock.return_value = None

    handler = Handler(path='/Applications/Sublime Text.app', content_type='public.boo')
    with pytest.raises(ActionError):
        handler.process()

    assert bundle_mock.bundleWithPath_.call_args == mock.call('/Applications/Sublime Text.app')
    assert copy_content_type_mock.call_args == mock.call('public.boo', kLSRolesAll)


@mock.patch('elite.actions.handler.LSCopyDefaultRoleHandlerForContentType')
@mock.patch('elite.actions.handler.NSBundle')
def test_content_type_same(bundle_mock, copy_content_type_mock):
    bundle_mock.bundleWithPath_().bundleIdentifier.return_value = 'com.sublimetext.3'
    copy_content_type_mock.return_value = 'com.sublimetext.3'

    handler = Handler(path='/Applications/Sublime Text.app', content_type='public.plain-text')
    assert handler.process() == ActionResponse(changed=False)
    assert bundle_mock.bundleWithPath_.call_args == mock.call('/Applications/Sublime Text.app')
    assert copy_content_type_mock.call_args == mock.call('public.plain-text', kLSRolesAll)


@mock.patch('elite.actions.handler.LSSetDefaultRoleHandlerForContentType')
@mock.patch('elite.actions.handler.LSCopyDefaultRoleHandlerForContentType')
@mock.patch('elite.actions.handler.NSBundle')
def test_content_type_different(bundle_mock, copy_content_type_mock, set_content_type_mock):
    bundle_mock.bundleWithPath_().bundleIdentifier.return_value = 'com.sublimetext.3'
    copy_content_type_mock.return_value = 'com.apple.TextEdit'

    handler = Handler(path='/Applications/Sublime Text.app', content_type='public.plain-text')
    assert handler.process() == ActionResponse(changed=True)
    assert copy_content_type_mock.call_args == mock.call('public.plain-text', kLSRolesAll)
    assert set_content_type_mock.call_args == mock.call(
        'public.plain-text', kLSRolesAll, 'com.sublimetext.3'
    )


@mock.patch('elite.actions.handler.LSCopyDefaultHandlerForURLScheme')
@mock.patch('elite.actions.handler.NSBundle')
def test_invalid_url_scheme(bundle_mock, copy_url_scheme_mock):
    bundle_mock.bundleWithPath_().bundleIdentifier.return_value = 'com.apple.Safari'
    copy_url_scheme_mock.return_value = None

    handler = Handler(path='/Applications/Safari.app', url_scheme='hwow')
    with pytest.raises(ActionError):
        handler.process()

    assert bundle_mock.bundleWithPath_.call_args == mock.call('/Applications/Safari.app')
    assert copy_url_scheme_mock.call_args == mock.call('hwow')


@mock.patch('elite.actions.handler.LSCopyDefaultHandlerForURLScheme')
@mock.patch('elite.actions.handler.NSBundle')
def test_url_scheme_same(bundle_mock, copy_url_scheme_mock):
    bundle_mock.bundleWithPath_().bundleIdentifier.return_value = 'com.apple.Safari'
    copy_url_scheme_mock.return_value = 'com.apple.Safari'

    handler = Handler(path='/Applications/Safari.app', url_scheme='http')
    assert handler.process() == ActionResponse(changed=False)
    assert bundle_mock.bundleWithPath_.call_args == mock.call('/Applications/Safari.app')
    assert copy_url_scheme_mock.call_args == mock.call('http')


@mock.patch('elite.actions.handler.LSSetDefaultHandlerForURLScheme')
@mock.patch('elite.actions.handler.LSCopyDefaultHandlerForURLScheme')
@mock.patch('elite.actions.handler.NSBundle')
def test_url_scheme_different(bundle_mock, copy_url_scheme_mock, set_url_scheme_mock):
    bundle_mock.bundleWithPath_().bundleIdentifier.return_value = 'com.apple.Safari'
    copy_url_scheme_mock.return_value = 'org.mozilla.firefox'

    handler = Handler(path='/Applications/Safari.app', url_scheme='http')
    assert handler.process() == ActionResponse(changed=True)
    assert copy_url_scheme_mock.call_args == mock.call('http')
    assert set_url_scheme_mock.call_args == mock.call('http', 'com.apple.Safari')
