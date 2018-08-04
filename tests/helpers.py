import grp
import pwd


def getpwuid(uidobj):
    if uidobj == 501:
        return pwd.struct_passwd(
            ('fots', '********', 501, 20, 'Fotis Gimian', '/Users/fots', '/bin/bash')
        )
    else:
        raise KeyError(f'getpwuid(): uid not found: {uidobj}')


def getpwnam(arg):
    if arg == 'fots':
        return pwd.struct_passwd(
            ('fots', '********', 501, 20, 'Fotis Gimian', '/Users/fots', '/bin/bash')
        )
    else:
        raise KeyError(f'getpwnam(): name not found: {arg}')


def getgrnam(name):
    if name == 'staff':
        return grp.struct_group(('staff', '*', 20, ['root']))
    else:
        raise KeyError(f'getgrnam(): name not found: {name}')
