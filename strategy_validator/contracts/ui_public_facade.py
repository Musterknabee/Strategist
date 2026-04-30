from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

UiPublicFacadeRouteKind = Literal['read', 'mutation', 'metadata', 'export']


@dataclass(frozen=True)
class UiPublicFacadeRoute:
    method: str
    path: str
    kind: UiPublicFacadeRouteKind
    auth_required: bool
    payload_schema: str

    def to_payload(self) -> dict[str, object]:
        return {
            'method': self.method,
            'path': self.path,
            'kind': self.kind,
            'auth_required': self.auth_required,
            'payload_schema': self.payload_schema,
        }


@dataclass(frozen=True)
class UiPublicFacadeInventory:
    schema_version: str
    surface: str
    frontend_expected_package: str
    frontend_package_present: bool
    frontend_status: str
    frontend_readiness_claimed: bool
    read_plane_only: bool
    mutation_route: str
    routes: tuple[UiPublicFacadeRoute, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            'schema_version': self.schema_version,
            'surface': self.surface,
            'frontend_expected_package': self.frontend_expected_package,
            'frontend_package_present': self.frontend_package_present,
            'frontend_status': self.frontend_status,
            'frontend_readiness_claimed': self.frontend_readiness_claimed,
            'read_plane_only': self.read_plane_only,
            'mutation_route': self.mutation_route,
            'routes': [route.to_payload() for route in self.routes],
        }


__all__ = [
    'UiPublicFacadeInventory',
    'UiPublicFacadeRoute',
    'UiPublicFacadeRouteKind',
]
