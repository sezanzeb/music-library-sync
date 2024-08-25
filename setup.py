from setuptools import setup

setup(
    name="music-library-sync",
    version="0.1.0",
    description=(
        "Synchronize a directory with music with one that contains smaller formats"
        "efficiently, for example for portable devices with less storage capacity."
    ),
    author="sezanzeb",
    packages=["music_library_sync"],
    zip_safe=False,
)
