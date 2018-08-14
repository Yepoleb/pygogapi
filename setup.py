from setuptools import setup

setup(
    name="gogapi",
    version="0.2",
    packages=["gogapi"],
    install_requires=[
        "requests",
        "python-dateutil"
    ],

    author="Gabriel Huber",
    author_email="huberg18@gmail.com",
    description="Python wrapper around the GOG API",
    license="MIT"
)
