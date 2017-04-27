import setuptools
from magicblue import __version__

setuptools.setup(
    name='magicblue',
    version=__version__,
    description='Unofficial Python API to control '
                'Magic Blue bulbs over Bluetooth',
    long_description=open('README.md').read(),
    url='https://github.com/Betree/pyMagicBlue',
    author='Benjamin Piouffle',
    author_email='benjamin.piouffle@gmail.com',
    license='MIT',
    packages=['magicblue'],
    install_requires=[
        'pygatt==3.1.1',
        'webcolors'
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'magicblueshell = magicblue.magicblueshell:main',
        ],
    }
)
