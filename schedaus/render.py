from datetime import timedelta
from traceback import format_exc

import svgwrite
from schedaus.model import Task
from schedaus.utils import get_prefix_space_num, len_multibyte, calc_remain_days_in_month


text_common_opts = {
    "font_family": "Serif",
    "dominant_baseline": "hanging",
}

line_common_opts = {
    "style": "stroke:#C0C0C0;stroke-width=1.0",
}


class Renderer:
    def __init__(self, dwg=None):
        if dwg is None:
            self.dwg = svgwrite.Drawing()
        else:
            self.dwg = dwg

        # width per day
        self.wpd = 8
        # height per line
        self.hpl = 16
        # maximum width
        self.mw = -1
        # maximum height
        self.mh = -1

        self.scale = "daily"
        self.schedule_offset = self.hpl * 4

    def get_svg(self):
        return self.dwg

    def add_error(self):
        mw = int(self.dwg.attribs["width"][0:-2])
        mh = int(self.dwg.attribs["height"][0:-2])
        print(mw, mh)
        text, height = self._generate_error_text(mh)
        self.dwg.add(text)
        self.dwg.attribs["height"] = f"{height}px"
        if mw < 640:
            self.dwg.attribs["width"] = "640px"

    def draw_error(self):
        text, height = self._generate_error_text()
        self.dwg.add(text)
        self.dwg.attribs["width"] = "640px"
        self.dwg.attribs["height"] = f"{height}px"
        return self.dwg

    def _generate_error_text(self, mh=0):
        text_opts = {
            "font_size": "14",
            "font_weight": "bold",
            "fill": "red",
        }
        text_opts.update(text_common_opts)
        text = None
        dy_per = 16
        dy = dy_per
        lines = format_exc().splitlines()
        for line in lines:
            if text is None:
                text = self.dwg.text(line, (0, mh+4), **text_opts)
            else:
                spaces = get_prefix_space_num(line)
                text.add(self.dwg.tspan(line, (spaces*8, mh+4), dy=[dy]))
                dy += dy_per

        height = mh + 4 + len(lines) * dy_per

        return text, height

    def render(self, data):
        schedules_y = {}
        idx = 0

        self.change_scale(data["calendar"].scale)

        objs = self.calendar_to_svg(data["calendar"], data)

        def _find(items, name):
            return [x for x in items if x.name == name][0]

        for group in data["groups"]:
            if group.text:
                group_objs = self.group_to_svg(data["calendar"], group)
                y = self.schedule_offset + self.hpl * (idx * 2)
                g = self.dwg.g(id=f"group-{group.text}", transform=f"translate(0, {y})")
                for group_obj in group_objs:
                    g.add(group_obj)
                objs.append({"z": 20, "o": g})
                idx += 1
            for sc_name in group.member:
                sc = _find(data["schedules"], sc_name)
                y = self.schedule_offset + self.hpl * (idx * 2)
                g = self._render_schedule(sc, y, data)
                objs.append({"z": 20, "o": g})
                schedules_y[sc.name] = y
                idx += 1

        self.register_arrowhead_svg()
        for dpath in data["dependency_paths"]:
            obj = self.dpath_to_svg(data["calendar"], schedules_y, dpath)
            objs.append({"z": 30, "o": obj})

        for obj in sorted(objs, key=lambda x: x["z"]):
            self.dwg.add(obj["o"])

    def change_scale(self, scale):
        self.scale = scale
        if scale == "daily":
            self.wpd = 16
            self.schedule_offset = self.hpl * 4
        elif scale == "weekly":
            self.wpd = 8
            self.schedule_offset = self.hpl * 3

    def _render_schedule(self, schedule, y, data):
        if isinstance(schedule, Task):
            task = schedule
            task_objs = self.task_to_svg(data["calendar"], task)
            g = self.dwg.g(transform=f"translate(0, {y})")
            for task_obj in sorted(task_objs, key=lambda x: x["z"]):
                g.add(task_obj["o"])
        else:
            ms = schedule
            ms_objs = self.milestone_to_svg(data["calendar"], ms)
            g = self.dwg.g(transform=f"translate(0, {y})")
            for ms_obj in sorted(ms_objs, key=lambda x: x["z"]):
                g.add(ms_obj["o"])

        return g

    def calendar_to_svg(self, calendar, data):
        ph = 1
        self.mw = self.wpd * ((calendar.end - calendar.start).days + 1)
        self.mh = (self.hpl * 3) + (self.hpl * 2 * (len(data["schedules"]) + len(data["groups"])))
        self.dwg.attribs["width"] = f"{self.mw}px"
        self.dwg.attribs["height"] = f"{self.mh}px"

        objs = []
        prev_month = None
        text_month_opts = {
            "font_size": "13",
            "font_weight": "bold",
        }
        text_month_opts.update(text_common_opts)
        text_day_opts = {
            "font_size": "11",
            "text_anchor": "middle",
        }
        text_day_opts.update(text_common_opts)
        x = 0
        date = calendar.start
        while date <= calendar.end:
            if date.month != prev_month:
                # draw 'YYYY/MM' text
                if calc_remain_days_in_month(date) >= 3:
                    month_text = "{}/{}".format(date.year, date.month)
                else:
                    month_text = "{}".format(date.month)
                objs.append({"z": 5, "o": self.dwg.text(month_text, (x+1, ph), **text_month_opts)})
                # draw line per month
                if self.scale == "daily":
                    h = self.mh
                elif self.scale == "weekly":
                    h = self.hpl
                objs.append({"z": 10, "o": self.dwg.line((x, 0), (x, h), **line_common_opts)})
                # update previous month
                prev_month = date.month

            if self.scale == "daily":
                # draw weekday text
                objs.append({"z": 5, "o": self.dwg.text(date.strftime("%a")[0:2], (x+self.wpd/2, self.hpl+ph), **text_day_opts)})
                # draw day text
                objs.append({"z": 5, "o": self.dwg.text(date.day, (x+self.wpd/2, self.hpl*2+ph), **text_day_opts)})
                # draw line per day
                objs.append({"z": 10, "o": self.dwg.line((x, self.hpl*3), (x, self.mh), **line_common_opts)})
            elif self.scale == "weekly":
                if date.weekday() == 0:
                    # draw day text
                    objs.append({"z": 5, "o": self.dwg.text(date.day, (x+self.wpd/2+2, self.hpl+ph), **text_day_opts)})
                    # draw line per week
                    objs.append({"z": 10, "o": self.dwg.line((x, self.hpl), (x, self.mh), **line_common_opts)})
            x += self.wpd
            date += timedelta(days=1)

        for closed in calendar.closed:
            offset_days = (closed - calendar.start).days
            if self.scale == "daily":
                xy = (self.wpd * offset_days, self.hpl)
            elif self.scale == "weekly":
                xy = (self.wpd * offset_days, self.hpl*2)
            objs.append({"z": 0, "o": self.dwg.rect(xy, (self.wpd, self.mh-self.hpl), fill="#D0D0D0")})

        # Outer frame
        objs.append({"z": 10, "o": self.dwg.line((self.mw, 0), (self.mw, self.mh), **line_common_opts)})
        objs.append({"z": 10, "o": self.dwg.line((0, self.hpl*0), (self.mw, self.hpl*0), **line_common_opts)})
        if self.scale == "daily":
            objs.append({"z": 10, "o": self.dwg.line((0, self.hpl*3), (self.mw, self.hpl*3), **line_common_opts)})
        elif self.scale == "weekly":
            objs.append({"z": 10, "o": self.dwg.line((0, self.hpl*1), (self.mw, self.hpl*1), **line_common_opts)})
            objs.append({"z": 10, "o": self.dwg.line((0, self.hpl*2), (self.mw, self.hpl*2), **line_common_opts)})

        # Today's line
        x = self.wpd * (calendar.today - calendar.start).days
        objs.append({"z": 99, "o": self.dwg.line((x, 0), (x, self.mh), stroke="#FF0000", stroke_width="3.0")})

        return objs

    def task_to_svg(self, calendar, task):
        delta_to_start = task.plan_start - calendar.start
        delta_to_end = task.plan_end - calendar.start + timedelta(days=1)

        objs = []
        xy = (self.wpd*delta_to_start.days, 0)
        wh = (self.wpd*(delta_to_end - delta_to_start).days, self.hpl)
        rect = self.dwg.rect(xy, wh, rx=6, ry=6, fill=task.color_plan_fill, stroke=task.color_plan_outline)
        objs.append({"z": 20, "o": rect})
        text_task_opts = {"font_size": "13", "color": task.color_text}
        text_task_opts.update(text_common_opts)
        text = task.text
        if task.assignee is not None:
            text += f"@{task.assignee}"
        objs.append({"z": 21, "o": self.dwg.text(text, (xy[0]+2, xy[1]+2), **text_task_opts)})

        if task.actual_start is not None and task.actual_end is not None:
            delta_to_start = task.actual_start - calendar.start
            delta_to_end = task.actual_end - calendar.start + timedelta(days=1)

            xy = (self.wpd*delta_to_start.days, self.hpl+2)
            wh = (self.wpd*(delta_to_end - delta_to_start).days, 4)
            if task.actual_completed is not None:
                opt = {"fill": "#FFFFFF", "stroke_dasharray": "4 3"}
            else:
                opt = {"fill": task.color_actual_fill}
            rect = self.dwg.rect(xy, wh, rx=2, ry=2, stroke=task.color_actual_outline, **opt)
            objs.append({"z": 20, "o": rect})

            if task.actual_progress is not None:
                xy = (self.wpd*delta_to_end.days+2, self.hpl+5)
                text_opts = {
                    "font_family": "Serif",
                    "font_size": 10,
                    "font_weight": "bold",
                    "dominant-baseline": "middle",
                }
                text = self.dwg.text(task.actual_progress, xy, **text_opts)
                objs.append({"z": 20, "o": text})

            if task.actual_completed is not None:
                delta_to_completed = task.actual_completed - calendar.start
                xy = (self.wpd*delta_to_start.days, self.hpl+2)
                wh = (self.wpd*(delta_to_completed - delta_to_start).days, 4)
                rect = self.dwg.rect(xy, wh, rx=2, ry=2, fill=task.color_actual_fill, stroke=task.color_actual_outline)
                objs.append({"z": 21, "o": rect})

        return objs

    def milestone_to_svg(self, calendar, milestone):
        x = self.wpd * ((milestone.plan_happen - calendar.start).days + 0.5)
        s = self.hpl / 2
        path = [(0, 0), (-s, s), (0, s*2), (s, s), (0, 0)]
        m = self.dwg.polyline(path, fill=milestone.color_plan_fill, stroke=milestone.color_plan_outline)
        text_ms_opts = {"font_size": "13", "color": milestone.color_text}
        text_ms_opts.update(text_common_opts)
        t = self.dwg.text(milestone.text, (self.hpl/2+2, 2), **text_ms_opts)
        g = self.dwg.g(transform=f"translate({x}, 0)")
        g.add(m)
        g.add(t)
        return [{"z": 0, "o": g}]

    def register_arrowhead_svg(self):
        # a rightward arrowhead
        width = 5
        hight = 10
        path = [(0, 0), (0, hight), (width, hight/2), (0, 0)]
        p = self.dwg.polyline(path)
        g = self.dwg.g(id="arrowhead", transform=f"translate({-width}, {-hight/2})")
        g.add(p)
        self.dwg.defs.add(g)

    def dpath_to_svg(self, calendar, schedules_y, dpath):
        # determine the direction
        if schedules_y[dpath.start_name] < schedules_y[dpath.end_name]:
            if dpath.start_date < dpath.end_date:
                direction = ["down", "right"]
            else:
                direction = ["down", "left"]
        else:
            if dpath.start_date < dpath.end_date:
                direction = ["right", "up"]
            else:
                direction = ["left", "up"]

        if direction[0] == "down":
            sx = self.wpd * (dpath.start_date - calendar.start).days + self.wpd / 2
            sy = schedules_y[dpath.start_name] + self.hpl
        else:
            if direction[0] == "right":
                sx = self.wpd * (dpath.start_date - calendar.start).days + self.wpd
            else:
                sx = self.wpd * (dpath.start_date - calendar.start).days
            sy = schedules_y[dpath.start_name] + self.hpl / 2

        if direction[0] != "down":
            ex = self.wpd * (dpath.end_date - calendar.start).days + self.wpd / 2
            ey = schedules_y[dpath.end_name] + self.hpl
        else:
            if direction[1] == "right":
                ex = self.wpd * (dpath.end_date - calendar.start).days
            else:
                ex = self.wpd * (dpath.end_date - calendar.start).days + self.wpd
            ey = schedules_y[dpath.end_name] + self.hpl / 2

        # adjust for weekly scale
        if self.scale == "weekly":
            if direction[1] == "right":
                sx -= self.wpd * 0.5
            if direction[1] == "left":
                sx += self.wpd * 0.5

        if direction[0] == "down":
            mx = sx
            my = ey
        else:
            mx = ex
            my = sy

        l1 = self.dwg.line((sx, sy), (mx, my), stroke=dpath.color, stroke_width=2.0)
        l2 = self.dwg.line((mx, my), (ex, ey), stroke=dpath.color, stroke_width=2.0)

        r = {"right": 0, "down": 90, "left": 180, "up": 270}
        arrowhead = self.dwg.g(transform=f"translate({ex}, {ey}) rotate({r[direction[1]]})")
        arrowhead.add(self.dwg.use("#arrowhead", fill=dpath.color))

        g = self.dwg.g(id=f"path-{dpath.start_name}-to-{dpath.end_name}")
        g.add(l1)
        g.add(l2)
        g.add(arrowhead)
        return g

    def group_to_svg(self, calendar, group):
        objs = []
        text_size = len_multibyte(group.text) * 8 + 10
        line_opts = {"style": "stroke:dimgray; stroke-width=1.0"}
        text_opts = {"font_family": "Serif", "font_size": 13, "dominant_baseline": "middle", "text_anchor": "middle"}
        objs.append(self.dwg.line((0, self.hpl/5*2), (self.mw/2 - text_size/2, self.hpl/5*2), **line_opts))
        objs.append(self.dwg.line((0, self.hpl/5*3), (self.mw/2 - text_size/2, self.hpl/5*3), **line_opts))
        objs.append(self.dwg.text(group.text, (self.mw/2, self.hpl/2), **text_opts))
        objs.append(self.dwg.line((self.mw/2 + text_size/2, self.hpl/5*2), (self.mw, self.hpl/5*2), **line_opts))
        objs.append(self.dwg.line((self.mw/2 + text_size/2, self.hpl/5*3), (self.mw, self.hpl/5*3), **line_opts))
        return objs
