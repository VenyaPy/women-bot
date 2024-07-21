from setuptools import setup
from Cython.Build import cythonize
import os


def find_pyx_files(directory):
    pyx_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                pyx_files.append(os.path.join(root, file))
    return pyx_files


pyx_files = find_pyx_files("app")

setup(
    ext_modules=cythonize(pyx_files),
    script_args=["build_ext", "--inplace"]
)
