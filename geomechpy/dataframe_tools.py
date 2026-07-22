"""Pandas-friendly helpers for depth-indexed geomechanics data.

The `_array` methods across GeomechPy accept plain ``list[float]`` inputs, so pandas
users can pass ``df["column"].tolist()`` directly. The helpers in this module cover the
other direction: turning lists of result dataclasses (`ElasticProperties`,
`DynamicElasticProperties`, `HorizontalStresses`, `MudWeightWindow`, ...) back into
DataFrame columns.

pandas is an optional dependency: it is only imported when one of these helpers is
called. Install it with ``pip install geomechpy[pandas]`` or ``pip install pandas``."""

from dataclasses import asdict, is_dataclass


def _require_pandas():
    """Import pandas lazily, raising a descriptive error when it is not installed."""
    try:
        import pandas
    except ImportError as error:
        raise ImportError(
            "pandas is required for geomechpy.dataframe_tools. Install it with 'pip install pandas' or 'pip install geomechpy[pandas]'"
        ) from error
    return pandas


def results_to_dataframe(results: list, index: list[float] | None = None, index_name: str = "tvd"):
    """Convert a list of GeomechPy result dataclasses into a pandas DataFrame.

    Each dataclass field becomes a column, one row per entry. Works with any of the
    library's frozen result dataclasses (`ElasticProperties`, `DynamicElasticProperties`,
    `HorizontalStresses`, `BoreholeWallStresses`, `MudWeightWindow`, ...).

    Args:
        results (list): Result dataclass instances, e.g. the output of an `_array` method. Unit: as produced by the calculation
        index (list[float] | None): Optional index values (typically the tvd used for the calculation). Must match the length of results. Defaults to None (integer index)
        index_name (str): Name given to the index when `index` is provided. Defaults to "tvd"

    Returns:
        pandas.DataFrame: One row per result, one column per dataclass field.

    Raises:
        ImportError: If pandas is not installed.
        TypeError: If entries are not dataclass instances.
        ValueError: If index and results lengths differ."""
    pandas = _require_pandas()

    for entry in results:
        if not is_dataclass(entry):
            raise TypeError(f"results must contain dataclass instances, got {type(entry).__name__}")
    if index is not None and len(index) != len(results):
        raise ValueError("index and results must have the same length")

    frame = pandas.DataFrame([asdict(entry) for entry in results])
    if index is not None:
        frame.index = pandas.Index(index, name=index_name)

    return frame


def add_results_to_dataframe(dataframe, results: list, prefix: str = ""):
    """Add the fields of a list of GeomechPy result dataclasses as columns of a DataFrame.

    Returns a copy of the input DataFrame with one new column per dataclass field,
    aligned positionally with the DataFrame rows. Useful for appending calculation
    results (e.g. dynamic moduli, horizontal stresses) next to the input log curves.

    Args:
        dataframe (pandas.DataFrame): Depth-indexed DataFrame the results belong to.
        results (list): Result dataclass instances, one per DataFrame row. Unit: as produced by the calculation
        prefix (str): Optional prefix for the new column names (e.g. "dyn_"). Defaults to ""

    Returns:
        pandas.DataFrame: Copy of the input DataFrame with the result columns appended.

    Raises:
        ImportError: If pandas is not installed.
        TypeError: If entries are not dataclass instances.
        ValueError: If the DataFrame and results lengths differ."""
    _require_pandas()

    if len(results) != len(dataframe):
        raise ValueError("dataframe and results must have the same length")

    result_frame = results_to_dataframe(results)
    output = dataframe.copy()
    for column in result_frame.columns:
        output[f"{prefix}{column}"] = result_frame[column].to_numpy()

    return output
