"""Visualization functions for Smullyanic Dynasty puzzle solver."""

from typing import Optional, Sequence
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, PathPatch
from matplotlib.path import Path

def render(i: int, j: int, grid: Sequence[Sequence[Optional[int]]],
           Cbool: Optional[Sequence[Sequence[bool]]]) -> str:
    """Choose Unicode character for grid position."""
    clue = grid[i][j]
    if clue is None:
        if Cbool is None or Cbool[i][j]:
            return '\u00b7' # raised dot
        else:
            return '\u25cf' # black disk
    else:
        if Cbool is None or Cbool[i][j]:
            return str(clue)
        else:
            # Since dingbats didn't have the 0 on black disc,
            # the Unicode character for it is not contiguous to
            # the other digits on black discs.
            if clue == 0:
                return '\u24ff'
            else:
                return chr(0x2789+clue)

def print_ascii(grid: Sequence[Sequence[Optional[int]]],
                Cbool: Optional[Sequence[Sequence[bool]]] = None) -> None:
    """Print grid."""
    N = len(grid)
    M = len(grid[0])
    for i in range(N):
        print(' '.join([render(i, j, grid, Cbool) for j in range(M)]))

def print_matplotlib(grid: Sequence[Sequence[Optional[int]]],
                     C: Optional[Sequence[Sequence[bool]]] = None,
                     E: Optional[Sequence[Sequence[str]]] = None,
                     P: Optional[Sequence[Sequence[bool]]] = None,
                     fontsize: int = 24) -> None:
    """Create matplotlib plot of the grid."""
    nrow = len(grid)
    ncol = len(grid[0])
    fig, ax = plt.subplots(figsize=(ncol,nrow))

    # Draw clues.
    for i in range(nrow):
        for j in range(ncol):
            if C is None:
                textcolor = 'black'
                fillcolor = 'white'
            elif C[i][j]:
                textcolor = 'black'
                fillcolor = 'palegreen'             
            else:
                textcolor = 'white'
                fillcolor = 'blue'
            rect = Rectangle((j,nrow-i-1),1,1, color=fillcolor)
            ax.add_patch(rect)
            clue = grid[i][j]
            if clue is not None:
                _ = ax.annotate(str(clue), xy=(j+1/2,nrow-i-1/2),
                                color=textcolor, fontsize=fontsize,
                                ha='center', va='center')

    # Draw grid lines.
    for i in range(nrow+1):
        path = Path([(0,i), (ncol,i)], [Path.MOVETO, Path.LINETO])
        patch = PathPatch(path, facecolor='black', lw=0.75)
        ax.add_patch(patch)

    for j in range(ncol+1):
        path = Path([(j,0), (j,nrow)], [Path.MOVETO, Path.LINETO])
        patch = PathPatch(path, facecolor='black', lw=0.75)
        ax.add_patch(patch)

    # Draw spanning tree.
    if C is not None and E is not None and P is not None:
        for i in range(nrow):
            for j in range(ncol):
                if C[i][j]:
                    arrowcolor = 'purple' if P[i][j] else 'teal'
                    if E[i][j] == '^':
                        hi, hj = 0.6, 0.0
                        ax.arrow(j+0.5, nrow-i-0.3, hj, hi, width=0.08,
                                 length_includes_head=True, head_width=0.16,
                                 color=arrowcolor)
                    elif E[i][j] == 'v':
                        hi, hj = -0.6, 0.0
                        ax.arrow(j+0.5, nrow-i-0.7, hj, hi, width=0.08,
                                 length_includes_head=True, head_width=0.16,
                                 color=arrowcolor)
                    elif E[i][j] == '>':
                        hi, hj = 0.0, 0.6
                        ax.arrow(j+0.7, nrow-i-0.5, hj, hi, width=0.08,
                                 length_includes_head=True, head_width=0.16,
                                 color=arrowcolor)
                    elif E[i][j] == '<':
                        hi, hj = 0.0, -0.6
                        ax.arrow(j+0.3, nrow-i-0.5, hj, hi, width=0.08,
                                 length_includes_head=True, head_width=0.16,
                                 color=arrowcolor)

    ax.set_xlim(-0.1,ncol+0.1)
    ax.set_ylim(-0.1,nrow+0.1)
    ax.set_aspect('equal','box')
    ax.set_axis_off()
    plt.show()

if __name__ == '__main__':

    from smullinputs import get_grid, check_grid, parse_command

    args = parse_command()

    try:
        grid = get_grid(args.puzzle)
        check_grid(grid)
    except Exception as err:
        raise SystemExit(err)

    if args.matplotlib:
        print_matplotlib(grid, C=None, fontsize=args.fontsize)
    else:
        print_ascii(grid)
