from flask_cors import CORS
from flask import Flask

app = Flask(__name__,
            static_folder="./dist/static",
            template_folder="./dist")


def after_request(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


app.after_request(after_request)
CORS(app, supports_credentials=True)  # 设置跨域
#app.run(host='0.0.0.0', port=5000)

from .routers import *  # 放在最后避免循环引入
