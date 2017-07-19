import setuptools
import re


__version__ = re.search(
    r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
    open('magicblue/__init__.py').read()
).group(1)

setuptools.setup(
    name='magicblue',
    version=__version__,
    description='Unofficial Python API to control '
                'Magic Blue bulbs over Bluetooth',
    long_description='See https://github.com/Betree/magicblue for more info',
    url='https://github.com/Betree/pyMagicBlue',
    author='Benjamin Piouffle',
    author_email='benjamin.piouffle@gmail.com',
    license='MIT',
    packages=['magicblue'],
    install_requires=[
        'bluepy==1.1.0',
        'webcolors'
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'magicblueshell = magicblue.magicblueshell:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3 :: Only',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English'
    ],
    keywords=['bluetooth', 'bulb', 'magic', 'blue', 'ble', 'iot']
)
