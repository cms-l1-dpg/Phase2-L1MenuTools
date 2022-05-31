import sys
from functions import *

class Verbose:
	def __init__(self, master, level = 2):
		self.master = master
		self.level  = level
		self.f      = open(self.master.bundledir+"/log","w")
	def close(self):
		self.f.close()
	def error(self, message):
		self.talk("ERROR: "  +message, 0)
		sys.exit()
	def talk(self, message, required=2):
		message = "> "+timestamp()+" "+message
		if self.level >= required: print message
		self.f.write(message+"\n")
	def warning(self, message):
		self.talk("WARNING: "+message, 1)
