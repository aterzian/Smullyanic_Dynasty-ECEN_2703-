"""
Z3-based solver of Smullyanic Dynasty puzzles.

The objective is to shade some squares, subject to the constraints below.
The "domain" of a square is the set of up to nine cells including the
cell itself and its neighbors.  An unshaded square is a knight.  A shaded
square is a knave.

1. Some squares are shaded.
2. Two shaded squares cannot share an edge.
3. The unshaded squares form a connected region.
4. The clues in unshaded squares are truthful.  They count the number
   of knaves in the square's domain.
5. The clues in shaded squares are not truthful.  They do not count the
   number of knaves in the square's domain.
"""

from typing import Sequence, Optional
import sys
import time
from z3 import SolverFor, Solver, Bool, BoolRef, And, Implies, Xor, Or, Not, PbEq, sat, is_true, ModelRef

from smullinputs import get_grid, check_grid, parse_command
from smulldisplay import print_ascii, print_matplotlib
from smullverify import verify

def evaluate_model(mdl: ModelRef,
                   C: Sequence[Sequence[BoolRef]],
                   H: Sequence[Sequence[Sequence[BoolRef]]],
                   V: Sequence[Sequence[Sequence[BoolRef]]],
                   P: Sequence[Sequence[BoolRef]]
                   ) -> tuple[list[list[bool]], list[list[str]], list[list[bool]]]:
    """Extract a complete solution from the solver's model."""
    nrow = len(C)
    ncol = len(C[0])
    Cbool = [[is_true(mdl.eval(C[i][j], model_completion=True))
              for j in range(ncol)] for i in range(nrow)]
    # Decode the H and V variables into "arrow" characters ('^','v','>','<'),
    # plus ' ' for no arrow and '?' for unexpected cases.
    Estr = [[(' ' if is_true(mdl.eval(And(absent_edge(H[i][j]), absent_edge(V[i][j])),
                                      model_completion=True)) else
              '^' if is_true(mdl.eval(And(up_right_edge(V[i][j]),absent_edge(H[i][j])),
                                      model_completion=True)) else
              'v' if is_true(mdl.eval(And(down_left_edge(V[i][j]),absent_edge(H[i][j])),
                                      model_completion=True)) else
              '>' if is_true(mdl.eval(And(up_right_edge(H[i][j]),absent_edge(V[i][j])),
                                      model_completion=True)) else
              '<' if is_true(mdl.eval(And(down_left_edge(H[i][j]),absent_edge(V[i][j])),
                                      model_completion=True)) else
              '?') for j in range(ncol)] for i in range(nrow)] 
    Pbool = [[is_true(mdl.eval(P[i][j], model_completion=True))
              for j in range(ncol)] for i in range(nrow)]
    return Cbool, Estr, Pbool


def solve_and_print(grid: Sequence[Sequence[Optional[int]]],
                    slv: Solver,
                    C: Sequence[Sequence[BoolRef]],
                    H: Sequence[Sequence[Sequence[BoolRef]]],
                    V: Sequence[Sequence[Sequence[BoolRef]]],
                    P: Sequence[Sequence[BoolRef]]) -> None:
    """Compute and print solutions."""
    args = parse_command()
    nrow = len(C)
    ncol = len(C[0])
    num_solutions = 0

    while slv.check() == sat:
        mdl = slv.model()
        Cbool, Estr, Pbool = evaluate_model(mdl, C, H, V, P)
        verify(grid, Cbool, allow_weak=False)

        # Safe checks for matplotlib and fontsize
        use_matplotlib = getattr(args, "matplotlib", False)
        fontsize = getattr(args, "fontsize", 12)

        if use_matplotlib:
            print_matplotlib(grid, Cbool, Estr, Pbool, fontsize=fontsize)
        else:
            print_ascii(grid, Cbool)

        num_solutions += 1
        print(f"# Found solution {num_solutions}")

        # Safe check for slimit
        slimit = getattr(args, "slimit", None)
        if slimit is not None and num_solutions >= slimit:
            break

        # Block the current solution
        block = [C[i][j] != is_true(mdl.eval(C[i][j], model_completion=True))
                 for i in range(nrow) for j in range(ncol)]
        slv.add(Or(block))

    if num_solutions == 0:
        print("# No solution found")
    else:
        print(f"# Total solutions found: {num_solutions}")

