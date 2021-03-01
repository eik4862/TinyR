from __future__ import annotations

from typing import List, Optional, Any, Callable, Tuple, Dict, final, Union, Final
from operator import add, sub, mul, mod, floordiv, truediv, pow, eq, ne, le, ge, gt, lt, and_, or_, matmul
from Error.Exception import ArrErr
from math import ceil, floor
from Core.Type import Errno
from copy import deepcopy
from CDLL.CLibrary import CLib


@final
def Strt:
    pass
