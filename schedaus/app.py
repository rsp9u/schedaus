import os
import logging
from traceback import format_exc
from flask import Flask, make_response, send_from_directory
from werkzeug.exceptions import InternalServerError
from schedaus.base64url import decode_base64url
from schedaus.parse import Parser
from schedaus.proc import Resolver
from schedaus.render import render
logging.basicConfig(format="[%(asctime)-15s] %(name)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask('schedaus')


@app.route('/sch/svg/<b64_data>')
def sch_to_svg(b64_data):
    data_sch = decode_base64url(b64_data)
    logger.debug(data_sch)
    p = Parser()
    p.parse(data_sch)
    data = Resolver().resolve(p.output)
    svg = render(data)
    resp = make_response(svg)
    resp.headers['Content-Type'] = "image/svg+xml; charset=utf-8"
    return resp


@app.route('/yaml/svg/<b64_data>')
def yaml_to_svg(b64_data):
    data_yaml = decode_base64url(b64_data)
    logger.debug(data_yaml)
    data = Resolver().resolve(data_yaml)
    svg = render(data)
    resp = make_response(svg)
    resp.headers['Content-Type'] = "image/svg+xml; charset=utf-8"
    return resp


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/x-icon')


@app.errorhandler(Exception)
def log_exception(exc):
    logger.error("an error occurred on the request.")
    logger.error(format_exc())
    return InternalServerError(format_exc())


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
