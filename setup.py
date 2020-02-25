from setuptools import find_namespace_packages, setup

setup(
    name='double_click',
    version='0.1.0',
    description='Helper framework to augment Click.',
    long_description='Helper framework to augment Click.',
    url='https://github.com/WillNye/double_click',
    python_requires='>=3.7',
    install_requires=[
        'aiovast==4.0.3',
        'certifi==2019.11.28',
        'chardet==3.0.4',
        'Click==7.0',
        'colored==1.4.2',
        'idna==2.8',
        'Markdown==3.2.1',
        'mdv==1.7.4',
        'Pygments==2.5.2',
        'requests<3.0.0',
        'tabulate==0.8.6',
        'tqdm==4.35.0',
        'urllib3==1.23',
    ],
    packages=find_namespace_packages(include=['double_click', 'double_click.*']),
    package_data={'': ['*.md']},
    include_package_data=True,
    author='Will Beasley',
    author_email='willbeas88@gmail.com',
    classifiers=[
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries'
    ]
)
