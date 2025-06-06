"""torch_xla.backends controls the behavior of the XLA backend.

This subpackage parallels the torch.backends.{cuda, cpu, mps, etc}
subpackages in PyTorch.
"""

# See https://github.com/pytorch/pytorch/blob/main/torch/backends/mps/__init__.py
# for an example of how backends are implemented in PyTorch
# in the __init__.py file, despite general style guidelines against this.

# Literal is available from Python 3.8,
# matching the Python versions for PyTorch and PyTorch/XLA.
import logging
from typing import Final, Literal, TypeAlias

import torch_xla

# TODO: Refactor logging in torch_xla package https://github.com/pytorch/xla/issues/9142
logger = logging.getLogger(__name__)
_WARNING_MESSAGE: Final[str] = (
    'Setting mat mul precision multiple times is not '
    'recommended. If you need to do so, please empirically '
    'verify that the precision setting is behaving as expected.')

__all__ = ["set_mat_mul_precision", "get_mat_mul_precision"]

# Valid values for get_mat_mul_precision/set_mat_mul_precision
# Note: it is idiomatic to PyTorch to use strings rather than enums.
# See https://github.com/pytorch/pytorch/blob/v2.7.0/torch/backends/cpu/__init__.py#L9

_DEFAULT: Final = "default"
_HIGH: Final = "high"
_HIGHEST: Final = "highest"

# Use of variables with Final typehint instead of literals is valid.
_PrecisionType: TypeAlias = Literal[
    _DEFAULT, _HIGH, _HIGHEST]  # pyright: ignore[reportInvalidTypeForm]


# Some of this description adapted from Jax documentation.
def set_mat_mul_precision(precision: _PrecisionType) -> None:
  """Control the default mat mul and conv precision for 32bit inputs.

    Some platforms, like TPU, offer configurable precision levels for
    matrix multiplication and convolution computations,
    trading off accuracy for speed.

    This option controls the default precision level for
    computations involved in matrix multiplication and convolutions on
    32bit inputs. The levels describe the precision at
    which scalar products are computed.

    On a TPU:
      `default` is the fastest and least precise,
      downcasting an FP32 to BF16 before multiplying.

      `high` takes three passes and generates approximately 14 bits of
      precision.

      `highest` is the most precise, and the slowest. It takes six
      passes and generates approximately 22 bits of precision.

    See the [precision tutorial](../../tutorials/precision_tutorial.html)
    for more information about the precision levels.

    Note: Setting mat mul precision multiple times is not recommended.
      If you need to do so, please empirically verify that the precision
      setting is behaving as expected.

    Args:
      precision (str): The precision to set for matrix multiplication.
        Must be one of 'default', 'high', or 'highest'.
    """
  if precision not in [_DEFAULT, _HIGH, _HIGHEST]:
    raise ValueError(f"Invalid precision: {precision}. "
                     f"Must be one of {_DEFAULT}, {_HIGH}, {_HIGHEST}.")

  logger.warning(_WARNING_MESSAGE)

  torch_xla._XLAC._xla_set_mat_mul_precision(precision)


def get_mat_mul_precision() -> _PrecisionType:
  """Get the current mat mul precision for 32bit inputs.

    See the [precision tutorial](../../tutorials/precision_tutorial.html)
    for more information about the precision levels.

    Returns:
        str: The current precision setting for matrix multiplication,
            one of 'default', 'high', or 'highest'.
    """
  precision = torch_xla._XLAC._xla_get_mat_mul_precision()
  assert precision in [_DEFAULT, _HIGH, _HIGHEST
                      ], (f"Invalid precision: {precision}. "
                          f"Must be one of {_DEFAULT}, {_HIGH}, {_HIGHEST}.")
  return precision
