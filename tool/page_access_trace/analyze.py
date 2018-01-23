#!/usr/bin/python3

''' Analyze a page access trace (PAT) file. '''

import sys
from sys import float_info
import argparse
from os import path

import pat
import plot
import symtab
import metisgraph

###############################################################################
# Parsing
###############################################################################

def parseArguments():
    parser = argparse.ArgumentParser(
        description="Run various analyses on page access trace (PAT) files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    config = parser.add_argument_group("Configuration Options")
    config.add_argument("-i", "--input", type=str, required=True,
            help="Input page access trace file")
    config.add_argument("-b", "--binary", type=str,
            help="Binary that was run to generate the trace")
    config.add_argument("-s", "--start", type=float, default=-1.0,
            help="Only analyze trace entries with timestamps after this time")
    config.add_argument("-e", "--end", type=float, default=float_info.max,
            help="Only analyze trace entries with timestamps before this time")
    config.add_argument("--no-code", action="store_true",
            help="Ignore code page faults - requires -b/--binary")
    config.add_argument("--no-data", action="store_true",
            help="Ignore data page faults - requires -b/--binary")
    # TODO filter by thread
    # TODO filter by access type
    config.add_argument("-v", "--verbose", action="store_true",
            help="Print status updates & verbose files")

    placement = parser.add_argument_group("Thread Placement Options")
    placement.add_argument("-p", "--partition", action="store_true",
            help="Run the graph partitioning algorithm to place threads")
    placement.add_argument("--nodes", type=int, default=1,
            help="Number of nodes over which to distribute threads")
    placement.add_argument("--gpmetis", type=str, default="gpmetis",
            help="Location of the 'gpmetis' graph partitioning executable")
    placement.add_argument("--save-partition", action="store_true",
            help="Save intermediate files generated by partitioning process")

    plot = parser.add_argument_group("Plotting Options")
    plot.add_argument("-t", "--trend", action="store_true",
            help="Plot frequencies of page faults over time")
    plot.add_argument("--chunks", type=int, default=100,
            help="Number of chunks into which to divide the application")
    plot.add_argument("--per-thread", action="store_true",
            help="Plot per-thread page fault frequencies - requires -t/--trend")
    plot.add_argument("--save-plot", type=str,
            help="If specified, save the plot to file")

    problemsym = parser.add_argument_group("Per-symbol Access Options")
    problemsym.add_argument("-l", "--list", action="store_true",
                    help="List memory objects that cause the most faults " \
                         "- requires -b/--binary")
    problemsym.add_argument("--num-syms", type=int, default=10,
                    help="Number of symbols to list")

    return parser.parse_args()

def sanityCheck(args):
    args.input = path.abspath(args.input)
    assert path.isfile(args.input), \
        "Invalid page access trace file '{}'".format(args.input)

    if args.binary != None:
        args.binary = path.abspath(args.binary)
        assert path.isfile(args.binary), \
            "Binary '{}' doesn't exist".format(args.binary)
    elif args.no_code or args.no_data:
        print("WARNING: cannot filter code or data faults without binary")
        args.no_code = False
        args.no_data = False

    assert args.start < args.end, \
        "Start time must be smaller than end time (start: {}, end: {})" \
        .format(args.start, args.end)

    if args.partition:
        assert args.nodes >= 1, \
            "Number of nodes must be >= 1 ({})".format(args.nodes)

    if args.trend:
        assert args.chunks > 1, \
            "Number of chunks must be >= 1 ({})".format(args.chunks)

    if args.list:
        assert args.binary, "Must specify a binary for -l/--list"
        assert args.num_syms > 0, \
            "Number of symbols must be >= 1 ({})".format(args.num_syms)

###############################################################################
# Driver
###############################################################################

if __name__ == "__main__":
    args = parseArguments()
    sanityCheck(args)

    # Instantiate objects needed for parsing & analysis
    if args.binary: symbolTable = symtab.SymbolTable(args.binary, args.verbose)
    else: symbolTable = None
    config = pat.ParseConfig(args.start, args.end, symbolTable,
                             args.no_code, args.no_data)

    if args.partition:
        graph = pat.parsePATtoGraph(args.input, config, args.verbose)
        metisgraph.placeThreads(graph, args.nodes, args.gpmetis,
                                args.save_partition, args.verbose)

    if args.trend:
        chunks, ranges = pat.parsePATtoTrendline(args.input, config,
                                                 args.chunks, args.per_thread,
                                                 args.verbose)
        plot.plotPageAccessFrequency(chunks, ranges, args.per_thread,
                                     args.save_plot)

    if args.list:
        sortedSyms = \
            pat.parsePATforProblemSymbols(args.input, config, args.verbose)
        print("\n{:30} | Number of Accesses".format("Program Object"))
        print("{:-<30}-|-------------------".format("-"))
        for sym in sortedSyms[:args.num_syms]:
            print("{:30} | {}".format(sym[1], sym[0]))
