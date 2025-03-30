from ai_utils import generate_response, optimize_history
from parser import Config, logging
from KSockets import ClientObject
import json
import uuid

class Client_Handler:
    def __init__(self, client: ClientObject, name: str) -> None:
        self.client = client
        self.history = {}
        self.longterm_memory = []
        self.context = []
        self.sid = str(uuid.UUID(int=self.client.id))
        self.atc = {}
        self.name = name

    def start(self):
        "Should be ran on a threaded environment"
        self.client.parent.client_liveliness(self.client)
        should_not_name = False
        while self.client.isactive:
            raw_msg = self.client.receive()
            if not isinstance(raw_msg, dict):
                break
            elif raw_msg.get('purpose') != "prompt":
                break
            message = raw_msg['data']
            result_slash = self.slash_command_parser(message)
            if result_slash:
                logging.info(f"[{self.sid}] Received command from user; length: {len(message)}")
                command, attribute = self.slash_command(result_slash[0], result_slash[1])
                if command == 0 or command == 2:
                    self.send_data("ready")
                    continue
                elif command == 1:
                    message = attribute
                    should_not_name = True
                elif command == -1:
                    self.send_data("cmdNull")
                    continue
            logging.info(f"[{self.sid}] Received prompt from user; length: {len(message)}")
            self.process_message(message, no_append_name=should_not_name)
            should_not_name = False #Set to default
            # print("History:", self.history)
            # print("Long:", self.longterm_memory)
        self.client.close()

    def send_history(self):
        history_parsed = json.dumps(self.history)
        self.send_data('save', data=history_parsed)

    def send_data(self, purpose, data=None):
        """
        purpose = waiting, reply, error, ready
        For reply/error:
            data: will relay data
        """
        self.client.send({
            "purpose": purpose,
            "data": data
        })
        if purpose == 'reply':
            logging.info(f"[{self.sid}] Replied to the user")
        elif purpose == 'ready':
            logging.info(f"[{self.sid}] Ready to the user")

    def process_message(self, message, no_append_name = False):
        self.send_data(purpose="waiting")
        self.history[self.sid] = self.history.get(self.sid, [])
        if not no_append_name:
            message_named = f"[{self.name}] {message}"
        else:
            message_named = message
        self.history[self.sid].append({"role": "user", "content": message_named})
        if len(self.longterm_memory) > Config.longterm_memory: self.longterm_memory.pop(0)
        # print("History: ", self.history)
        # print("Context: ", self.context)
        # print("longterm: ", self.longterm_memory)
        response, status = generate_response(instructions=Config.get_instructions(), history=[*self.longterm_memory, *self.history[self.sid]])
        if status:
            if len(self.history[self.sid]) >= Config.max_history:
                if not Config.optimize_memory: 
                    self.history[self.sid] = self.history[self.sid][-Config.max_history:]
                elif Config.optimize_memory:
                    captured = self.history[self.sid][0+len(self.context)]
                    self.context.append(captured)
                    if len(self.context) >= Config.context: 
                        optimized_data = optimize_history(Config.get_instructions(optimizer=True), self.context)
                        if not optimized_data:
                            logging.warning("Failed to optimize data, due to an error")
                        else:
                            self.history[self.sid] = self.history[self.sid][-Config.max_history:]
                            self.longterm_memory.append(optimized_data)
                            self.context = []
            else:
                captured = None
            #post response
            self.history[self.sid].append({"role": "assistant", "content": response})
            self.send_response(response)
        else:
            logging.error(response) #Necessary
            self.history[self.sid].append({"role": "assistant", "content": "[Error input, ignore]"})
            self.send_data(purpose="error", data="An error has occured while generating my response. Please contact the administrator.")
        
    def send_response(self, response):
        if response is not None:
            try:
                self.send_data(purpose="reply", data=response)
            except Exception as e:
                logging.error(f"[Client Handler] Delivery failed due to: {e}")
                self.send_data(purpose="error", data="I apologize for any inconvenience caused. It seems that there was an error preventing the delivery of my message.")
        else:
            logging.error("[Client Handler] Delivery failed due to: No response message" )
            self.send_data(purpose="error", data="I apologize for any inconvenience caused. It seems that there was an error preventing the delivery of my message.")
    
    def slash_command_parser(self, message: str):
        # Check if the message starts with a slash
        if message.startswith('/'):
            # Split the message into command and argument
            parts = message[1:].split(' ', 1)  # Split once at the first space
            command = parts[0]  # First part is the command
            argument = parts[1] if len(parts) > 1 else ''  # Second part is the argument (if present)
            return (command, argument)  # Return command and argument as a tuple
        else:
            return None  # Not a slash command
    
    def _remove_context(self, data):
        try:
            self.context.remove(data)
            return True
        except ValueError:
            return False

    def slash_command(self, command_type, attributes):
        """
        returns <should rerun: int> <attribute or new prompt: string>
        \n
        -1 - Command not found
        \n        
        0 - Will return for reset empty args
        \n        
        1 - Rerun/Send response
        \n        
        2 - Save
        \n

        """
        if command_type == "reset" or command_type == "rst" or command_type == "res":
            captured_1, captured_2 = self.history[self.sid][-2:]
            self.history[self.sid] = self.history[self.sid][:-2] #Remove 1 user and 1 AI prior
            self._remove_context(captured_1)
            self._remove_context(captured_2)
            if attributes:
                return 0, attributes
            return 0, None
        elif command_type == "regenerate" or command_type == "regen" or command_type == "reg":
            print(self.history[self.sid])
            last_assistant = self.history[self.sid].pop()
            last_message = self.history[self.sid].pop() #user
            self._remove_context(last_assistant)
            self._remove_context(last_message)
            return 1, last_message['content']
        elif command_type == "narration" or command_type == "narrate" or command_type == "nar":
            if attributes:
                return 1, attributes
            return 1, None
        elif command_type == "save":
            self.send_history()
            return 2, None 
        return -1, None