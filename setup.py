from setuptools import setup, Extension
from Cython.Build import cythonize
import cython

extensions = [
    Extension(
        name="minimax_mcts_cython",
        
    )
]