import grp
import pwd


def getpwuid(uidobj):
    if uidobj == 501:
        return pwd.struct_passwd(
            ('fots', '********', 501, 20, 'Fotis Gimian', '/Users/fots', '/bin/bash')
        )
    elif uidobj == 502:
        return pwd.struct_passwd(
            ('happy', '********', 502, 20, 'Happy Man', '/Users/happy', '/bin/bash')
        )
    else:
        raise KeyError(f'getpwuid(): uid not found: {uidobj}')


def getpwnam(arg):
    if arg == 'fots':
        return pwd.struct_passwd(
            ('fots', '********', 501, 20, 'Fotis Gimian', '/Users/fots', '/bin/bash')
        )
    elif arg == 'happy':
        return pwd.struct_passwd(
            ('happy', '********', 502, 20, 'Happy Man', '/Users/happy', '/bin/bash')
        )
    else:
        raise KeyError(f'getpwnam(): name not found: {arg}')


def getgrnam(name):
    if name == 'staff':
        return grp.struct_group(('staff', '*', 20, ['root']))
    elif name == 'wheel':
        return grp.struct_group(('wheel', '*', 0, ['root']))
    else:
        raise KeyError(f'getgrnam(): name not found: {name}')
