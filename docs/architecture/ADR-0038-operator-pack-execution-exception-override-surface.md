# ADR-0038: Operator pack execution exception / override surface

Status: Accepted

We add a typed control-plane read model that sits above dispatch outcome plus lease governance and classifies operator-pack execution into three reusable override paths: `NO_OVERRIDE_REQUIRED`, `EXCEPTION_ELIGIBLE`, and `OVERRIDE_NEEDED`. This turns blocked and held execution into a reusable override/exception surface that downstream operator tooling can consume without reinterpreting raw block reasons.
