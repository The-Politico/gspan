from setuptools import find_packages, setup

setup(
    name='gspan',
    version='0.1.0',
    description='',
    url='https://github.com/The-Politico/gspan',
    author='POLITICO interactive news',
    author_email='interactives@politico.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
    ],
    keywords='',

    packages=find_packages(exclude=['docs', 'tests']),

    install_requires=['html2text', 'copydoc', 'cement'],
    entry_points={
        'console_scripts': (
            'gspan = gspan.cli:main',
        ),
    },
    extras_require={
        'test': ['pytest'],
    },
)
