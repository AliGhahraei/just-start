from setuptools import setup, find_packages

setup(
    name='just-start',
    version='0.4.0',
    description='Just Start is a wrapper for Task Warrior with pomodoro'
                ' support',
    author='Ali Ghahraei Figueroa',
    author_email='aligf94@gmail.com',
    url='https://github.com/AliGhahraei/just-start',
    license='GPLv3',

    install_requires=['pexpect', 'toml'],
    extras_require={
        'dev': [
            'pytest',
            'pytest-mock',
            'pytest-cov',
        ],
        # Just to be "installable" like the other clients
        'term': [],
        'urwid': ['urwid'],
    },
    packages=find_packages(),
    python_requires='>=3.6',

    entry_points={
        'console_scripts': [
            'just-start-term = just_start.client_example:main[term]',
            'just-start-urwid = just_start_urwid:main[urwid]',
        ],
    }
)
