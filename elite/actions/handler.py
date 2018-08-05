from Foundation import NSBundle  # pylint: disable=no-name-in-module
from LaunchServices import (  # pylint: disable=no-name-in-module
    LSCopyDefaultHandlerForURLScheme, LSCopyDefaultRoleHandlerForContentType,
    LSSetDefaultHandlerForURLScheme, LSSetDefaultRoleHandlerForContentType, kLSRolesAll
)

from . import Action, ActionError


class Handler(Action):
    def __init__(self, path, content_type=None, url_scheme=None, **kwargs):
        self._content_type = content_type
        self._url_scheme = url_scheme
        self.path = path
        self.content_type = content_type
        self.url_scheme = url_scheme
        super().__init__(**kwargs)

    @property
    def content_type(self):
        return self._content_type

    @content_type.setter
    def content_type(self, content_type):
        if not content_type and not self.url_scheme:
            raise ValueError("you must specify one of 'content_type' or 'url_scheme'")
        if content_type and self.url_scheme:
            raise ValueError("you may only specify one of 'content_type' or 'url_scheme'")
        self._content_type = content_type

    @property
    def url_scheme(self):
        return self._url_scheme

    @url_scheme.setter
    def url_scheme(self, url_scheme):
        if not self.content_type and not url_scheme:
            raise ValueError("you must specify one of 'content_type' or 'url_scheme'")
        if self.content_type and url_scheme:
            raise ValueError("you may only specify one of 'content_type' or 'url_scheme'")
        self._url_scheme = url_scheme

    def process(self):
        # Determine the bundle_id of the app path provided
        bundle = NSBundle.bundleWithPath_(self.path)
        if not bundle:
            raise ActionError('unable to locate the bundle id of the app path provided')

        bundle_id = bundle.bundleIdentifier()

        # The user is trying to change the default application for a content type
        if self.content_type:
            # Get the default bundle id for the specified content type
            default_bundle_id = LSCopyDefaultRoleHandlerForContentType(
                self.content_type, kLSRolesAll
            )
            if not default_bundle_id:
                raise ActionError('the content type provided could not be found')

            # The current default application matches the one requested
            if default_bundle_id.lower() == bundle_id.lower():
                return self.ok()

            # Change the default application for the specified content type
            LSSetDefaultRoleHandlerForContentType(self.content_type, kLSRolesAll, bundle_id)
            return self.changed()

        # The user is trying to change the default application for a URL scheme
        else:
            # Get the default bundle id for the specified url scheme
            default_bundle_id = LSCopyDefaultHandlerForURLScheme(self.url_scheme)
            if not default_bundle_id:
                raise ActionError('the url scheme provided could not be found')

            # The current default application matches the one requested
            if default_bundle_id.lower() == bundle_id.lower():
                return self.ok()

            # Change the default application for the specified url scheme
            LSSetDefaultHandlerForURLScheme(self.url_scheme, bundle_id)
            return self.changed()
