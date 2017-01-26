from Foundation import NSBundle
from LaunchServices import (
    LSCopyDefaultRoleHandlerForContentType, LSSetDefaultRoleHandlerForContentType,
    LSCopyDefaultHandlerForURLScheme, LSSetDefaultHandlerForURLScheme, kLSRolesAll
)

from . import Argument, Action


class Handler(Action):
    def validate_args(self, path, content_type, url_scheme):
        if not content_type and not url_scheme:
            self.fail("you must specify one of 'content_type' or 'url_scheme'")

        if content_type and url_scheme:
            self.fail("you may only specify one of 'content_type' or 'url_scheme'")

    def process(self, path, content_type, url_scheme):
        # Determine the bundle_id of the app path provided
        bundle = NSBundle.bundleWithPath_(path)
        if not bundle:
            self.fail('unable to locate the bundle id of the app path provided')

        bundle_id = bundle.bundleIdentifier()

        # The user is trying to change the default application for a content type
        if content_type:
            # Get the default bundle id for the specified content type
            default_bundle_id = LSCopyDefaultRoleHandlerForContentType(content_type, kLSRolesAll)
            if not default_bundle_id:
                self.fail('the content type provided could not be found')

            # The current default application matches the one requested
            if default_bundle_id.lower() == bundle_id.lower():
                self.ok()

            # Change the default application for the specified content type
            LSSetDefaultRoleHandlerForContentType(
                content_type, kLSRolesAll, bundle_id
            )
            self.changed()

        # The user is trying to change the default application for a URL scheme
        else:
            # Get the default bundle id for the specified url scheme
            default_bundle_id = LSCopyDefaultHandlerForURLScheme(url_scheme)
            if not default_bundle_id:
                self.fail('the url scheme provided could not be found')

            # The current default application matches the one requested
            if default_bundle_id.lower() == bundle_id.lower():
                self.ok()

            # Change the default application for the specified url scheme
            LSSetDefaultHandlerForURLScheme(url_scheme, bundle_id)
            self.changed()


if __name__ == '__main__':
    handler = Handler(
        Argument('path'),
        Argument('content_type', optional=True),
        Argument('url_scheme', optional=True)
    )
    handler.invoke()
