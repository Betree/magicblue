import setuptools

setuptools.setup(
    name='magicblue',
    description='Unofficial Python API to control Magic Blue bulbs over Bluetooth',
    long_description=open('README.md').read(),
    url='https://github.com/Betree/pyMagicBlue',
    author='Benjamin Piouffle',
    author_email='benjamin.piouffle@gmail.com',
    license='MIT',
    packages=['magicblue'],
    install_requires=[
        'pybluez',
        'gattlib',
        'webcolors'
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'magicblueshell = magicblue.magicblueshell:main',
        ],
    }
)
