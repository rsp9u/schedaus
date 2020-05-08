from datetime import timedelta
from traceback import format_exc

import svgwrite
from schedaus.model import Task
from schedaus.utils import get_prefix_space_num, len_multibyte


w = 16
h = 16

text_common_opts = {
    "font_family": "Serif",
    "dominant_baseline": "hanging",
}

line_common_opts = {
    "style": "stroke:#C0C0C0;stroke-width=1.0",
}


def add_error(drawing):
    mw = int(drawing.attribs["width"][0:-2])
    mh = int(drawing.attribs["height"][0:-2])
    print(mw, mh)
    text, height = _generate_error_text(mh)
    drawing.add(text)
    drawing.attribs["height"] = f"{height}px"
    if mw < 640:
        drawing.attribs["width"] = "640px"


def draw_error():
    text, height = _generate_error_text()
    drawing = svgwrite.Drawing()
    drawing.add(text)
    drawing.attribs["width"] = "640px"
    drawing.attribs["height"] = f"{height}px"
    return drawing


def _generate_error_text(mh=0):
    d = svgwrite.Drawing()

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
            text = d.text(line, (0, mh+4), **text_opts)
        else:
            spaces = get_prefix_space_num(line)
            text.add(d.tspan(line, (spaces*8, mh+4), dy=[dy]))
            dy += dy_per

    height = mh + 4 + len(lines) * dy_per

    return text, height


def render(data):
    d = svgwrite.Drawing()
    schedules_y = {}
    idx = 0

    objs = calendar_to_svg(data["calendar"], data)

    def _find(items, name):
        return [x for x in items if x.name == name][0]

    for group in data["groups"]:
        if group.text:
            group_objs = group_to_svg(data["calendar"], group)
            y = h * 2 * (idx + 2)
            g = d.g(id=f"group-{group.text}", transform=f"translate(0, {y})")
            for group_obj in group_objs:
                g.add(group_obj)
            objs.append({"z": 20, "o": g})
            idx += 1
        for sc_name in group.member:
            sc = _find(data["schedules"], sc_name)
            y = h * 2 * (idx + 2)
            g = _render_schedule(sc, y, data)
            objs.append({"z": 20, "o": g})
            schedules_y[sc.name] = y
            idx += 1

    register_arrowhead_svg(d)
    for dpath in data["dependency_paths"]:
        obj = dpath_to_svg(data["calendar"], schedules_y, dpath)
        objs.append({"z": 30, "o": obj})

    for obj in sorted(objs, key=lambda x: x["z"]):
        d.add(obj["o"])

    mw = w * ((data["calendar"].end - data["calendar"].start).days + 1)
    mh = (h * 3) + (h * 2 * (len(data["schedules"]) + len(data["groups"])))
    d.attribs["width"] = f"{mw}px"
    d.attribs["height"] = f"{mh}px"

    return d


def _render_schedule(schedule, y, data):
    if isinstance(schedule, Task):
        task = schedule
        task_objs = task_to_svg(data["calendar"], task)
        g = svgwrite.Drawing().g(transform=f"translate(0, {y})")
        for task_obj in sorted(task_objs, key=lambda x: x["z"]):
            g.add(task_obj["o"])
    else:
        ms = schedule
        ms_objs = milestone_to_svg(data["calendar"], ms)
        g = svgwrite.Drawing().g(transform=f"translate(0, {y})")
        for ms_obj in sorted(ms_objs, key=lambda x: x["z"]):
            g.add(ms_obj["o"])

    return g


def calendar_to_svg(calendar, data):
    ph = 1
    mw = w * ((calendar.end - calendar.start).days + 1)
    mh = (h * 3) + (h * 2 * (len(data["schedules"]) + len(data["groups"])))

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
    d = svgwrite.Drawing()
    date = calendar.start
    while date <= calendar.end:
        if date.month != prev_month:
            objs.append({"z": 5, "o": d.text("{}/{}".format(date.year, date.month), (x+1, ph), **text_month_opts)})
            objs.append({"z": 10, "o": d.line((x, 0), (x, mh), **line_common_opts)})
            prev_month = date.month
        objs.append({"z": 5, "o": d.text(date.strftime("%a")[0:2], (x+w/2, h+ph), **text_day_opts)})
        objs.append({"z": 5, "o": d.text(date.day, (x+w/2, h*2+ph), **text_day_opts)})
        objs.append({"z": 10, "o": d.line((x, h*3), (x, mh), **line_common_opts)})
        x += w
        date += timedelta(days=1)
    for closed in calendar.closed:
        offset_days = (closed - calendar.start).days
        xy = (w * offset_days, h)
        objs.append({"z": 0, "o": d.rect(xy, (w, mh-h), fill="#D0D0D0")})

    # Outer frame
    objs.append({"z": 10, "o": d.line((mw, 0), (mw, mh), **line_common_opts)})
    objs.append({"z": 10, "o": d.line((0, h*0), (mw, h*0), **line_common_opts)})
    objs.append({"z": 10, "o": d.line((0, h*3), (mw, h*3), **line_common_opts)})

    # Today's line
    x = w * (calendar.today - calendar.start).days
    objs.append({"z": 99, "o": d.line((x, 0), (x, mh), stroke="#FF0000", stroke_width="3.0")})

    return objs


