# Class for commands
class Command():

    def __init__(self, name:str, server_command:bool, user:str, command:str, path:str, strip:bool) -> None:
        self.name = name
        self.server_command = server_command
        self.user = user
        self.command = command
        self.path = path
        self.strip = strip
        self.input = self.require_input

    def require_input(self) -> bool:
        return "{}" in self.command

    def execute(self) -> bool:
        return