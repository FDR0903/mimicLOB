import setuptools
import mimicLOB

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name= mimicLOB.__name__,
    version= mimicLOB.__version__,
    author="Fayçal DRISSI",
    author_email="FDR0903.DEV@gmail.com",
    description="Simulation at the LOB level",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)