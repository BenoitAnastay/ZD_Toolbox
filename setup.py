from setuptools import find_packages, setup
setup(
    name='zdtools',
    packages=find_packages(include=['zdtools']),
    version='0.1.2',
    description='Toolbox for wiki about a game',
    author='Benoit Anastay',
    license='Apache',
    install_requires=['pyyaml','yamlloader'],
    include_package_data=True 
)