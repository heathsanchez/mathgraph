"""Finite countermodel constructors for the compact SAIR solver."""

from __future__ import annotations

try:
    from .finite_magma_core import countermodel_certificate, verify_countermodel_certificate
except ImportError:  # standalone build
    pass


def generated_tables(max_n=4):
    seen = set()

    def add(name, table):
        key = tuple(tuple(row) for row in table)
        if key not in seen:
            seen.add(key)
            yield name, key

    for n in range(1, max_n + 1):
        yield from add("left_projection_%d" % n, [[i for j in range(n)] for i in range(n)])
        yield from add("right_projection_%d" % n, [[j for j in range(n)] for i in range(n)])
        for c in range(n):
            yield from add("constant_%d_%d" % (n, c), [[c for j in range(n)] for i in range(n)])
        yield from add("add_mod_%d" % n, [[(i + j) % n for j in range(n)] for i in range(n)])
        yield from add("sub_mod_%d" % n, [[(i - j) % n for j in range(n)] for i in range(n)])
        yield from add("min_%d" % n, [[min(i, j) for j in range(n)] for i in range(n)])
        yield from add("max_%d" % n, [[max(i, j) for j in range(n)] for i in range(n)])
        yield from add("left_zero_%d" % n, [[0 if i == 0 else j for j in range(n)] for i in range(n)])
        yield from add("right_zero_%d" % n, [[0 if j == 0 else i for j in range(n)] for i in range(n)])
        yield from add("first_nonzero_%d" % n, [[i if i != 0 else j for j in range(n)] for i in range(n)])
        yield from add("second_nonzero_%d" % n, [[j if j != 0 else i for j in range(n)] for i in range(n)])
        if n <= 4:
            for A in range(n):
                for B in range(n):
                    for C in range(n):
                        if A == 0 and B == 0:
                            continue
                        yield from add(
                            "affine_%d_%d_%d_%d" % (n, A, B, C),
                            [[(A * i + B * j + C) % n for j in range(n)] for i in range(n)],
                        )


def prove_false_by_table_search(eq1, eq2, max_n=4):
    for name, table in generated_tables(max_n=max_n):
        cert = countermodel_certificate(eq1, eq2, table)
        if cert and verify_countermodel_certificate(eq1, eq2, cert):
            cert["table_name"] = name
            return {"terminal_form": "FINITE_COUNTERMODEL", "method": "finite_table_search", "certificate": cert}
    return None


def prove_false(eq1, eq2):
    return prove_false_by_table_search(eq1, eq2, max_n=4)

