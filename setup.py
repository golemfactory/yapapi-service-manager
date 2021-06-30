import setuptools  # type: ignore

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="yapapi-service-manager",
    version="0.0.0",
    author="Golem Factory, Jan Betley",
    author_email="contact@golem.network, jan.betley@golem.network",
    description="Helper tool for management of Golem-based services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://handbook.golem.network/yapapi/",
    download_url="https://github.com/golemfactory/yapapi-service-manager",
    packages=setuptools.find_packages(),
    package_data={'yapapi_service_manager': ['py.typed']},
    install_requires=["yapapi==0.6.1"],
    classifiers=[
        "Development Status :: 0 - Alpha",
        "Framework :: YaPaPI",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
    ],
    python_requires=">=3.6.1",
)
