import socket
import threading
from flask import Flask, request

app = Flask(__name__)

def tunnel(client_sock, remote_sock):
    try:
        while True:
            data = client_sock.recv(4096)
            if not data:
                break
            remote_sock.sendall(data)
    except Exception as e:
        print(f"Erro no túnel: {e}")
    finally:
        client_sock.close()
        remote_sock.close()

@app.route('/proxy_https', methods=['CONNECT'])
def proxy_https():
    raw_uri = request.environ.get('RAW_URI')
    if not raw_uri:
        return "RAW_URI não encontrado", 400

    try:
        host_port = raw_uri.split(' ')[1]
        host, port = host_port.split(':')
        port = int(port)
    except Exception as e:
        return f"Erro ao processar RAW_URI: {e}", 400

    try:
        remote = socket.create_connection((host, port))
        client = request.environ['wsgi.input'].raw._sock  # cuidado, pode falhar em outros servidores WSGI

        client.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")

        t1 = threading.Thread(target=tunnel, args=(client, remote), daemon=True)
        t2 = threading.Thread(target=tunnel, args=(remote, client), daemon=True)
        t1.start()
        t2.start()

        # Não bloqueia o worker Flask, retorna logo
        return '', 200
    except Exception as e:
        return f"Erro no túnel CONNECT: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)
