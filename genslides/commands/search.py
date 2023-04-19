import genslides.commands.simple as SimpleCommand

class SearchCommand(SimpleCommand):
	def __init__(self, input) -> None:
		super().__init__()
		self.prompt = input
	def execute(self):
		print("Some search")
	def unexecute(self):
		print("Revert results")

                  