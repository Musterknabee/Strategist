# ADR-0032: Operator Pack Claim / Lease Surface

Status: Accepted

We introduce a typed `operator_pack_claim_lease` control-plane read model above handoff and workboard context.
This surface translates handoff acknowledgement into reusable claim and lease semantics so operator-facing pack flows can represent active, pending, and unclaimed lease state through one shared boundary.
