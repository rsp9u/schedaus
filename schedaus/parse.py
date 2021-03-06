import re
import yaml
from datetime import timedelta
from collections import defaultdict

from schedaus.utils import strpdate, is_float, is_valid_date, is_valid_color


class ParserContext:
    def __init__(self):
        self.group = None
        self.schedule = None


class Parser:
    re_comment = re.compile("^#.*$")
    re_project_period = re.compile("^(p|P)roject lasts (.*) to (.*)$")
    re_ranged_holiday = re.compile("^(.*) to (.*) (are|is) closed$")
    re_holiday = re.compile("^(.*) (are|is) closed$")
    re_today = re.compile("^today is (.*)$")
    re_scale = re.compile("^scale is (.*)$")
    re_color = re.compile("^(tasks?|milestones?|paths?) (are|is) colored (.*)$")
    re_group = re.compile("^(--|==).*")
    re_task = re.compile("^([^!\\s:]+)(\\s*:\\s*)?(.*)$")
    re_milestone = re.compile("^!([^\\s:]+)(:\\s*)?(.*)$")
    re_attribute = re.compile("^  [^\\s].*$")

    def __init__(self):
        self.output = {
            "project": {
                "closed": [],
            },
            "style": {
                "color": {},
            },
            "task": [],
            "milestone": [],
            "group": []
        }
        self.context = ParserContext()

    def parse(self, data_sch):
        for line in data_sch.splitlines():
            self.dispatch(line)

        self.output["task"] = [dict(t) for t in self.output["task"]]
        self.output["milestone"] = [dict(m) for m in self.output["milestone"]]

    def dispatch(self, line):
        patterns = [
            "comment",
            "project_period",
            "ranged_holiday",
            "holiday",
            "today",
            "scale",
            "color",
            "group",
            "task",
            "milestone",
            "attribute",
        ]

        for pattern_name in patterns:
            m = getattr(self, "re_" + pattern_name).match(line)
            if m is not None:
                getattr(self, pattern_name)(line, m)
                return

    def comment(self, line, m):
        pass

    def project_period(self, line, m):
        try:
            strpdate(m.group(2))
            strpdate(m.group(3))
            self.output["project"]["start"] = m.group(2)
            self.output["project"]["end"] = m.group(3)
        except ValueError:
            pass

    def ranged_holiday(self, line, m):
        try:
            d = strpdate(m.group(1))
            end = strpdate(m.group(2)) + timedelta(days=1)
            if d > end:
                return
            while d != end:
                self.output["project"]["closed"].append(d.strftime("%Y/%m/%d"))
                d += timedelta(days=1)
        except ValueError:
            pass

    def holiday(self, line, m):
        self.output["project"]["closed"].append(m.group(1))

    def today(self, line, m):
        try:
            strpdate(m.group(1))
            self.output["project"]["today"] = m.group(1)
        except ValueError:
            pass

    def scale(self, line, m):
        self.output["project"]["scale"] = m.group(1)

    def color(self, line, m):
        if all([is_valid_color(color) for color in m.group(3).split("/")]):
            kind = m.group(1)
            if kind.endswith("s"):
                kind = kind[:-1]
            self.output["style"]["color"][kind] = m.group(3)

    def group(self, line, m):
        text = line.strip("-= ")
        group = {"text": text, "member": []}
        self.output["group"].append(group)
        self.context.group = group

    def task(self, line, m, kind="task"):
        task = defaultdict(dict)
        task["name"] = m.group(1)
        task["kind"] = kind
        if m.group(3):
            task["text"] = m.group(3).strip("'\"")
        self.context.schedule = task

    def milestone(self, line, m):
        self.task(line, m, kind="milestone")

    def attribute(self, line, m):
        if self.context.schedule is None:
            return

        def _parse_schedule(line, plan_or_actual):
            if plan_or_actual == "plan":
                mark = ">"
            else:
                mark = "."

            if line.startswith(f"  {mark}>"):
                value = line[4:].strip()
                if is_valid_date(value) or value.endswith("'s start") or value.endswith("'s end"):
                    self.context.schedule[plan_or_actual]["start"] = value
            if line.startswith(f"  {mark}<"):
                value = line[4:].strip()
                if is_valid_date(value) or value.endswith("'s start") or value.endswith("'s end"):
                    self.context.schedule[plan_or_actual]["end"] = value
            if line.startswith(f"  {mark}="):
                value = line[4:].strip()
                if value.endswith("days"):
                    self.context.schedule[plan_or_actual]["period"] = value
            if line.startswith(f"  {mark}!"):
                value = line[4:].strip()
                if is_valid_date(value) or value.endswith("'s start") or value.endswith("'s end"):
                    self.context.schedule[plan_or_actual] = value

        _parse_schedule(line, "plan")
        _parse_schedule(line, "actual")

        if line.startswith(f"  .-"):
            value = line[4:].strip()
            if value.endswith("%") or len(value.split("/")) == 2 or is_float(value):
                self.context.schedule["actual"]["progress"] = value

        if line.startswith(f"  @"):
            value = line[3:].strip()
            self.context.schedule["assignee"] = value

        self._register_schedule()

    def _register_schedule(self):
        sc = self.context.schedule
        kind = sc["kind"]

        if sc["name"] in [o["name"] for o in self.output[kind]]:
            # already registered
            return

        if kind == "task":
            if "plan" not in sc:
                return
            if "start" not in sc["plan"]:
                return
            if "end" not in sc["plan"] and "period" not in sc["plan"]:
                return
        else:
            if "plan" not in sc:
                return

        self.output[kind].append(sc)
        if self.context.group is not None:
            self.context.group["member"].append(sc["name"])


if __name__ == "__main__":
    with open("example.sch") as f:
        p = Parser()
        p.parse(f.read())
        print(yaml.dump(p.output))
