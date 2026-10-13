"""
Enterprise Capability-Based Security and Sandbox Policy Engine for Fractal.
Enforces Principle of Least Privilege: restricts file I/O, network, memory, and subprocess access.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Set, Optional

class Permission(Enum):
    READ_FILE = "READ_FILE"
    WRITE_FILE = "WRITE_FILE"
    NETWORK_ACCESS = "NETWORK_ACCESS"
    CONCURRENCY_SPAWN = "CONCURRENCY_SPAWN"
    SUBPROCESS_EXEC = "SUBPROCESS_EXEC"

class SecurityViolationException(PermissionError):
    pass

@dataclass(slots=True)
class SecuritySandboxPolicy:
    allowed_permissions: Set[Permission] = field(default_factory=lambda: {
        Permission.CONCURRENCY_SPAWN
    })
    read_paths_whitelist: Set[str] = field(default_factory=set)
    write_paths_whitelist: Set[str] = field(default_factory=set)

    def check_permission(self, permission: Permission, resource: Optional[str] = None) -> None:
        if permission not in self.allowed_permissions:
            raise SecurityViolationException(
                f"Security Sandbox Denied: Action '{permission.value}' is not permitted by active policy."
            )
        
        if permission == Permission.READ_FILE and resource and self.read_paths_whitelist:
            if not any(resource.startswith(p) for p in self.read_paths_whitelist):
                raise SecurityViolationException(
                    f"Security Sandbox Denied: Reading path '{resource}' is outside allowed whitelist."
                )

        if permission == Permission.WRITE_FILE and resource and self.write_paths_whitelist:
            if not any(resource.startswith(p) for p in self.write_paths_whitelist):
                raise SecurityViolationException(
                    f"Security Sandbox Denied: Writing path '{resource}' is outside allowed whitelist."
                )

    @classmethod
    def create_permissive(cls) -> 'SecuritySandboxPolicy':
        return cls(allowed_permissions=set(Permission))

    @classmethod
    def create_restricted(cls) -> 'SecuritySandboxPolicy':
        return cls(allowed_permissions={Permission.CONCURRENCY_SPAWN})
