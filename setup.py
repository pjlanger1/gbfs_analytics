from setuptools import setup, find_packages

setup(
    name="gbfs_analytics",  # Replace with your package name
    version="0.1.5",  # Initial release version
    author="transit ventures limited",
    author_email="hello@bikewatch.nyc",
    description="tools for polling and analytics on generalized bikeshare feed specification (gbfs) v 2.3 feeds",
    long_description=open("gbfs_analytics/README.md").read(),  # Use README.md as long description
    long_description_content_type="text/markdown",  # Required if using Markdown for long description
    url="https://www.bikewatch.nyc",  # Your package's GitHub or other homepage
    packages=find_packages(),  # Automatically find your package
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",  # Apache2.0
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",  # Specify the minimum Python version
    install_requires=[
    "requests>=2.25.0",  
    "schedule>=1.0.0"
    ],
)
