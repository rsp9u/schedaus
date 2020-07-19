import math
import logging
from datetime import timedelta
from pprint import pformat

from graph import Graph
from schedaus.const import C
from schedaus.model import Calendar, Task, Milestone, DependencyPath, Group
from schedaus.utils import strpdate, weekday_to_dates, calc_date_in_business_days

logger = logging.getLogger(__name__)


class Resolver:
    def __init__(self):
        self.colors = None

    def resolve(self, data_dict):
        ret = {
            "calendar": None,
            "schedules": [],
            "dependency_paths": [],
            "groups": [],
        }

        project = data_dict["project"]
        start = strpdate(project["start"])
        end = strpdate(project["end"])
        closed = []
        for c in project["closed"]:
            try:
                d = strpdate(c)
                closed.append(d)
            except ValueError:
                closed.extend(weekday_to_dates(c, start, end))
        project["closed_dates"] = closed
        project["scale"] = project.get("scale", "daily")
        ret["calendar"] = Calendar(start, end, strpdate(project["today"]), closed, project["scale"])

        self.colors = self._get_colors(data_dict.get("style"))

        schedules = {}
        for task in data_dict.get("task", []):
            if task["name"] in schedules.keys():
                raise Exception(f"'{task['name']}' is duplicated.")
            schedules[task["name"]] = task
        for ms in data_dict.get("milestone", []):
            if ms["name"] in schedules.keys():
                raise Exception(f"'{ms['name']}' is duplicated.")
            if "plan" in ms:
                ms["plan"] = {"start": ms["plan"], "end": ms["plan"]}
            schedules[ms["name"]] = ms
        dpaths = self._resolve_dependency(project, schedules)
        ret["dependency_paths"] = dpaths

        for task in data_dict.get("task", []):
            self._resolve_actual(project, task)
            t = Task(
                task["name"],
                task.get("text", task["name"]),
                strpdate(task["plan"]["start"]),
                strpdate(task["plan"]["end"]),
                self.colors["task"]["plan_fill"],
                self.colors["task"]["plan_outline"],
                self.colors["task"]["actual_fill"],
                self.colors["task"]["actual_outline"],
                self.colors["task"]["text"],
                strpdate(task.get("actual", {}).get("start")),
                strpdate(task.get("actual", {}).get("completed")),
                task.get("actual", {}).get("progress"),
                strpdate(task.get("actual", {}).get("end")),
                task.get("assignee"),
            )
            ret["schedules"].append(t)

        for ms in data_dict.get("milestone", []):
            m = Milestone(
                ms["name"],
                ms.get("text", ms["name"]),
                strpdate(ms["plan"]["start"]),
                self.colors["milestone"]["plan_fill"],
                self.colors["milestone"]["plan_outline"],
                self.colors["milestone"]["actual_fill"],
                self.colors["milestone"]["actual_outline"],
                self.colors["milestone"]["text"],
                strpdate(ms.get("actual", None)),
            )
            ret["schedules"].append(m)

        belongs = set()
        for group in data_dict.get("group", []):
            ret["groups"].append(Group(group["text"], group["member"]))
            belongs.update(group["member"])
        notbelongs_unordered = set([sc.name for sc in ret["schedules"]]) - belongs
        notbelongs = []
        for sc in ret["schedules"]:
            if sc.name in notbelongs_unordered:
                notbelongs.append(sc.name)
        ret["groups"].insert(0, Group("", notbelongs))

        logger.debug(pformat(ret))

        return ret

    def _resolve_dependency(self, project, schedules):
        g = Graph()
        dpaths = []
        for k, v in schedules.items():
            g.add_node(k, v)
        for k, v in schedules.items():
            plan = v.get("plan")
            if plan is None:
                continue
            if "start" in plan:
                self._add_dep(g, schedules, k, plan["start"])
            if "end" in plan:
                self._add_dep(g, schedules, k, plan["end"])

        if g.has_cycles():
            raise Exception("the dependencies are looped!")

        independents = []
        for n in g.nodes():
            if len(g.edges(from_node=n)) == 0 and len(g.edges(to_node=n)) == 0:
                g.del_node(n)
                independents.append(n)

        for n in g.nodes():
            if len(g.edges(from_node=n)) == 0:
                path = self._search_to_root(g, n, [])
                for t in reversed(path):
                    self._resolve_date(project, schedules, t)
                    dpaths.extend(self._make_dpath(schedules, t))
        dpaths = list(set(dpaths))

        for n in independents:
            self._resolve_date(project, schedules, n)

        return dpaths

    def _add_dep(self, g, schedules, k, s):
        if not s.endswith("'s start") and not s.endswith("'s end"):
            return

        dep = s
        dep = dep.replace("'s start", "")
        dep = dep.replace("'s end", "")
        if dep not in g:
            if dep != "project":
                logger.warning(f"warn: '{dep}' does not exist.")
            return
        g.add_edge(dep, k, 1)

    def _search_to_root(self, g, s, p):
        p.append(s)
        for n in g.nodes(to_node=s):
            self._search_to_root(g, n, p)
        return p

    def _resolve_date(self, project, schedules, name):
        print(f"resolve date {name}")
        t = schedules[name]
        plan = t.get("plan")
        if plan is None:
            return

        def _date_delta(d, delta):
            return calc_date_in_business_days(strpdate(d), delta, project["closed_dates"]).strftime("%Y/%m/%d")

        def _(k):
            if plan[k] == "project's start":
                plan[k] = project["start"]
            if plan[k] == "project's end":
                plan[k] = project["end"]
            if plan[k].endswith("'s end"):
                dep = plan[k].replace("'s end", "")
                plan[k+"_org"] = plan[k]
                plan[k] = _date_delta(schedules.get(dep, {}).get("plan", {}).get("end"), 2)
            if plan[k].endswith("'s start"):
                dep = plan[k].replace("'s start", "")
                plan[k+"_org"] = plan[k]
                plan[k] = _date_delta(schedules.get(dep, {}).get("plan", {}).get("start"), -2)

        if "start" in plan:
            _("start")
        if "end" in plan:
            _("end")
        if "period" in plan:
            end_date = calc_date_in_business_days(strpdate(plan["start"]), plan["period"], project["closed_dates"])
            plan["end"] = end_date.strftime("%Y/%m/%d")

    def _make_dpath(self, schedules, name):
        t = schedules[name]
        plan = t.get("plan")
        if plan is None:
            return

        def _(k):
            if plan[k+"_org"].endswith("'s end"):
                dep = plan[k+"_org"].replace("'s end", "")
                dep_end = strpdate(schedules.get(dep, {}).get("plan", {}).get("end"))
                return DependencyPath(dep, dep_end, name, strpdate(plan[k]), self.colors["path"])
            if plan[k+"_org"].endswith("'s start"):
                dep = plan[k+"_org"].replace("'s start", "")
                dep_start = strpdate(schedules.get(dep, {}).get("plan", {}).get("start"))
                return DependencyPath(dep, dep_start, name, strpdate(plan[k]), self.colors["path"])

        paths = []
        if "start_org" in plan:
            paths.append(_("start"))
        if "end_org" in plan:
            paths.append(_("end"))
        return paths

    def _resolve_actual(self, project, task):
        today = strpdate(project["today"])
        actual = task.get("actual")
        if actual is None or actual.get("start") is None:
            return

        if "period" in actual:
            end_date = calc_date_in_business_days(strpdate(actual["start"]), actual["period"], project["closed_dates"])
            actual["end"] = end_date.strftime("%Y/%m/%d")

        if "progress" in actual:
            start = strpdate(actual["start"])
            progress = actual["progress"]

            dates = set([start + timedelta(i) for i in range((today - start).days)])
            dates = dates - set(project["closed_dates"])
            days = math.ceil(len(dates) / progress)

            actual["completed"] = today.strftime("%Y/%m/%d")

            end_date = calc_date_in_business_days(start, days, project["closed_dates"])
            actual["end"] = end_date.strftime("%Y/%m/%d")

    def _get_colors(self, style):
        colors = {
            "task": dict(**C.default_colors),
            "milestone": dict(**C.default_colors),
            "path": C.default_colors["path"],
        }

        if style is None:
            return colors

        if style.get("color", {}).get("path"):
            colors["path"] = style["color"]["path"]
        if style.get("color", {}).get("task"):
            colors["task"].update(self._parse_color_set(style["color"]["task"]))
        if style.get("color", {}).get("milestone"):
            colors["milestone"].update(self._parse_color_set(style["color"]["milestone"]))

        return colors

    def _parse_color_set(self, color_set):
        ret = {}
        colors = color_set.split("/")
        if len(colors) >= 1:
            ret["plan_fill"] = colors[0]
        if len(colors) >= 2:
            ret["plan_outline"] = colors[1]
        if len(colors) >= 3:
            ret["text"] = colors[2]
        if len(colors) >= 4:
            ret["actual_fill"] = colors[3]
        if len(colors) >= 5:
            ret["actual_outline"] = colors[4]
        return ret
