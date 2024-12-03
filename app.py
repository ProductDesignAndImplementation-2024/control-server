from flask import Flask, request, jsonify, render_template
import paramiko
from flask_socketio import SocketIO, emit
from pyModbusTCP.client import ModbusClient

app = Flask(__name__)
socketio = SocketIO(app)

host_ip = 'localhost'
port = 5000

route = ["r","l","l","l","f","l","l","r","r","r","r","f","r","r","f","r","f","r","s"]

current_command = None

c = ModbusClient(host="10.0.0.10")

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/request-route', methods=['GET'])
def request_image():
    try:
        return jsonify({"route": route}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.get_json()
    if 'message' in data:
        message = data['message']
        
        if message[11:] == "waiting for package":
            if c.write_single_register(16, 0):
                print("write ok")
            else:
                print("write fail")
        if message[11:] == "waiting for package removal":
            if c.write_single_register(1, 0):
                print("write ok")
            else:
                print("write fail")
        
        print(f"Message received: {message}")
        print(message[11:])
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
    if 'command' in data:
        command = data['command']
        try:
            hostname = '10.0.0.34' #GoPiGo3ONE IP
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
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'No command provided'}), 400


if __name__ == '__main__':
    #app.run(debug=True, host=host_ip, port=port)
    socketio.run(app, debug=True, host=host_ip, port=port)