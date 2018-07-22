# Elite

![Build Status](https://travis-ci.org/fgimian/elite.svg?branch=master)
![Coverage Status](https://coveralls.io/repos/fgimian/elite/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

![Elite Logo](https://raw.githubusercontent.com/fgimian/elite/master/images/elite-logo.png)

Artwork courtesy of
[Open Clip Art Library](https://openclipart.org/detail/257286/cute-cartoon-butterfly)

## Introduction

Elite is an automation framework designed specifically for automating macOS based systems.
Elite implements actions to perform different tasks which may be invoked via Python code with
config data provided in YAML.

Actions are implemented in pure Python classes and also leverage PyObjC to reach into lower
level territory when configuring various aspects of the Mac operating system.

## Why Another Tool?

Although Ansible and Elite share some similarities, Elite was designed and developed to
specifically address the following points:

* **Python API** Although YAML is wonderful for config files, it falls short as a DSL for writing
  automation.  Python is fully-featured, simple and very mature.  It also has significantly more
  robust typing than Ansible's Jinja2 interpretations in YAML.
* **Mac-specific Functionality** Elite implements many Mac specific features such as aliases,
  login items, default apps and app scripting to provide customisation previously not possible in
  Ansible and other tools.
* **More Informative Output**: While running Elite-based automation code, you'll see what is
  currently running and a detailed summary of what changed and failed after a run is complete.

## Installation

Elite only works on Python 3.7 or later, and has been specifically tested with the Python release
provided by [Homebrew](https://brew.sh).

If you haven't setup Homebrew and Python, please follow the steps below:

```bash
# Install Homebrew
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)" < /dev/null

# Install Python 3.7+
brew install python3
```

You are now ready to install Elite:

```bash
pip3 install git+https://github.com/fgimian/elite.git
```

## Quick Start

A suggested directory structure of an Elite project is as follows:

```
├── macbuild.py
├── config
└── files
```

You may structure your config directory any way you like.  Personally, I like to create
sub-directories for different applications.  Elite offers various useful YAML tag functions which
allow you to include one config file in another.

e.g.

```
config/
├── software
│   ├── desktop_software
│   │   ├── 1password.yaml
│   │   ├── daisydisk.yaml
│   │   ├── dock.yaml
│   │   ├── dropbox.yaml
│   │   ├── finder.yaml
│   │   ├── flux.yaml
│   │   ├── forklift.yaml
│   │   ├── iwork.yaml
│   │   ├── microsoft_office.yaml
│   │   ├── openemu.yaml
│   │   ├── safari.yaml
│   │   ├── spotify.yaml
│   │   ├── sublime_text.yaml
│   │   ├── terminal.yaml
│   │   ├── things.yaml
│   │   └── vmware_fusion.yaml
│   │── unix_tooling
│   │   ├── bash.yaml
│   │   ├── crystal.yaml
│   │   ├── git.yaml
│   │   ├── hugo.yaml
│   │   ├── python.yaml
│   │   ├── ruby.yaml
│   │   └── unix.yaml
│   ├── dock_layout.yaml
│   ├── fonts.yaml
│   ├── launchpad_layout.yaml
│   ├── macos_general.yaml
│   ├── macos_system.yaml
│   └── taps.yaml
├── globals.yaml
└── software.yaml
```

Similarly, you can structure your files in any way you like as you have the ability to reference
any file in any location.

And your primary Python build script (in this case named macbuild.py) should be laid out as
follows:

```python
#!/usr/bin/env python3
from elite import ActionError, Config, automate


@automate()
def main(elite, printer):
    # Load a configuration file
    config = Config('config/software.yaml')

    # You may use the printer to print headings and sub-eadings
    printer.heading('Desktop Software')
    printer.info('Sublime Text')

    # You may access top level keys in your config using dot notation and
    # deeper keys as dicts
    sublime_cask_name = config.sublime_text['cask']
    elite.cask(name=sublime_cask_name, state='latest')

    # You may use the options context manager to alter the behaviour of actions
    with elite.options(sudo=True):
        # Actions return responses that you can use to take further action
        response = elite.run(command='ls -l')
        if 'scary' in response.data['stdout']:
            elite.fail(message='oh no, we better go!')


if __name__ == '__main__':
    main()
```

For a complete pattern for how Elite may be used, please see my macbuild project on GitHub
(coming soon).

## License

Elite is released under the MIT license.  Please see the
[LICENSE](https://github.com/fgimian/elite/blob/master/LICENSE) file for more details.
