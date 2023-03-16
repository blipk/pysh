import lzma
from streamlit.runtime.uploaded_file_manager import UploadedFile, UploadedFileRec
from typing import Any, Optional
import pysh


def decode(obj: Any, force_type: Optional[str] = None) -> Any:
    try:
        obj = lzma.decompress(obj)
    except:
        pass

    if "__serialized_type__" in obj:
        type = obj["__serialized_type__"]

        if type == "BashBlock" or force_type == "BashBlock":
            obj = pysh.BashBlock(**obj["class_dict"])
    return obj


def type_check(obj, class_ref, class_str, force_type=None):
    """
    isinstance and is class are failing across threads when they shouldn't.
    Possibly to do with PYTHONHASHSEED or import hierarchy.

    obj.__class__.__name__ seems to work best
    """
    # print(obj.__dict__)
    # print(vars(obj))
    # print(obj.__class__)
    # print(obj.__class__.__name__)
    # print( obj.__name__,)

    return isinstance(obj, class_ref) \
        or type(obj) is type(class_ref) \
        or type(obj) is class_ref \
        or (hasattr(obj, "__class__") and obj.__class__ is class_ref) \
        or (hasattr(obj, "__class__") and hasattr(obj.__class__, "__name__") and obj.__class__.__name__ == class_str) \
        or force_type == class_str


def encode(obj: Any, force_type: Optional[str] = None) -> Any:
    serialized = None

    if type_check(obj, pysh.BashBlock, "BashBlock", force_type):
        attr_dict = obj.__dict__.copy()
        del attr_dict["pysh"]
        del attr_dict["pipe"]
        attr_dict["serialized"] = True
        serialized = {
            "__serialized_type__": "BashBlock",
            "class_dict": attr_dict
        }
        return serialized

    return serialized if serialized else obj
