class ConstError(TypeError):
    pass


class MetaConst(type):
    def __setattr__(self, k, v):
        raise ConstError("Const class is immutable.")


class ImmutableDict(dict):
    def __setitem__(self, k, v):
        raise ConstError("Const class is immutable.")


class C(metaclass=MetaConst):
    default_colors = ImmutableDict({
        "plan_fill": "yellowgreen",
        "plan_outline": "green",
        "actual_fill": "blueviolet",
        "actual_outline": "darkviolet",
        "text": "black",
        "path": "blue",
    })

    text_common_opts = ImmutableDict({
        "font_family": "Serif",
        "dominant_baseline": "hanging",
        "alignment_baseline": "hanging",
    })

    line_common_opts = ImmutableDict({
        "style": "stroke:#C0C0C0;stroke-width=1.0",
    })

    width_per_day = 8
    height_per_line = 16

    def __init__(self):
        raise ConstError("Const class can not be instantiated.")
