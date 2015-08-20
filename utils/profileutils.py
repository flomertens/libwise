'''
Created on Jul 31, 2012

@author: fmertens
'''

import cProfile
try:
    import line_profiler
    line_profil = line_profiler.LineProfiler()
except:
    line_profil = None

profiler = None


def start():
    global profiler, line_profiler

    profiler = cProfile.Profile()
    profiler.enable()


def report_line_profile():
    print "\nFunction Line Time"
    print "-------------------------"
    lstats = line_profil.get_stats()
    stats = lstats.timings
    unit = lstats.unit
    for (fn, lineno, name), timings in sorted(stats.items()):
        line_profiler.show_func(fn, lineno, name, stats[fn, lineno, name], unit)


def done(stdout=True, file=None):
    global profiler, line_profiler

    if not profiler:
        print "Profiler not started"
        return
    profiler.disable()
    if file is not None:
        profiler.dump_stats(file)
    if stdout:
        profiler.print_stats("cumulative")
        if line_profil is not None and len(line_profil.functions) > 0:
            report_line_profile()
