from setuptools import find_namespace_packages, setup

with open('README.md', 'r') as long_desc:
    long_description = long_desc.read()

setup(
    name='double_click',
    version='0.2.12',
    description='Helper framework to augment Click.',
    long_description='Helper framework to augment Click.',
    url='https://github.com/WillNye/double_click',
    python_requires='>=3.7',
    install_requires=[
        'certifi==2019.11.28',
        'chardet==3.0.4',
        'colored==1.4.2',
        'idna==2.9',
        'Markdown==3.2.1',
        'mdv==1.7.4',
        'Pygments==2.5.2',
        'requests<3.0.0',
        'tabulate==0.8.6',
        'tqdm==4.43.0',
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
