from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="stingray_cli",
    version='2.1.1',
    author="Stingray Technologies LLC",
    description="Stingray cli package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Swordfish-Security/stingray_cli",
    packages=find_packages(),
    author_email='stingray@appsec.global',
    include_package_data=True,
    install_requires=[
         'requests > 2.20',
         'stingray_cli_core == 2.1.3'
    ],
    entry_points ={
            'console_scripts': [
                'stingray_cli=stingray_cli.run_stingray_scan:main'
            ]
        },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
    ],
)
