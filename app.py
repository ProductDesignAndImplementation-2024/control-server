import sys
import os
from flask import Flask, request, jsonify, render_template, send_from_directory
import paramiko
from flask_socketio import SocketIO, emit
from pyModbusTCP.client import ModbusClient
sys.path.append('c:/koulu/ProductDesign/tello-drone-controller')

# Drone files
import intersection_finder as isf
import drone_controlv2 as  drc


app = Flask(__name__)
socketio = SocketIO(app)

host_ip = '10.0.0.2'
port = 5000

#route = []
#route_flag = False

route_image_path = 'c:/koulu/ProductDesign'

current_command = None

c = ModbusClient(host="10.0.0.10")


# API routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/image/<filename>')
def send_image(filename):
    return send_from_directory(route_image_path, filename)


@app.route('/request-route', methods=['GET'])
def request_image():
    #print(isf.main())
    try:
        route = drc.drone_autopilot()
        isf.main()

        """ 
        global route
        global route_flag
        if not route_flag:
            route = drc.drone_autopilot()
            #route = ['f', 'r', 'l', 'r', 'l', 'l', 'r', 'r', 'f', 'r', 'l', 'r', 'f', 'f', 'f']
            route_flag = True
        """      
        return jsonify({"route": route}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.get_json()
    if 'message' in data:
        message = data['message']
        
        # set UR-registers
        if message[11:] == "waiting for package":
            if c.write_single_register(1, 1): 
                print("write ok")
            else:
                print("write fail")
            print(message[11:])
        if message[11:] == "waiting for package removal":
            if c.write_single_register(16, 1):
                print("write ok")
            else:
                print("write fail")
            print(message[11:])
        if message[8:] == "package removed":
            # reset UR-register
            if c.write_single_register(16, 0):
                print("write ok")
            else:
                print("write fail")
            print(message[8:])
        if message[8:] == "picked up package and is requesting route":
            # reset UR-register
            if c.write_single_register(1, 0):
                print("write ok")
            else:
                print("write fail")
            print(message[8:])  

        
        print(f"Message received: {message}")
        socketio.emit('message', {'message': message})
        return jsonify({'status': 'success', 'message': message}), 200
    else:
        return jsonify({'error': 'No message specified'}), 400


@app.route('/get-command', methods=['GET'])
def get_command():
    global current_command
    if current_command:
        return jsonify({'command': current_command}), 200
    else:
        return jsonify({'error': 'No command available'}), 404


@app.route('/send-command', methods=['POST'])
def send_command():
    global current_command
    data = request.get_json()
    if 'command' in data:
        current_command = data['command']
        return jsonify({'status': 'success', 'command': current_command}), 200
    else:
        return jsonify({'error': 'No command specified'}), 400


@app.route('/run-ssh-command', methods=['POST'])
def run_ssh_command():
    data = request.get_json()
    if 'command' in data and 'ip' in data:
        command = data['command']
        ip = data['ip']
        try:
            hostname = ip
            port = 22
            username = 'pi'
            password = 'robots1234'

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname, port, username, password)

            stdin, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            print("Output: ", output)
            ssh.close()
            
            if error:
                return jsonify({'error': error}), 500
            else:
                return jsonify({'message': output if output else 'Command executed successfully'}), 200
        except Exception as e:
            print("Error: ", str(e))
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'No command or IP provided'}), 400


if __name__ == '__main__':
    #app.run(debug=True, host=host_ip, port=port)
    socketio.run(app, debug=True, host=host_ip, port=port)