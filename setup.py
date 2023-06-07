import pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

README = (HERE / "README.md").read_text()
INSTALL_REQUIRED = (HERE / "requirements.txt").read_text()
IMAGE_EXTRA_REQUIRED = (HERE / "image_extra_requirements.txt").read_text()
SETUP_REQUIRED = (HERE / "setup_requirements.txt").read_text()
TEST_REQUIRED = (HERE / "test_requirements.txt").read_text()

setup(
    name='weconnect-cupra-daern',
    packages=find_packages(),
    version=open("weconnect_cupra/__version.py").readlines()[-1].split()[-1].strip("\"'"),
    description='Python API for the Cupra Born online services',
    long_description=README,
    long_description_content_type="text/markdown",
    author='Till Steinbach / Alan Gibson / Stuart Hall',
    keywords='weconnect_cupra, weconnect, we connect, carnet, car net, volkswagen, vw, telemetry, cupra',
    url='https://github.com/daernsinstantfortress/WeConnect-Cupra-python',
    project_urls={
        'Funding': 'https://github.com/sponsors/tillsteinbach',
        'Source': 'https://github.com/daernsinstantfortress/WeConnect-Cupra-python',
        'Bug Tracker': 'https://github.com/daernsinstantfortress/WeConnect-Cupra-python/issues'
    },
    license='MIT',
    install_requires=INSTALL_REQUIRED,
    extras_require={
        "Images": IMAGE_EXTRA_REQUIRED,
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Software Development :: Libraries',
    ],
    python_requires='>=3.7',
    setup_requires=SETUP_REQUIRED,
    tests_require=TEST_REQUIRED,
    include_package_data=True,
    zip_safe=False,
    package_data={'': ['weconnect_cupra/api/vw/badges/*.png']}
)
