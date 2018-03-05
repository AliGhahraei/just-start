from setuptools import setup, find_packages

setup(
    name='just-start',
    version='0.2.0',
    description=('Just Start is a wrapper for Task Warrior with pomodoro'
                 ' support'),
    author='Ali Ghahraei Figueroa',
    author_email='aligf94@gmail.com',
    url='https://github.com/AliGhahraei/just-start',

    install_requires=['pexpect', 'pyyaml'],
    packages=find_packages('src'),
    package_dir={'': 'src'},

    entry_points={
        'console_scripts': ['just-start = clients.curses:main'],
    }
)
