import X86, Arm, Power
import argparse
import os, sys, shutil
from Arch import Arch
import Linker
import Globals
import glob
from Globals import er

# Instantiate one object representing each architecture and put them
# in a dictionary indexed by the Arch "enum" (see Arch.py)
x86_obj = X86.X86()
arm_obj = Arm.Arm()
power_obj = Power.Power()

archs = { 	Arch.X86 : x86_obj,
			Arch.ARM : arm_obj,
			Arch.POWER : power_obj,
		}

#TODO add power later
considered_archs = [archs[Arch.X86], archs[Arch.ARM]]
considered_sections = [".text", ".data", ".bss", ".rodata", ".tdata", 
		".tbss"]

###############################################################################
# buildArgparser
###############################################################################
def buildArgParser():
	""" Construct the command line argument parser object """

	res = argparse.ArgumentParser(description="Align symbols in binaries from" +
		" multiple ISAs")
	
	res.add_argument("--x86-bin", help="Path to the input x86 executable",
		required=True)
	res.add_argument("--arm-bin", help="Path to the input ARM executable",
		required=True)
	res.add_argument("--x86-map", help="Path to the x86 memory map file " +
		"corresponding to the x86 binary (generated through ld -MAP)",
		required=True)
	res.add_argument("--arm-map", help="Path to the ARM memory map file " +
		"corresponding to the x86 binary (generated through ld -MAP)",
		required=True)
	res.add_argument("--x86-object-files", nargs="+", help="List of input " +
		"object files (x86)", required=True)
	res.add_argument("--arm-object-files", nargs="+", help="List of input " +
		"object files (arm)", required=True)
	res.add_argument("--power-object-files", nargs="+", help="List of input " +
	"object files (power)", required=False) #TODO set to true later
	res.add_argument("--work-dir", help="Temporary work directory",
		default="/tmp/align")
	res.add_argument("--clean-work-dir", type=bool, 
		help="Delete work directory when done",	default=True)

	return res

###############################################################################
# parseAndCheckArgs
###############################################################################
def parseAndCheckArgs(parser):
	args = parser.parse_args()
	# TODO checks here

	return args

###############################################################################
# prepareWorkDir
###############################################################################
def prepareWorkDir(args):
	""" Clean the working directory and copy input files in it """
	workdir = args.work_dir
	if os.path.exists(workdir):
		if not os.path.isdir(workdir):
			er(workdir + " exists and is not a directory, remove it first")
			sys.exit(-1)
		shutil.rmtree(workdir)

	os.makedirs(workdir)
	
	# Copy binaries and map files
	# TODO power
	shutil.copy(args.x86_bin, workdir + "/" + 
		archs[Arch.X86].getExecutable())
	shutil.copy(args.arm_bin, workdir + "/" + 
		archs[Arch.ARM].getExecutable())
	shutil.copy(args.x86_map, workdir + "/" + 
		archs[Arch.X86].getMapFile())
	shutil.copy(args.arm_map, workdir + "/" + 
		archs[Arch.ARM].getMapFile())

	# Copy linker script templates
	# TODO power
	templates_loc = Globals.POPCORN_LOCATION + "/share/align-script-templates"
	linkerScriptTemplates=os.listdir(templates_loc)
	for f in linkerScriptTemplates:
		shutil.copy(templates_loc + "/" + f, workdir + "/" + f)

	# Copy object files
	# TODO power
	x86ObjsSubdir = Globals.X86_OBJS_SUBDIR
	armObjsSubdir = Globals.ARM_OBJS_SUBDIR
	os.makedirs(workdir + "/" + x86ObjsSubdir)
	os.makedirs(workdir + "/" + armObjsSubdir)
	for f in args.x86_object_files:
		shutil.copy(f, workdir + "/" + x86ObjsSubdir + "/" + 
			os.path.basename(f))
	for f in args.arm_object_files:
		shutil.copy(f, workdir + "/" + armObjsSubdir + "/" + 
			os.path.basename(f))

	return

###############################################################################
# setObjectFiles
###############################################################################
def setObjectFiles(args):
	workdir = args.work_dir
	
	archs[Arch.X86].setObjectFiles(glob.glob(workdir + "/" + 
		Globals.X86_OBJS_SUBDIR + "/*.o"))
	archs[Arch.ARM].setObjectFiles(glob.glob(workdir + "/" + 
		Globals.ARM_OBJS_SUBDIR + "/*.o"))
	# TODO power

###############################################################################
# Order symbols
###############################################################################
# in each section, the symbols will be ordered by number of architectures 
# referencing the symbols in questions
# sl is a list of Symbol instances (should correspond to one section)
# return as a result an ordered symbol list
def orderSymbolList(sl):
	res = []

	# TODO Explain the trick
	for order in list(reversed(range(1, len(considered_archs)+1))):
		for symbol in sl:
			referencingArchs = len(considered_archs)
			for arch_instance in considered_archs:
				arch = arch_instance.getArch()
				if symbol.getAddress(arch) == -1:  # not referenced by this arch
					referencingArchs -= 1

			if referencingArchs == order:
				res.append(symbol)

	return res

###############################################################################
# align
##############################################################################
# sl is a list of symbols (same as for orderSymbolsList that should correspond
# to one section
def align(sl):
	dot = 0		# starting offset of the section



###############################################################################
# main
###############################################################################
if __name__ == "__main__":
	# Argument parsing stuff
	parser = buildArgParser()
	args = parseAndCheckArgs(parser)

	# Prepare work directory and switch to it as cwd
	prepareWorkDir(args)
	os.chdir(args.work_dir)
	setObjectFiles(args)

	# List of per-section symbols that we are going to fill and manipulate
	work = {}
	for section in considered_sections:
		work[section] = []

	# Add symbols to the list
	for arch in considered_archs:
		arch.updateSymbolsList(work)

	# Order symbols in each section based on the number of arch referencing 
	# each symbol 
	for section in considered_sections:
		work[section] = orderSymbolList(work[section])

	# perform the alignment


	for arch in considered_archs:
		Linker.Linker.produceLinkerScript(work, arch)
		arch.goldLink(arch.getObjectFiles())	
