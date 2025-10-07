"""
PokerTool compatibility layer for PyTorch.

When a native torch installation is available the module delegates every import
to the upstream package.  In lightweight environments (e.g., CI without GPU
support) a minimal NumPy-backed stub is provided so dependant modules can be
imported and tested.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import site
import sys
from pathlib import Path
from typing import Iterable, Tuple, Union

import numpy as np
from contextlib import contextmanager
import types


STUB_ROOT = Path(__file__).resolve().parent


def _candidate_paths() -> Iterable[str]:
    paths = []
    try:
        paths.extend(site.getsitepackages())
    except Exception:  # pragma: no cover - environment specific
        pass
    try:
        user_site = site.getusersitepackages()
        if user_site:
            paths.append(user_site)
    except Exception:  # pragma: no cover - environment specific
        pass
    for entry in sys.path:
        if not entry:
            continue
        entry_path = Path(entry).resolve()
        # Skip the repository path hosting the stub to avoid recursion.
        if STUB_ROOT in entry_path.parents or entry_path == STUB_ROOT:
            continue
        paths.append(str(entry_path))
    return paths


def _load_real_torch():
    for root in _candidate_paths():
        try:
            spec = importlib.machinery.PathFinder.find_spec("torch", [root])
        except Exception:  # pragma: no cover - safety belt
            spec = None
        if not spec or not spec.loader:
            continue
        origin_path = Path(spec.origin or "")
        if origin_path == Path(__file__):
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[__name__] = module
        return module
    return None


_REAL_TORCH = _load_real_torch()
if _REAL_TORCH is not None:
    globals().update(_REAL_TORCH.__dict__)
    _POKERTOOL_STUB = False
    __all__ = getattr(_REAL_TORCH, "__all__", [])
else:
    _POKERTOOL_STUB = True

    Number = Union[int, float]

    class Tensor:
        """Thin wrapper over ``np.ndarray`` exposing a subset of torch.Tensor."""

        def __init__(self, data: Union[np.ndarray, Iterable[Number]]) -> None:
            self._array = np.asarray(data, dtype=np.float32)

        @property
        def shape(self) -> Tuple[int, ...]:
            return tuple(self._array.shape)

        def numpy(self) -> np.ndarray:
            return self._array.copy()

        def view(self, *shape: int) -> "Tensor":
            return Tensor(self._array.reshape(shape))

        def reshape(self, *shape: int) -> "Tensor":
            return Tensor(self._array.reshape(shape))

        def astype(self, dtype) -> "Tensor":
            return Tensor(self._array.astype(dtype))

        def __array__(self, dtype=None) -> np.ndarray:
            return self._array.astype(dtype) if dtype else self._array

        def __repr__(self) -> str:  # pragma: no cover - debugging helper
            return f"Tensor(shape={self.shape})"

    def randn(*shape: int, dtype=np.float32) -> Tensor:
        return Tensor(np.random.randn(*shape).astype(dtype))

    def zeros(shape: Union[Tuple[int, ...], Iterable[int]], dtype=np.float32) -> Tensor:
        return Tensor(np.zeros(tuple(shape), dtype=dtype))

    @contextmanager
    def no_grad():
        yield

    class _Module:
        def __init__(self) -> None:
            self.training = True

        def eval(self) -> None:
            self.training = False

        def forward(self, *args, **kwargs):  # pragma: no cover - interface
            raise NotImplementedError

        def __call__(self, *args, **kwargs):
            return self.forward(*args, **kwargs)

    class _Sequential(_Module):
        def __init__(self, *modules):
            super().__init__()
            self.modules = modules

        def forward(self, input_tensor: Tensor) -> Tensor:
            output = input_tensor
            for module in self.modules:
                output = module(output)
            return output

    class _Identity(_Module):
        def forward(self, input_tensor: Tensor) -> Tensor:
            return input_tensor

    class _PassThroughModule(_Module):
        def __init__(self, *args, **kwargs):
            super().__init__()

        def forward(self, input_tensor: Tensor) -> Tensor:
            return input_tensor

    class _ReLU(_Module):
        def __init__(self, inplace: bool = False):
            super().__init__()
            self.inplace = inplace

        def forward(self, input_tensor: Tensor) -> Tensor:
            array = np.array(input_tensor)
            np.maximum(array, 0, out=array)
            return Tensor(array)

    class _AdaptiveAvgPool2d(_Module):
        def __init__(self, output_size):
            super().__init__()
            self.output_size = output_size

        def forward(self, input_tensor: Tensor) -> Tensor:
            batch, channels, *_ = input_tensor.shape
            height, width = self.output_size
            pooled = np.zeros((batch, channels, height, width), dtype=np.float32)
            return Tensor(pooled)

    class _Flatten(_Module):
        def forward(self, input_tensor: Tensor) -> Tensor:
            array = np.array(input_tensor)
            batch = array.shape[0]
            flattened = array.reshape(batch, -1)
            return Tensor(flattened)

    class _Linear(_Module):
        def __init__(self, in_features: int, out_features: int):
            super().__init__()
            self.out_features = out_features

        def forward(self, input_tensor: Tensor) -> Tensor:
            batch = input_tensor.shape[0]
            return Tensor(np.zeros((batch, self.out_features), dtype=np.float32))

    _nn_module = types.ModuleType("torch.nn")
    _nn_module.Module = _Module
    _nn_module.Sequential = _Sequential
    _nn_module.Identity = _Identity
    _nn_module.Conv2d = _PassThroughModule
    _nn_module.BatchNorm2d = _PassThroughModule
    _nn_module.ReLU = _ReLU
    _nn_module.MaxPool2d = _PassThroughModule
    _nn_module.AdaptiveAvgPool2d = _AdaptiveAvgPool2d
    _nn_module.Flatten = _Flatten
    _nn_module.Linear = _Linear

    sys.modules[__name__ + ".nn"] = _nn_module
    nn = _nn_module

    __all__ = [
        "Tensor",
        "randn",
        "zeros",
        "no_grad",
        "nn",
    ]
