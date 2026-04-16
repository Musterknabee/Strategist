# ADR-0085: Chronic Exit Return-Authorization Bridge

## Status
Accepted

## Context
Chronic exit certification proves an item may safely rejoin the return path, but certification alone is not the same as reconnecting the item to the existing return-authorization flow.

## Decision
Introduce `oracle_operator_chronic_exit_return_bridge/v1` as the typed bridge surface from chronic-exit certification into the normal return-authorization path. The bridge must distinguish standard rejoin, monitored rejoin, and held chronic exits.

## Consequences
Certified chronic work no longer terminates in isolation. It reconnects to the existing return-path machinery under an explicit, inspectable bridge artifact.