def absent_edge(a: Sequence[BoolRef]) -> BoolRef:
    """Return constraint for absent edge."""
    return And(Not(a[0]), Not(a[1]))

def up_right_edge(a: Sequence[BoolRef]) -> BoolRef:
    """Return constraint for edge pointing up or right."""
    return a[1]

def down_left_edge(a: Sequence[BoolRef]) -> BoolRef:
    """Return constraint for edge pointing down or left."""
    return a[0]

def legal_edge(a: Sequence[BoolRef]) -> BoolRef:
    """Return constraint preventing forbidden edge value."""
    return Or(Not(a[0]), Not(a[1]))

def add_constraints(grid: Sequence[Sequence[Optional[int]]],
                    slv: Solver,
                    C: Sequence[Sequence[BoolRef]],
                    H: Sequence[Sequence[Sequence[BoolRef]]],
                    V: Sequence[Sequence[Sequence[BoolRef]]],
                    P: Sequence[Sequence[BoolRef]]) -> None:
    """Encode puzzle constraints."""
    nrow = len(C)
    ncol = len(C[0])

    #At least one of the first two cells is unshaded (to serve as root)
    slv.add(Or(C[0][0], C[0][1]))
    
    for i in range(nrow):
        for j in range(ncol):
            # Neighbor constraints: no two shaded cells share an edge
            if i < nrow - 1:
                slv.add(Or(C[i][j], C[i+1][j]))
            if j < ncol - 1:
                slv.add(Or(C[i][j], C[i][j+1]))

            # Connectivity constraints for unshaded cells
            absentH = And(Not(H[i][j][0]), Not(H[i][j][1]))
            absentV = And(Not(V[i][j][0]), Not(V[i][j][1]))
            legalH = Or(Not(H[i][j][0]), Not(H[i][j][1]))
            legalV = Or(Not(V[i][j][0]), Not(V[i][j][1]))
            legal = And(legalH, legalV)
            
            slv.add(legal) # Legality defined first to help solver
            if i == 0 and (j == 0 or j == 1):
                # If cell is unshaded and is the root, no parent links exist
                slv.add(Implies(C[i][j], And(absentH, absentV)))
            else:
                # If cell is unshaded and not the root, exactly one of horizontal or vertical arrow is present
                slv.add(Implies(C[i][j], PbEq([(H[i][j][0], 1), (H[i][j][1], 1), (V[i][j][0], 1), (V[i][j][1], 1)], 1)))           

                # Prevent two cells from pointing to each other
                # Prevent out of bounds arrows
                # Ensure that parent link points to an unshaded cell
                if j > 0:
                    slv.add(Implies(H[i][j][0], Not(H[i][j-1][1])))
                    slv.add(Implies(And(C[i][j], H[i][j][0]), C[i][j-1]))
                else:
                    slv.add(Not(H[i][j][0]))
                if j < ncol - 1:
                    slv.add(Implies(H[i][j][1], Not(H[i][j+1][0])))
                    slv.add(Implies(And(C[i][j], H[i][j][1]), C[i][j+1]))
                else:
                    slv.add(Not(H[i][j][1]))
                if i > 0:
                    slv.add(Implies(V[i][j][1], Not(V[i-1][j][0])))
                    slv.add(Implies(And(C[i][j], V[i][j][1]), C[i-1][j]))
                else:
                    slv.add(Not(V[i][j][1]))
                if i < nrow - 1:
                    slv.add(Implies(V[i][j][0], Not(V[i+1][j][1])))
                    slv.add(Implies(And(C[i][j], V[i][j][0]), C[i+1][j]))
                else:
                    slv.add(Not(V[i][j][0]))

            #Parity constraints for
            if j > 0 and j < ncol - 1:
                rightright = Implies(And(H[i][j-1][1], H[i][j][1]), P[i][j-1] == P[i][j])
                leftleft = Implies(And(H[i][j+1][0], H[i][j][0]), P[i][j+1] == P[i][j])
                slv.add(And(rightright, leftleft))
            if i > 0 and i < nrow - 1:
                downdown = Implies(And(V[i-1][j][0], V[i][j][0]), P[i-1][j] == P[i][j])
                upup = Implies(And(V[i+1][j][1], V[i][j][1]), P[i+1][j] == P[i][j])
                slv.add(And(downdown, upup))
            if j < ncol - 1 and i > 0:
                leftup = Implies(And(H[i][j+1][0], V[i][j][1]), P[i][j+1] == P[i][j])
                downright = Implies(And(V[i-1][j][0], H[i][j][1]), P[i-1][j] == P[i][j])
                slv.add(And(leftup, downright))
            if i < nrow - 1 and j > 0:
                upleft = Implies(And(V[i+1][j][1], H[i][j][0]), P[i+1][j] == P[i][j])
                rightdown = Implies(And(H[i][j-1][1], V[i][j][0]), P[i][j-1] == P[i][j])
                slv.add(And(upleft, rightdown))
            if i > 0 and j > 0:
                downleft = Implies(And(V[i-1][j][0], H[i][j][0]), P[i-1][j] == P[i][j])
                ### Constraint for changing parity ###
                rightup = Implies(And(H[i][j-1][1], V[i][j][1]), P[i][j-1] != P[i][j])
                slv.add(And(downleft, rightup))
            if j < ncol - 1 and i < nrow - 1:
                leftdown = Implies(And(H[i][j+1][0], V[i][j][0]), P[i][j+1] == P[i][j])
                ### Constraint for changing parity ###
                upright = Implies(And(V[i+1][j][1], H[i][j][1]), P[i+1][j] != P[i][j])
                slv.add(And(leftdown, upright))            

            # If cell does not have a number, disregard its grid constraint
            if grid[i][j] is None:
                continue

            # Domain: 3x3 centered at (i,j)
            di0 = max(0, i-1)
            di1 = min(nrow, i+2)
            dj0 = max(0, j-1)
            dj1 = min(ncol, j+2)
            domain = [C[x][y] for x in range(di0, di1) for y in range(dj0, dj1)]

            # If unshaded (C[i][j] == True), there are exactly that many shaded cells
            slv.add(Or(Not(C[i][j]), PbEq([(Not(cell), 1) for cell in domain], grid[i][j])))

            # If shaded (C[i][j] == False), there is a different number of shaded cells
            slv.add(Or(C[i][j], Not(PbEq([(Not(cell), 1) for cell in domain], grid[i][j]))))


