from datetime import date

from schedaus.const import C


class Normalizer:
    def normalize(self, data_dict):
        def _(data, keys):
            if isinstance(data, dict):
                for k, v in data.items():
                    data[k] = _(v, keys + [k])
                return data
            if isinstance(data, list):
                for idx, elem in enumerate(data):
                    data[idx] = _(elem, keys + ["elem"])
                return data
            return self._normalized_value(data, keys)

        _(data_dict, [])

    def _normalized_value(self, value, keys):
        f = getattr(self, "_" + "_".join(keys), None)
        if f is not None:
            return f(value)
        return value

    def _project_closed_elem(self, value):
        for i in range(7):
            d = date(1970, 1, 1+i)
            if d.strftime("%a").lower()[0:2] == value.lower()[0:2]:
                return d.strftime("%A")
        return value

    def _task_elem_plan_period(self, value):
        if isinstance(value, float):
            return value
        if isinstance(value, int):
            return float(value)
        if isinstance(value, str):
            try:
                if "hour" in value:
                    value = value.replace("hours", "").replace("hour", "").strip()
                    return float(value) / C.default_hours_of_day
                if "day" in value:
                    value = value.replace("days", "").replace("day", "").strip()
                    return float(value)
                return float(value)
            except ValueError:
                raise Exception(f"unsupported type of period: {value}({type(value)})")

        raise Exception(f"unsupported type of period: {value}({type(value)})")

    def _task_elem_actual_period(self, value):
        return self._task_elem_plan_period(value)

    def _milestone_elem_plan_period(self, value):
        return self._task_elem_plan_period(value)

    def _milestone_elem_actual_period(self, value):
        return self._task_elem_plan_period(value)

    def _task_elem_actual_progress(self, value):
        if isinstance(value, float):
            return value
        if isinstance(value, int):
            return float(value)
        if isinstance(value, str) and value.endswith("%"):
            return float(value.strip("%")) / 100.0
        if isinstance(value, str) and len(value.split("/")) == 2:
            sp = value.split("/")
            return float(sp[0]) / float(sp[1])
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                raise Exception(f"unsupported type of progress: {value}({type(value)})")

        raise Exception(f"unsupported type of progress: {value}({type(value)})")

    def _milestone_elem_actual_progress(self, value):
        return self._task_elem_actual_progress(value)
