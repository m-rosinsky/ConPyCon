from pathlib import Path
from setuptools import find_packages, setup

# Get ConPyCon version.
version = (Path(__file__).parent / "conpycon/VERSION").read_text('ascii').strip()

install_requires = [

]

setup(
    name='ConPyCon',
    version=version,
    url='',
    project_urls={
        'Docs': '',
        'Source': 'https://github.com/m-rosinsky/ConPyCon',
        'Tracker': '',
    },
    description='A Configurable Python Console',
    long_description=open('README.md', encoding='utf-8').read(),
    author='Mike Rosinsky',
    author_email='rosinskymike@gmail.com',
    maintainer='Mike Rosinsky',
    maintainer_email='rosinskymike@gmail.com',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={},
    python_requires='>=3.7',
    install_requires=install_requires,
)
