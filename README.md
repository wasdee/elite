# Elite

![License](https://img.shields.io/badge/license-Proprietary-blue.svg)

![Elite Logo](https://gitlab.com/macbuild/elite/raw/master/images/elite-logo.png)

Artwork courtesy of
[Open Clip Art Library](https://openclipart.org/detail/257286/cute-cartoon-butterfly)

## Introduction

Elite is an automation framework designed specifically for automating macOS
based systems.  Elite implements actions to perform different tasks which may
be invoked via Python code with config data provided in YAML.

Actions are implemented via a simple Pythonic API and also leverage PyObjC
to reach into lower level territory when configuring various aspects of
the mac operating system.

## Why Another Tool?

Although Ansible and Elite share some similarities, Elite was designed
and developed to specifically address the following points:

* **Python API** Although YAML is wonderful for config files, it falls short
  as a DSL for writing automation.  Python is fully-featured, simple and
  very mature.  It also has significantly more robust typing than Ansible's
  Jinja2 interpretations in YAML.
* **Mac-specific Functionality** Elite implements many Mac specific features
  such as aliases, login items, default apps and app scripting to provide
  customisation previously not possible in Ansible and other tools.
* **More Informative Output**: While running Elite-based automation code,
  you'll see what is currently running and a detailed summary of what changed
  and failed after a run is complete.

## Installation

```bash
pip install git+ssh://git@gitlab.com/fgimian/elite.git
```

## Quick Start

The directory structure of an Elite project should be similar to the following:

```
├── macbuild.sh
├── build.py
├── roles
│   ├── __init__.py
│   ├── role1.py
│   ├── role2.py
│   └── role3.py
├── config
│   ├── settings1.yaml
│   ├── settings2.yaml
│   └── settings3.yaml
└── files
    ├── role1
    │   ├── file1
    │   ├── file2
    │   └── file3
    ├── role2
    └── role3
```

Some notes about this structure:

* You may place any number of YAML files in the config directory and they will
  be recursively read and merged into one large YAMl structure which will be
  passed in as a named tuple under the config variable.
* You may name all files and directories whatever you like as you will have
  full control over importing them and/or referring to them in your Python
  build script (which also may be named whatever you like).

The main Bootstrap shell script which is executed first should look something
like this:

```bash
#!/bin/bash

# Prompt the user for their sudo password
sudo -v

# Enable passwordless sudo for the macbuild run
sudo sed -i -e "s/^%admin.*/%admin  ALL=(ALL) NOPASSWD: ALL/" /etc/sudoers

# Install Homebrew
if ! which brew > /dev/null 2>&1
then
    ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)" < /dev/null
fi

# Install Python
if ! brew list python3 > /dev/null 2>&1
then
    brew install python3
fi

# Install PyObjC dependencies
for package in \
    pyobjc-framework-Cocoa \
    pyobjc-framework-LaunchServices \
    pyobjc-framework-ScriptingBridge
do
    if ! pip3 show "$package" > /dev/null 2>&1
    then
        pip3 install "$package"
    fi
done

# Perform the build
./build.py

# Disable passwordless sudo after the macbuild is complete
sudo sed -i -e "s/^%admin.*/%admin  ALL=(ALL) ALL/" /etc/sudoers
```

And your primary Python build script (in this case named build.py) should
be laid out as follows:

```python
from elite.decorators import elite_main


@elite_main(config_path='config')
def main(elite, config, printer):
    # Use the elite object to call actions with configuration from the
    # config object.  Use the printer object to print info about what
    # each set of actions is doing.
    pass


if __name__ == '__main__':
    main()
```

## License

Elite is proprietary software and may not be copied and/or distributed without
the express written permission of Fotis Gimian.
