from setuptools import setup, find_packages

setup(
    name='just-start',
    version='0.2.0',
    description='Just Start is a wrapper for Task Warrior with pomodoro'
                ' support',
    author='Ali Ghahraei Figueroa',
    author_email='aligf94@gmail.com',
    url='https://github.com/AliGhahraei/just-start',
    license='GPLv3',

    install_requires=['pexpect', 'toml', 'urwid'],
    extras_require={
        'dev': [
            'pytest',
            'pytest-mock',
            'pytest-cov',
        ]
    },
    packages=find_packages(),
    python_requires='>=3.6',

    entry_points={
        'console_scripts': [
            'just-start-term = just_start.client_example:main',
        ],
    }
)
