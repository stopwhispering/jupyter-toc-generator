import setuptools
from jupyter_toc_generator import __version__, __author__

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="jupyter-toc-generator",  # Desired PyPi Package Name
    version=__version__,
    author=__author__,
    description="Generate a table of contents incl. links and anchor tags in a Jupyter Notebook.",
    long_description=long_description,  # see above
    long_description_content_type="text/markdown",
    url="https://github.com/stopwhispering/jupyter-toc-generator",
    packages=setuptools.find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'generate_toc = jupyter_toc_generator.main:main',
        ],
    },
    # scripts=['generate_toc.py'],
    install_requires=[
        'pyperclip',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