if __name__ == '__main__':
    starttime = time.process_time()
    sys.stdout.reconfigure(encoding='utf-8')  # type: ignore

    args = parse_command()

    try:
        grid = get_grid(args.puzzle)
        check_grid(grid)
    except Exception as err:
        raise SystemExit(err)

    nrow = len(grid)
    ncol = len(grid[0])

    if args.drawonly:
        if args.matplotlib:
            print_matplotlib(grid, C=None, fontsize=args.fontsize)
        else:
            print_ascii(grid)
        raise SystemExit(0)

    slv = SolverFor('QF_FD')

        # C[i][j] is true if Cell (i,j) is unshaded.
    C = [[Bool(f"C_{i}_{j}") for j in range(ncol)] for i in range(nrow)] # Add definition here.
    
    # For each arrow:
    # (false,false) means "absent."
    # (false,true)  means "pointing up or right."
    # (true,false)  means "pointing down or left."
    # (true,true)   is forbidden.

    # Horizontal edges.
    H = [[[Bool(f'H_{i}_{j}_{k}') for k in range(2)] for j in range(ncol)] for i in range(nrow)] # Add definition here.
    # Vertical edges.
    V = [[[Bool(f'V_{i}_{j}_{k}') for k in range(2)] for j in range(ncol)] for i in range(nrow)] # Add definition here.

    # Turn parity variables.
    P = [[Bool(f"P_{i}_{j}") for j in range(ncol)] for i in range(nrow)] # Add definition here.

    add_constraints(grid, slv, C, H, V, P)

    print('# Encoding time: {0:.4} s'.format(time.process_time() - starttime))

    solve_and_print(grid, slv, C, H, V, P)

    print('# CPU time: {0:.4} s'.format(time.process_time() - starttime))