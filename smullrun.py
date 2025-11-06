"""
Run Smullyanic Dynasty solver on sequence of examples.
"""

from typing import Optional
import subprocess
import sys
import os
import time
import argparse

if sys.platform == 'linux':
    import psutil

def parse_command(cmdline: Optional[str] = None) -> argparse.Namespace:
    """Extract command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Run Smullyanic Dynasty puzzle solver.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v', '--verbose', help='increase output verbosity',
                        default=0, action='count')
    parser.add_argument('-i', '--interpreter', help='python interpreter',
                        type=str, default=os.path.basename(sys.executable))
    parser.add_argument('-F', '--filename', help='script file to run',
                        type=str, default='smull.py')
    parser.add_argument('-o', '--output', help='output file',
                        type=str, default='tmp.out')
    parser.add_argument('-f', '--first', help='first puzzle to solve',
                        type=int, default=0)
    parser.add_argument('-l', '--last', help='last puzzle to solve',
                        type=int, default=51)
    parser.add_argument('-t', '--timeout', help='timeout (in s) for each puzzle',
                        type=int, default=60)
    parser.add_argument('-s', '--solutions', help='maximum number of solutions',
                        type=int, default=10)
    parser.add_argument('-e', '--extra-args', help='extra arguments for each puzzle',
                        type=str, default=None)
    if cmdline is None:
        return parser.parse_args()
    else:
        return parser.parse_args(cmdline.split())

if __name__ == '__main__':

    startTime = time.time()
    if sys.platform == 'linux':
        process = psutil.Process()
        initialTimes = sum(process.cpu_times()[:4]) # exclude iowait

    args = parse_command()

    fixedargs = [args.interpreter, args.filename, '-s{0}'.format(args.solutions)]
    if args.extra_args is not None:
        fixedargs = fixedargs + args.extra_args.split()
    fixedargs = fixedargs + ['-p']
    banner = '================================= {0:2} ================================='
    exceptions = 0

    with open(args.output, 'w', encoding='utf-8') as file_obj:
        for i in range(args.first, args.last + 1):
            print(banner.format(i), file=file_obj, flush=True)
            if args.verbose > 0:
                print('Running', ' '.join(fixedargs + [str(i)])) 
            try:
                subprocess.run(fixedargs + [str(i)], stdout=file_obj,
                               encoding='utf-8', check=True,
                               timeout=args.timeout)
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError) as e:
                exceptions += 1
                print('Caught', e, file=file_obj, flush=True)

    # Print summary.
    print('Ran puzzles {0}-{1}'.format(args.first, args.last))
    if exceptions > 0:
        print('Caught', exceptions, 'exceptions' if exceptions > 1 else 'exception',
              '(see', args.output, 'for details)')
    elapsedTime = time.time() - startTime
    print('Elapsed time: {0:.4} s'.format(elapsedTime))
    if sys.platform == 'linux':
        finalTimes = sum(process.cpu_times()[:4]) # exclude iowait
        runTime = finalTimes - initialTimes
        print('    CPU time: {0:.4} s'.format(runTime))