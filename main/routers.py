from . import app
from flask import request, jsonify, render_template, Response
from multiprocessing import shared_memory
import socket
import time
import _thread
import re
import json

MaxBytes = 1024 * 1024
host = '0.0.0.0'
port = 8266

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

data = {
    "adc_v": 0,
    "date": [],
    "temperature": 0,
    "humidity": 0,
}

global client_n
global client_group
control_client = ""
pic_len = 0


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template("index.html")


def opentcp():
    global client_n
    global client_group
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))  # 绑定端口
    server.listen(10)  # 监听
    client_n = 0
    client_group = []
    client, addr = server.accept()  # 等待客户端连接
    client_group.append(client)
    print(addr, " 连接上了")
    client_n = client_n + 1
    _thread.start_new_thread(recv_t,
                             ("recv_t" + str(addr), 0, client_n - 1, addr))


def set_adc_v(adc_v):
    global data
    data["adc_v"] = adc_v


def get_adc_v():
    global data
    return data["adc_v"]


def recv_t(threadName, delay, client, addr):  # 接收处理函数
    global client_n
    global control_client
    global client_group

    i = 0

    control_client = client_group[client] 
    while 1:
        i = i + 1
        rec = b""
        rec = client_group[client].recv(MaxBytes)
        cmds = str(rec).split('\\n\\x00')

        for cmd in cmds:
            if "adc_v" in cmd:
                set_adc_v(re.findall(r"\d+\.?\d*", cmd))
                
            if "date" in cmd: 
                data["date"] = re.findall(r"\d+\.?\d*", cmd) 
                with open('data.json', 'w') as f:
                    json.dump(data, f)
            if "time" in cmd: 
                data["time"] = re.findall(r"\d+\.?\d*", cmd) 
                with open('data.json', 'w') as f:
                    json.dump(data, f)
            if "temperature" in cmd:
                data["temperature"] = re.findall(r"\d+\.?\d*", cmd)
            if "humidity" in cmd:
                data["humidity"] = re.findall(r"\d+\.?\d*", cmd)

            #print(date)


@app.route('/api/get_data', methods=['GET', 'POST'])
def get_data():
    global data
    global control_client
    with open('data.json', 'r') as f:
        data = json.load(f)
    return jsonify(data)


def send_data():
    old_cmd = ""
    while 1:
        time.sleep(1)
        if control_client:
            try:
                with open('cmd.json', 'r') as f:
                    data = json.load(f)
                if data:
                    cmd = data["cmd"].encode()
                    control_client.send(bytes(data["cmd"].encode()))
                    with open('cmd.json', 'w') as f:
                        json.dump({}, f)
            except BaseException as e:
                print("出现异常：", repr(e))
    
        #server.close()  # 关闭连接


@app.route('/api/cmd', methods=['GET', 'POST'])
def senddata_tcp():
    global control_client
    if request.method == 'POST':
        with open('cmd.json', 'w') as f:
            json.dump({"cmd": request.json["cmd"]}, f)
        
        return jsonify({'result': 1})
    else:
        return jsonify({'error': 1})


@app.route('/api/opentcp', methods=['GET', 'POST'])
def urlopentcp():
    _thread.start_new_thread(opentcp, )
    _thread.start_new_thread(send_data, )
    time.sleep(1)
    return jsonify({'code': 1})


#urlopentcp()