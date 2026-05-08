# Root Compiler

The root compiler turns promoted advisory roots into constructor-family plans.
It does not create certificates.

A constructor plan records:

- root ID and canonical name
- constructor type
- obstruction surface
- route
- source signature
- target-demand signature
- table hashes
- witness schema
- carrier orders
- replay queue
- expected yield score
- verifier requirements

The compiler chooses constructor families such as table reuse, witness schema,
source burst, carrier-order boundary, residual compression, derived
amplification, obstruction boundary, or symbolic closure separator
constructors.

Constructor plans are scheduling pressure for future verified construction.
Their outputs must still be checked by MathGraph’s verifier/importer boundary.
Finite countermodels require source satisfaction and target violation replay.
Formal proof artifacts require their corresponding proof checker.
