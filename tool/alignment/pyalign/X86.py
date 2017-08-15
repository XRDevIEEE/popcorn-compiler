import Symbol, Globals
from AbstractArchitecture import AbstractArchitecture 
from Arch import Arch

class X86(AbstractArchitecture):

	def __init__(self):
		# Prefix for the gcc compiler name
		self._gccPrefix = "x86_64-linux-gnu"
		# Executable name
		self._executable = "bin_x86"
		# Name of the map file used in multiple steps of the alignment process
		self._mapFile= "map_x86"
		# Linker script used in multiple steps
		self._linkerScript = "linker_script_x86.x"
		# Linker script template
		self._linkerScriptTemplate = "ls_x86.template"
		# list of object files, to be set at runtime
		self._objectFiles = []

	def getArch(self):
		return Arch.X86

	def getArchString(self):
		return "X86"