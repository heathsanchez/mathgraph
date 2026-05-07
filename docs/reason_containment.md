# Reason Containment

Reason containment is scaffolding for the Reason Atlas.

The intended future shape is:

- True claims: source constraints contain the target demand under a lawful route.
- False claims: the target demand is not contained, and a countermodel separates it.
- Residuals: the failed route becomes a sharper obstruction candidate.

In v16.10, reason-containment records are advisory unless backed by a verified
proof, finite countermodel certificate, or other terminal certificate chain. A
finite search miss remains residual evidence only, never proof.
