from . import app
from flask import request, jsonify, render_template, Response
import socket
import time
import _thread
MaxBytes = 1024 * 1024


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template("index.html")


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# host = '192.168.43.48'
host = '127.0.0.1'
port = 14466
global picture
global pic_len
global client_n
global client_group
pic_len = 0


def opentcp():
    global client_n
    global client_group
    global control_client
    global server
    server.bind((host,port))
    server.listen()  # 监听
    client_n = 0
    client_group = []
    while 1:
        if client_n == 1:
            break
        client, addr = server.accept()  # 等待客户端连接
        client_group.append(client)
        print(addr, " 连接上了")
        control_client = client
        client_n = client_n + 1
        _thread.start_new_thread(recv_t,
                                 ("recv_t" + str(addr), 0, client_n - 1, addr))


def recv_t(threadName, delay, client, addr):  # 接收处理函数
    global picture
    global client_n
    global client_group
    global control_client
    i = 0
    while client_n < 1:
        time.sleep(0.1)
    send_data(client_group[client], "$$$$")
    data = client_group[client].recv(MaxBytes)
    # print(data)
    if data == b'k210 has recived!':
        control_client = client_group[client]
    while 1:
        i = i + 1
        data = b""
        readbuf = b''
        data = client_group[client].recv(MaxBytes)
        if b'img_start' in data:
            '''
            with open("./snap" + str(i)+".jpeg", "ab") as f:
                print("start")
                find = data.find(b"img_start")
                f.write(data[find+9:])
                for n in range(1, 1000):
                    if b"img_end" in data:
                        find = data.find(b"img_end")
                        if find != 0:
                            f.write(data[0:find])
                        print("end")
                        break
                    data = client.recv(MaxBytes)
                    f.write(data)
            print("end")
            '''
            # print("start")
            find = data.find(b"img_start")
            if data[find + 9] != 0xff or data[find + 10] != 0xd8:
                continue
            readbuf += data[find + 9:]
            for n in range(1, 1000):
                if b"img_end" in data:
                    find = data.find(b"img_end")
                    if find != 0:
                        readbuf += data[0:find]
                    # print("end")
                    break
                data = client_group[client].recv(MaxBytes)
                readbuf += data
            if readbuf[-2] == 0xff and readbuf[-1] == 0xd9:

                picture = readbuf
            # print("end", readbuf)
        # else:
        #     print("")  # data)
        # client.send(bytes("recived!".encode()))
        # print(len(data))


def send_data(client, data):
    try:
        client.send(bytes(data.encode()))
    except BaseException as e:
        print("出现异常：", repr(e))
    finally:
        server.close()  # 关闭连接


@app.route('/senddata_tcp', methods=['GET', 'POST'])
def senddata_tcp():
    global control_client
    if request.method == 'POST':
        send_data(control_client, request.json["command"])
        return jsonify({'result': 1})
    else:
        return jsonify({'error': 1})


class VideoCamera(object):
    def get_frame(self):
        global picture
        global pic_len
        if pic_len == len(picture):
            print(len(picture))
        time.sleep(0.02)
        while len(picture) < 1000:
            time.sleep(0.02)
        while picture[-2] != 0xff or picture[-1] != 0xd9:
            time.sleep(0.02)
        return picture


def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(gen(VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# @app.route('/opentcp', methods=['GET', 'POST'])
def urlopentcp():
    _thread.start_new_thread(opentcp, )
    # return jsonify({'code': 1})


urlopentcp()