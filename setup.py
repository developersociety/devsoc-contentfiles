#!/usr/bin/env python
from setuptools import find_packages, setup

setup(
    name='blanc-contentfiles',
    version='0.2.1',
    description='Blanc Content Files',
    long_description=open('README.rst').read(),
    url='https://github.com/blancltd/blanc-contentfiles',
    maintainer='Alex Tomkins',
    maintainer_email='alex@blanc.ltd.uk',
    platforms=['any'],
    packages=find_packages(),
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    license='BSD',
)
