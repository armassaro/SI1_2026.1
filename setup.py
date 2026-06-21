from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        "ai",
        ["ai.pyx"],
        extra_compile_args=["-O3", "-march=native", "-ffast-math", "-funroll-loops"],
        extra_link_args=["-O3"],
    )
]

setup(
    name="minimax_mcts_cython",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "nonecheck": False,
            "cdivision": True,
            "initializedcheck": False,
            "infer_types": True,
            "optimize.use_switch": True,
            "optimize.unpack_method_calls": True,
        },
    ),
)
