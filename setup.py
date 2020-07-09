from setuptools import find_namespace_packages, setup

with open('requirements.txt', 'r') as f:
    install_requires = f.read().replace(' ', '').split('\n')

setup(
    name='double_click',
    version='0.2.14',
    description='Helper framework to augment Click.',
    long_description='Helper framework to augment Click.',
    url='https://github.com/WillNye/double_click',
    python_requires='>=3.7',
    install_requires=install_requires,
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
