import os
import io
import logging
from traceback import format_exc

import cairosvg
from flask import Flask, request, make_response, send_from_directory, send_file
from schedaus.utils import decode_base64url
from schedaus.parse import Parser
from schedaus.proc import Resolver
from schedaus.render import Renderer
from schedaus.cache import ResponseCache
logging.basicConfig(format="[%(asctime)-15s] %(name)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask('schedaus')
response_cache = ResponseCache()


@app.route('/sch/svg/<b64_data>')
def sch_to_svg(b64_data):
    data_sch = decode_base64url(b64_data)
    logger.debug(data_sch)
    p = Parser()
    p.parse(data_sch)
    renderer = resolve_render(p.output)
    return make_svg_response(renderer.get_svg().tostring())


@app.route('/yaml/svg/<b64_data>')
def yaml_to_svg(b64_data):
    data_yaml = decode_base64url(b64_data)
    logger.debug(data_yaml)
    renderer = resolve_render(data_yaml)
    return make_svg_response(renderer.get_svg().tostring())


@app.route('/sch/png/<b64_data>')
def sch_to_png(b64_data):
    data_sch = decode_base64url(b64_data)
    logger.debug(data_sch)
    p = Parser()
    p.parse(data_sch)
    renderer = resolve_render(p.output)
    return make_png_response(renderer.get_svg().tostring())


def resolve_render(data_yaml):
    global response_cache

    data = Resolver().resolve(data_yaml)
    renderer = Renderer()
    renderer.render(data)
    if request.args.get('client_id'):
        response_cache.set(request.args.get('client_id'), renderer.get_svg())

    return renderer


def make_svg_response(svg_text):
    resp = make_response(svg_text)
    add_common_header(resp)
    return resp


def make_png_response(svg_text):
    byteio = io.BytesIO()
    cairosvg.svg2png(bytestring=svg_text.encode(), write_to=byteio)
    byteio.seek(0)
    return send_file(byteio, attachment_filename='schedaus.png', mimetype='image/png')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/x-icon')


@app.errorhandler(Exception)
def log_exception(exc):
    global response_cache

    logger.error("an error occurred on the request.")
    logger.error(format_exc())

    client_id = request.args.get('client_id')
    if client_id and response_cache.get(client_id):
        svg = response_cache.get(client_id).copy()
        renderer = Renderer(svg)
        renderer.add_error()
    else:
        renderer = Renderer()
        renderer.draw_error()

    resp = make_response(renderer.get_svg().tostring())
    add_common_header(resp)
    return resp


def add_common_header(resp):
    resp.headers['Content-Type'] = "image/svg+xml; charset=utf-8"
    resp.headers['Cache-Control'] = "no-store"


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
