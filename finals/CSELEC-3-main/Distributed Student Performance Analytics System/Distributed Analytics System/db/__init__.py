# Makes MongoDB connection available when importing the package
from .mongodb import get_db

__all__ = ['get_db']  # Optional: controls what gets imported with `from db import *`