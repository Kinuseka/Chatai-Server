from KSockets import SimpleServer, ClientObject
from KSockets.secure import wrap_secure
from KSockets.multiplexor import handle_event
from client_handler import Client_Handler
from parser import Config, logging
from ai_utils import list_models
import dotenv


@handle_event
def gateway(client: ClientObject):
    logging.info(f"Connected client; {client.address[0]}:{client.address[1]}")
    meta_client = client.receive()
    password = meta_client.get("cli-auth", None)
    if not meta_client: 
        client.close()
        return
    elif password != Config.key_auth:
        client.close()
        return
    client.send({
        "purpose": "info",
        "data": { 
            "model": Config.model,
            "instruction_config": Config.instructions,
            "client_version": Config.client_version,
            "server_version": Config.server_version
        }
    })
    event = Client_Handler(client=client, name=meta_client.get("name", "User"))
    event.start() #pause here

def main():
    logging.info(f"We are officially online and listening: {server.address}")
    while True:
        client = server.accept()
        if client:
            gateway(client)

if __name__ == "__main__":
    import sys, os
    def resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
    for model in list_models():
        if model:
            logging.info(f"Models: {model.id}")
    try:
        server = wrap_secure(SimpleServer((Config.ip, Config.port)), keypath=resource_path("ssl/key_file.key"), certpath=resource_path("ssl/certificate_file.crt"))
        # server = SimpleServer((Config.ip, Config.port))
        server.create_server()
        server.listen()
        main()
    except KeyboardInterrupt:
        server.close()
        sys.exit(0)