def task_to_svg(calendar, task):
    delta_to_start = task.plan_start - calendar.start
    delta_to_end = task.plan_end - calendar.start + timedelta(days=1)

    objs = []
    d = svgwrite.Drawing()
    xy = (w*delta_to_start.days, 0)
    wh = (w*(delta_to_end - delta_to_start).days, h)
    rect = d.rect(xy, wh, rx=6, ry=6, fill=task.color_plan_fill, stroke=task.color_plan_outline)
    objs.append({"z": 20, "o": rect})
    text_task_opts = {"font_size": "13", "color": task.color_text}
    text_task_opts.update(text_common_opts)
    text = task.text
    if task.assignee is not None:
        text += f"@{task.assignee}"
    objs.append({"z": 21, "o": d.text(text, (xy[0]+2, xy[1]+2), **text_task_opts)})

    if task.actual_start is not None and task.actual_end is not None:
        delta_to_start = task.actual_start - calendar.start
        delta_to_end = task.actual_end - calendar.start + timedelta(days=1)

        xy = (w*delta_to_start.days, h+2)
        wh = (w*(delta_to_end - delta_to_start).days, 4)
        if task.actual_completed is not None:
            opt = {"fill": "#FFFFFF", "stroke_dasharray": "4 3"}
        else:
            opt = {"fill": task.color_actual_fill}
        rect = d.rect(xy, wh, rx=2, ry=2, stroke=task.color_actual_outline, **opt)
        objs.append({"z": 20, "o": rect})

        if task.actual_progress is not None:
            xy = (w*delta_to_end.days+2, h+5)
            text_opts = {"font_family": "Serif", "font_size": 10, "font_weight": "bold", "dominant-baseline": "middle"}
            text = d.text(task.actual_progress, xy, **text_opts)
            objs.append({"z": 20, "o": text})

        if task.actual_completed is not None:
            delta_to_completed = task.actual_completed - calendar.start
            xy = (w*delta_to_start.days, h+2)
            wh = (w*(delta_to_completed - delta_to_start).days, 4)
            rect = d.rect(xy, wh, rx=2, ry=2, fill=task.color_actual_fill, stroke=task.color_actual_outline)
            objs.append({"z": 21, "o": rect})

    return objs


def milestone_to_svg(calendar, milestone):
    d = svgwrite.Drawing()
    x = w * (milestone.plan_happen - calendar.start).days
    path = [(w/2, 0), (0, h/2), (w/2, h), (w, h/2), (w/2, 0)]
    m = d.polyline(path, fill=milestone.color_plan_fill, stroke=milestone.color_plan_outline)
    text_ms_opts = {"font_size": "13", "color": milestone.color_text}
    text_ms_opts.update(text_common_opts)
    t = d.text(milestone.text, (w+2, 2), **text_ms_opts)
    g = d.g(transform=f"translate({x}, 0)")
    g.add(m)
    g.add(t)
    return [{"z": 0, "o": g}]


def register_arrowhead_svg(d):
    # a rightward arrowhead
    width = 5
    hight = 10
    path = [(0, 0), (0, hight), (width, hight/2), (0, 0)]
    p = d.polyline(path)
    g = d.g(id="arrowhead", transform=f"translate({-width}, {-hight/2})")
    g.add(p)
    d.defs.add(g)


def dpath_to_svg(calendar, schedules_y, dpath):
    d = svgwrite.Drawing()

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
        sx = w * (dpath.start_date - calendar.start).days + w / 2
        sy = schedules_y[dpath.start_name] + h
    else:
        if direction[0] == "right":
            sx = w * (dpath.start_date - calendar.start).days + w
        else:
            sx = w * (dpath.start_date - calendar.start).days
        sy = schedules_y[dpath.start_name] + h / 2

    if direction[0] != "down":
        ex = w * (dpath.end_date - calendar.start).days + w / 2
        ey = schedules_y[dpath.end_name] + h
    else:
        if direction[1] == "right":
            ex = w * (dpath.end_date - calendar.start).days
        else:
            ex = w * (dpath.end_date - calendar.start).days + w
        ey = schedules_y[dpath.end_name] + h / 2

    if direction[0] == "down":
        mx = sx
        my = ey
    else:
        mx = ex
        my = sy

    l1 = d.line((sx, sy), (mx, my), stroke=dpath.color, stroke_width=2.0)
    l2 = d.line((mx, my), (ex, ey), stroke=dpath.color, stroke_width=2.0)

    r = {"right": 0, "down": 90, "left": 180, "up": 270}
    arrowhead = d.g(transform=f"translate({ex}, {ey}) rotate({r[direction[1]]})")
    arrowhead.add(d.use("#arrowhead", fill=dpath.color))

    g = d.g(id=f"path-{dpath.start_name}-to-{dpath.end_name}")
    g.add(l1)
    g.add(l2)
    g.add(arrowhead)
    return g


def group_to_svg(calendar, group):
    mw = w * ((calendar.end - calendar.start).days + 1)
    objs = []
    d = svgwrite.Drawing()
    text_size = len_multibyte(group.text) * 8 + 10
    line_opts = {"style": "stroke:black; stroke-width=1.0"}
    text_opts = {"font_family": "Serif", "font_size": 13, "dominant_baseline": "middle", "text_anchor": "middle"}
    objs.append(d.line((0, h/3*1), (mw/2 - text_size/2, h/3*1), **line_opts))
    objs.append(d.line((0, h/3*2), (mw/2 - text_size/2, h/3*2), **line_opts))
    objs.append(d.text(group.text, (mw/2, h/2), **text_opts))
    objs.append(d.line((mw/2 + text_size/2, h/3*1), (mw, h/3*1), **line_opts))
    objs.append(d.line((mw/2 + text_size/2, h/3*2), (mw, h/3*2), **line_opts))
    return objs
