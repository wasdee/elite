from setuptools import setup


setup(
    name='elite',
    version='0.4.0',
    url='https://github.com/fgimian/elite',
    license='MIT',
    author='Fotis Gimian',
    author_email='fgimiansoftware@gmail.com',
    description='An automation framework specifically built for Mac automation.',
    packages=['elite'],
    install_requires=[
        'ruamel.yaml',
        'pyobjc-framework-Cocoa',
        'pyobjc-framework-LaunchServices',
        'pyobjc-framework-ScriptingBridge',
        'rarfile'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities'
    ]
)
