from typing import Type, Union

NOT_SET = object()  # Sentinal used in place of None

DATA_TYPES = {
    "int": int,
    "str": str,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
}

DataType = Type[Union[int, str, float, bool, list, dict]]

def get_data_type(data_type: str) -> Type[DataType]:
    """Returns the builtin type given from the type mapping"""
    d_type = DATA_TYPES.get(data_type)
    if not d_type:
        raise AttributeError(f"Invalid data type {data_type}")
    return d_type