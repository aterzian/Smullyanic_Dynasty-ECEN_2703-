"""Functions to verify Smullyanic Dynasty solutions."""

from typing import Sequence, Optional

def get_neighbors(current: tuple[int,int],
                  C: Sequence[Sequence[bool]]) -> list[tuple[int,int]]:
    """Collect (unshaded) neighbors of current."""
    nrow = len(C)
    ncol = len(C[0])

    i, j = current
    nbors = list()
    if i > 0 and C[i-1][j]:
        nbors.append((i-1,j,))
    if i < nrow-1 and C[i+1][j]:
        nbors.append((i+1,j,))
    if j > 0 and C[i][j-1]:
        nbors.append((i,j-1,))
    if j < ncol-1 and C[i][j+1]:
        nbors.append((i,j+1,))

    return nbors

def knaves_in_domain(i: int, j: int,
                     C: Sequence[Sequence[bool]]) -> int:
    """Count knaves in domain of (i,j)."""
    nrow = len(C)
    ncol = len(C[0])
    knaves = 0 if C[i][j] else 1

    if i > 0:
        knaves += 0 if C[i-1][j] else 1
        if j > 0:
            knaves += 0 if C[i-1][j-1] else 1
        if j < ncol-1:
            knaves += 0 if C[i-1][j+1] else 1
    if i < nrow-1:
        knaves += 0 if C[i+1][j] else 1
        if j > 0:
            knaves += 0 if C[i+1][j-1] else 1
        if j < ncol-1:
            knaves += 0 if C[i+1][j+1] else 1
    if j > 0:
        knaves += 0 if C[i][j-1] else 1
    if j < ncol-1:
        knaves += 0 if C[i][j+1] else 1

    return knaves


def verify(grid: Sequence[Sequence[Optional[int]]],
           C: Sequence[Sequence[bool]],
           allow_weak: bool = False) -> None:
    """Verify solution to Smullyanic Dynasty puzzle."""
    nrow = len(grid)
    ncol = len(grid[0])

    # Shaded cells may not share an edge.
    for i in range(nrow):
        for j in range(ncol):
            if j > 0:
                if not C[i][j] and not C[i][j-1]:
                    raise ValueError(f'adjacent shaded cells at ({i},{j-1})')
            if i > 0:
                if not C[i][j] and not C[i-1][j]:
                    raise ValueError(f'adjacent shaded cells at ({i-1},{j})')


    # Unshaded clues count knaves in their square's domain.
    # Shaded clues do not count knaves in their square's domain.
    for i in range(nrow):
        for j in range(ncol):
            clue = grid[i][j]
            if clue is not None:
                knaves = knaves_in_domain(i,j,C)
                if C[i][j] and clue != knaves:
                    raise ValueError(f'unshaded {clue} at ({i},{j}) with {knaves} knaves in its domain')
                elif not C[i][j] and clue == knaves:
                    raise ValueError(f'shaded {clue} at ({i},{j}) with {knaves} knaves in its domain')

    # If both C[0][0] and C[0][1] are unshaded, it doesn't matter
    # which one we choose as root.
    if C[0][0]:
        root = (0,0)
    elif C[0][1]:
        root = (0,1)
    else:
        raise ValueError('the first two cells of the first row are both shaded')

    # Count unshaded cells in the whole grid.
    totalcount = 0
    for i in range(nrow):
        count = sum([C[i][j] for j in range(ncol)])
        totalcount += count

    # Check reachability of all unshaded cells from chosen root.
    if not allow_weak:
        reached = set()
        work = {root}

        while len(work) > 0:
            current = work.pop()
            reached.add(current)
            for cell in get_neighbors(current, C):
                if cell not in reached:
                    work.add(cell)

        if len(reached) != totalcount:
            raise ValueError(f'reached {len(reached)} cells instead of {totalcount}')
