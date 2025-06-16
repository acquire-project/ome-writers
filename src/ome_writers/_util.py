from collections.abc import Iterator, Mapping
from itertools import product
from typing import cast, get_args

import numpy as np

from ome_writers import DimensionInfo, DimensionLabel

VALID_LABELS = get_args(DimensionLabel)
UNITS: dict[DimensionLabel, tuple[float, str]] = {
    "t": (1.0, "s"),
    "z": (1.0, "um"),
    "y": (1.0, "um"),
    "x": (1.0, "um"),
}


def fake_data_for_sizes(
    sizes: Mapping[str, int],
    *,
    dtype: np.typing.DTypeLike = np.uint16,
    chunk_sizes: Mapping[str, int] | None = None,
) -> tuple[Iterator[np.ndarray], list[DimensionInfo], np.dtype]:
    """Simple helper function to create a data generator and dimensions.

    Provide the sizes of the dimensions you would like to "acquire", along with the
    datatype and chunk sizes. The function will return a generator that yields
    2-D (YX) planes of data, along with the dimension information and the dtype.

    This can be passed to create_stream to create a stream for writing data.

    Parameters
    ----------
    sizes : Mapping[str, int]
        A mapping of dimension labels to their sizes. Must include 'y' and 'x'.
    dtype : np.typing.DTypeLike, optional
        The data type of the generated data. Defaults to np.uint16.
    chunk_sizes : Mapping[str, int] | None, optional
        A mapping of dimension labels to their chunk sizes. If None, defaults to 1 for
        all dimensions, besizes 'y' and 'x', which default to their full sizes.
    """
    if not {"y", "x"} <= sizes.keys():  # pragma: no cover
        raise ValueError("sizes must include both 'y' and 'x'")
    if not all(k in VALID_LABELS for k in sizes):  # pragma: no cover
        raise ValueError(
            f"Invalid dimension labels in sizes: {sizes.keys() - set(VALID_LABELS)}"
        )

    _chunk_sizes = dict(chunk_sizes or {})
    _chunk_sizes.setdefault("y", sizes["y"])
    _chunk_sizes.setdefault("x", sizes["x"])

    ordered_labels = [z for z in sizes if z not in "yx"]
    ordered_labels += ["y", "x"]
    dims = [
        DimensionInfo(
            label=lbl,
            size=sizes[lbl],
            unit=UNITS.get(lbl, None),
            chunk_size=_chunk_sizes.get(lbl, 1),
        )
        for lbl in cast("list[DimensionLabel]", ordered_labels)
    ]

    shape = [d.size for d in dims]
    dtype = np.dtype(dtype)
    if not np.issubdtype(dtype, np.integer):  # pragma: no cover
        raise ValueError(f"Unsupported dtype: {dtype}.  Must be an integer type.")

    rng = np.random.default_rng()
    data = rng.integers(0, np.iinfo(dtype).max, size=shape, dtype=dtype)

    def _build_plane_generator() -> Iterator[np.ndarray]:
        """Yield 2-D planes in y-x order."""
        if not (non_spatial_sizes := shape[:-2]):  # it's just a 2-D image
            yield data
        else:
            for idx in product(*(range(n) for n in non_spatial_sizes)):
                yield data[idx]

    return _build_plane_generator(), dims, dtype
