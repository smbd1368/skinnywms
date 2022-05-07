# (C) Copyright 2012-2019 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation nor
# does it submit to any jurisdiction.

import os
import argparse

from flask import Flask, request, Response, render_template, send_file, jsonify
from flask_cors import CORS, cross_origin
from .server import WMSServer
from .plot.magics import Plotter, Styler
from .data.fs import Availability


application = Flask(__name__)

cors = CORS(application)
application.config['CORS_HEADERS'] = 'Content-Type'

demo = os.path.join(os.path.dirname(__file__), "testdata", "sfc.grib")

demo = os.environ.get("SKINNYWMS_DATA_PATH", demo)

parser = argparse.ArgumentParser(description="Simple WMS server")

parser.add_argument(
    "-f",
    "--path",
    default=demo,
    help="Path to a GRIB or NetCDF file, or a directory\
                         containing GRIB and/or NetCDF files.",
)
parser.add_argument(
    "--style", default="", help="Path to a directory where to find the styles"
)

parser.add_argument(
    "--user_style", default="", help="Path to a json file containing the style to use"
)

parser.add_argument("--host", default="0.0.0.0", help="Hostname")
parser.add_argument("--port", default=5000, help="Port number")
parser.add_argument(
    "--baselayer", default="", help="Path to a directory where to find the baselayer"
)
parser.add_argument(
    "--magics-prefix",
    default="magics",
    help="prefix used to pass information to magics",
)


args = parser.parse_args()

if args.style != "":
    os.environ["MAGICS_STYLE_PATH"] = args.style + ":ecmwf"

if args.user_style != "":
    os.environ["MAGICS_USER_STYLE_PATH"] = args.user_style

server = WMSServer(
    Availability(args.path), Plotter(args.baselayer), Styler(args.user_style)
)


server.magics_prefix = args.magics_prefix


@application.route("/wms", methods=["GET"])
@cross_origin()
def wms():
    request_args = request.args.to_dict()

    w_model = request_args['model'] if "model" in request_args else 'ecmwf'
    date = request_args['date'] if "date" in request_args else '20220501'
    time = request_args['time'] if "time" in request_args else '00'

    location = "data/" + w_model + "/" + date + "/" + time + "/"

    server.setAvailability(Availability(location))

    return server.process(
        request,
        Response=Response,
        send_file=send_file,
        render_template=render_template,
        reraise=True,
    )


def GetDirectoriesName(base_path, depth):
    if os.path.isdir(base_path):
        d = {}
        for path1 in os.listdir(base_path):
            d[path1] = {}
            path2 = os.path.join(base_path, path1)
            if os.path.isdir(path2):
                for times in os.listdir(path2):
                    d[path1][times] =  os.listdir(os.path.join(path2, times))
    else:
        d = []

    return d

@application.route("/listdir", methods=["GET"])
def ListDir():
    data = f('./data')
    return jsonify(data)


@application.route("/timeseries", methods=["GET"])
def timeseries():
    totalDir = 0
    for base, dirs, files in os.walk("./data"):
        for directories in dirs:
            totalDir += 1
    return jsonify({"count":  totalDir})


@application.route("/availability", methods=["GET"])
def availability():
    return jsonify(server.availability.as_dict())


@application.route("/", methods=["GET"])
def index():
    return render_template("leaflet_demo.html")


def execute():
    application.run(port=args.port, host=args.host, debug=True, threaded=False)
