"""Configuration, security, effect, and policy contracts for Curios."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Self

from curios_contracts._validation import (
    normalize_details,
    reject_secret_shaped_text,
    validate_safe_text,
    validate_safe_token,
)
from curios_contracts.evidence import EvidenceReference
from curios_contracts.identifiers import EvidenceId
from curios_contracts.observability import ObservabilityContext
from curios_contracts.references import ObjectReference, ReferenceKind
from curios_contracts.schema_version import SchemaVersion
from curios_contracts.serialization import to_json_compatible
from curios_contracts.temporal import UtcTimestamp

_CREDENTIAL_URL_RE = re.compile(r"://[^/\s:@]+(?::[^/\s@]*)?@")


class ConfigurationProfileName(StrEnum):
    """Closed M0 canonical Curios environment-profile vocabulary."""

    LOCAL_DOCKER = "LOCAL_DOCKER"


class PrincipalType(StrEnum):
    """M0 principal categories without authentication or credential semantics."""

    HUMAN = "HUMAN"
    SERVICE = "SERVICE"
    AGENT_INSTANCE = "AGENT_INSTANCE"
    TOOL_EXECUTOR = "TOOL_EXECUTOR"
    PROVIDER = "PROVIDER"
    SYSTEM = "SYSTEM"


class EffectClassification(StrEnum):
    """Canonical M0 effect vocabulary."""

    READ_ONLY = "READ_ONLY"
    LOCAL_WRITE = "LOCAL_WRITE"
    EXTERNAL_READ = "EXTERNAL_READ"
    EXTERNAL_WRITE = "EXTERNAL_WRITE"
    DESTRUCTIVE = "DESTRUCTIVE"
    SECRET_ACCESS = "SECRET_ACCESS"
    NETWORK_ACCESS = "NETWORK_ACCESS"
    EXECUTION = "EXECUTION"


class RiskClassification(StrEnum):
    """Canonical M0 risk vocabulary, separate from effect semantics."""

    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PolicyDecisionOutcome(StrEnum):
    """Canonical policy decision outcomes."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"
    UNKNOWN = "UNKNOWN"


class ApprovalOutcome(StrEnum):
    """Canonical approval record outcomes."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class ConfigurationProfile:
    """Canonical configuration-profile identity, independent of settings loading."""

    profile: ConfigurationProfileName
    schema_version: SchemaVersion = field(default_factory=lambda: SchemaVersion(1, 0, 0))
    description: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile", ConfigurationProfileName(self.profile))
        if not isinstance(self.schema_version, SchemaVersion):
            object.__setattr__(
                self, "schema_version", SchemaVersion.parse(str(self.schema_version))
            )
        if self.description is not None:
            object.__setattr__(
                self,
                "description",
                _validate_public_text(self.description, "description", max_length=512),
            )

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        parsed = _require_mapping(value, "configuration profile JSON")
        _reject_unexpected_keys(parsed, {"profile", "schema_version", "description"})
        return cls(
            profile=ConfigurationProfileName(_require_str(parsed["profile"], "profile")),
            schema_version=SchemaVersion.parse(
                _require_str(parsed.get("schema_version", "1.0.0"), "schema_version")
            ),
            description=(
                _require_str(parsed["description"], "description")
                if parsed.get("description") is not None
                else None
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "profile": self.profile.value,
            "schema_version": to_json_compatible(self.schema_version),
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class SecretReference:
    """Provider-neutral pointer to a secret name/key, never a secret value."""

    name: str
    scope: str
    purpose: str
    key: str | None = None
    resolver_ref: ObjectReference | None = None
    secret_provider_ref: ObjectReference | None = None

    def __post_init__(self) -> None:
        if (self.resolver_ref is None) == (self.secret_provider_ref is None):
            msg = "exactly one of resolver_ref or secret_provider_ref must be provided"
            raise ValueError(msg)
        if self.resolver_ref is not None and not isinstance(self.resolver_ref, ObjectReference):
            msg = "resolver_ref must be an ObjectReference when provided"
            raise TypeError(msg)
        if self.secret_provider_ref is not None:
            _require_reference_kind(
                self.secret_provider_ref,
                ReferenceKind.PROVIDER,
                "secret_provider_ref",
            )
        object.__setattr__(self, "name", _validate_public_text(self.name, "name", max_length=256))
        object.__setattr__(
            self, "scope", _validate_public_text(self.scope, "scope", max_length=256)
        )
        object.__setattr__(
            self,
            "purpose",
            _validate_public_text(self.purpose, "purpose", max_length=512),
        )
        if self.key is not None:
            object.__setattr__(
                self,
                "key",
                _validate_public_text(self.key, "key", max_length=256),
            )

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        parsed = _require_mapping(value, "secret reference JSON")
        _reject_unexpected_keys(
            parsed,
            {"name", "scope", "purpose", "key", "resolver_ref", "secret_provider_ref"},
        )
        return cls(
            name=_require_str(parsed["name"], "name"),
            scope=_require_str(parsed["scope"], "scope"),
            purpose=_require_str(parsed["purpose"], "purpose"),
            key=_require_optional_str(parsed, "key"),
            resolver_ref=_parse_optional_reference(parsed, "resolver_ref"),
            secret_provider_ref=_parse_optional_reference(parsed, "secret_provider_ref"),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "name": self.name,
            "key": self.key,
            "scope": self.scope,
            "purpose": self.purpose,
            "resolver_ref": to_json_compatible(self.resolver_ref),
            "secret_provider_ref": to_json_compatible(self.secret_provider_ref),
        }


@dataclass(frozen=True, slots=True)
class Principal:
    """Canonical actor identity without credentials or authentication state."""

    principal_type: PrincipalType
    identity: str
    principal_ref: ObjectReference | None = None
    related_agent_ref: ObjectReference | None = None
    execution_ref: ObjectReference | None = None

    def __post_init__(self) -> None:
        principal_type = PrincipalType(self.principal_type)
        object.__setattr__(self, "principal_type", principal_type)
        object.__setattr__(
            self,
            "identity",
            _validate_public_text(self.identity, "identity", max_length=256),
        )
        if self.principal_ref is not None and not isinstance(self.principal_ref, ObjectReference):
            msg = "principal_ref must be an ObjectReference when provided"
            raise TypeError(msg)
        if principal_type is PrincipalType.AGENT_INSTANCE and self.principal_ref is not None:
            _require_reference_kind(
                self.principal_ref,
                ReferenceKind.AGENT_INSTANCE,
                "principal_ref",
            )
        if principal_type is PrincipalType.PROVIDER and self.principal_ref is not None:
            _require_reference_kind(self.principal_ref, ReferenceKind.PROVIDER, "principal_ref")
        if self.related_agent_ref is not None:
            _require_reference_kind(
                self.related_agent_ref,
                ReferenceKind.AGENT_INSTANCE,
                "related_agent_ref",
            )
        if self.execution_ref is not None:
            _require_reference_kind(self.execution_ref, ReferenceKind.EXECUTION, "execution_ref")

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        parsed = _require_mapping(value, "principal JSON")
        _reject_unexpected_keys(
            parsed,
            {"principal_type", "identity", "principal_ref", "related_agent_ref", "execution_ref"},
        )
        return cls(
            principal_type=PrincipalType(_require_str(parsed["principal_type"], "principal_type")),
            identity=_require_str(parsed["identity"], "identity"),
            principal_ref=_parse_optional_reference(parsed, "principal_ref"),
            related_agent_ref=_parse_optional_reference(parsed, "related_agent_ref"),
            execution_ref=_parse_optional_reference(parsed, "execution_ref"),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "principal_type": self.principal_type.value,
            "identity": self.identity,
            "principal_ref": to_json_compatible(self.principal_ref),
            "related_agent_ref": to_json_compatible(self.related_agent_ref),
            "execution_ref": to_json_compatible(self.execution_ref),
        }


@dataclass(frozen=True, slots=True)
class Permission:
    """Bounded action/resource/scope/effect permission abstraction."""

    action: str
    resource_type: str
    scope: str
    permitted_effects: tuple[EffectClassification, ...]
    resource_ref: ObjectReference | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "action", validate_safe_token(self.action, "action"))
        object.__setattr__(
            self,
            "resource_type",
            validate_safe_token(self.resource_type, "resource_type"),
        )
        object.__setattr__(
            self, "scope", _validate_public_text(self.scope, "scope", max_length=256)
        )
        object.__setattr__(
            self,
            "permitted_effects",
            _normalize_effects(self.permitted_effects, "permitted_effects"),
        )
        if self.resource_ref is not None and not isinstance(self.resource_ref, ObjectReference):
            msg = "resource_ref must be an ObjectReference when provided"
            raise TypeError(msg)

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        parsed = _require_mapping(value, "permission JSON")
        _reject_unexpected_keys(
            parsed,
            {"action", "resource_type", "scope", "permitted_effects", "resource_ref"},
        )
        return cls(
            action=_require_str(parsed["action"], "action"),
            resource_type=_require_str(parsed["resource_type"], "resource_type"),
            scope=_require_str(parsed["scope"], "scope"),
            permitted_effects=_parse_effect_tuple(parsed["permitted_effects"], "permitted_effects"),
            resource_ref=_parse_optional_reference(parsed, "resource_ref"),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_ref": to_json_compatible(self.resource_ref),
            "scope": self.scope,
            "permitted_effects": to_json_compatible(self.permitted_effects),
        }


@dataclass(frozen=True, slots=True)
class Authority:
    """Explicit bounded authority granted to a principal."""

    authority_id: str
    principal: Principal
    permissions: tuple[Permission, ...]
    scope: str
    granted_at: UtcTimestamp
    expires_at: UtcTimestamp | None = None
    provenance_refs: tuple[EvidenceReference | EvidenceId | ObjectReference, ...] = ()
    approval_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "authority_id",
            _validate_identifier_text(self.authority_id, "authority_id"),
        )
        if not isinstance(self.principal, Principal):
            msg = "principal must be a Principal"
            raise TypeError(msg)
        object.__setattr__(self, "permissions", _normalize_permissions(self.permissions))
        object.__setattr__(
            self, "scope", _validate_public_text(self.scope, "scope", max_length=256)
        )
        object.__setattr__(self, "granted_at", UtcTimestamp(self.granted_at))
        if self.expires_at is not None:
            expires_at = UtcTimestamp(self.expires_at)
            if expires_at.to_datetime() <= self.granted_at.to_datetime():
                msg = "expires_at must be after granted_at"
                raise ValueError(msg)
            object.__setattr__(self, "expires_at", expires_at)
        object.__setattr__(
            self,
            "provenance_refs",
            _normalize_evidence_object_refs(self.provenance_refs, "provenance_refs"),
        )
        if self.approval_id is not None:
            object.__setattr__(
                self,
                "approval_id",
                _validate_identifier_text(self.approval_id, "approval_id"),
            )

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        parsed = _require_mapping(value, "authority JSON")
        _reject_unexpected_keys(
            parsed,
            {
                "authority_id",
                "principal",
                "permissions",
                "scope",
                "granted_at",
                "expires_at",
                "provenance_refs",
                "approval_id",
            },
        )
        return cls(
            authority_id=_require_str(parsed["authority_id"], "authority_id"),
            principal=Principal.from_json_compatible(parsed["principal"]),
            permissions=_parse_permission_tuple(parsed["permissions"]),
            scope=_require_str(parsed["scope"], "scope"),
            granted_at=UtcTimestamp(_require_str(parsed["granted_at"], "granted_at")),
            expires_at=(
                UtcTimestamp(_require_str(parsed["expires_at"], "expires_at"))
                if parsed.get("expires_at") is not None
                else None
            ),
            provenance_refs=_parse_evidence_object_ref_tuple(
                parsed.get("provenance_refs", ()),
                "provenance_refs",
            ),
            approval_id=_require_optional_str(parsed, "approval_id"),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "authority_id": self.authority_id,
            "principal": to_json_compatible(self.principal),
            "permissions": to_json_compatible(self.permissions),
            "scope": self.scope,
            "granted_at": to_json_compatible(self.granted_at),
            "expires_at": to_json_compatible(self.expires_at),
            "provenance_refs": to_json_compatible(self.provenance_refs),
            "approval_id": self.approval_id,
        }


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    """Policy decision record; UNKNOWN remains distinct from DENY."""

    subject_ref: ObjectReference
    principal: Principal
    requested_effects: tuple[EffectClassification, ...]
    resource_refs: tuple[ObjectReference, ...]
    scope: str
    outcome: PolicyDecisionOutcome
    reason: str
    decided_at: UtcTimestamp
    decision_id: str | None = None
    policy_refs: tuple[ObjectReference, ...] = ()
    approval_id: str | None = None
    observability_context: ObservabilityContext | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.subject_ref, ObjectReference):
            msg = "subject_ref must be an ObjectReference"
            raise TypeError(msg)
        if not isinstance(self.principal, Principal):
            msg = "principal must be a Principal"
            raise TypeError(msg)
        object.__setattr__(
            self,
            "requested_effects",
            _normalize_effects(self.requested_effects, "requested_effects"),
        )
        object.__setattr__(
            self,
            "resource_refs",
            _normalize_object_refs(self.resource_refs, "resource_refs"),
        )
        object.__setattr__(
            self, "scope", _validate_public_text(self.scope, "scope", max_length=256)
        )
        object.__setattr__(self, "outcome", PolicyDecisionOutcome(self.outcome))
        object.__setattr__(
            self,
            "reason",
            _validate_public_text(self.reason, "reason", max_length=1024),
        )
        object.__setattr__(self, "decided_at", UtcTimestamp(self.decided_at))
        if self.decision_id is not None:
            object.__setattr__(
                self,
                "decision_id",
                _validate_identifier_text(self.decision_id, "decision_id"),
            )
        object.__setattr__(
            self,
            "policy_refs",
            _normalize_object_refs(self.policy_refs, "policy_refs"),
        )
        if self.approval_id is not None:
            object.__setattr__(
                self,
                "approval_id",
                _validate_identifier_text(self.approval_id, "approval_id"),
            )
        if self.observability_context is not None and not isinstance(
            self.observability_context,
            ObservabilityContext,
        ):
            msg = "observability_context must be an ObservabilityContext when provided"
            raise TypeError(msg)

    @property
    def is_authorizing(self) -> bool:
        """Return whether this decision explicitly authorizes its requested effects."""
        return self.outcome is PolicyDecisionOutcome.ALLOW

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        parsed = _require_mapping(value, "policy decision JSON")
        _reject_unexpected_keys(
            parsed,
            {
                "decision_id",
                "subject_ref",
                "principal",
                "requested_effects",
                "resource_refs",
                "scope",
                "outcome",
                "reason",
                "policy_refs",
                "approval_id",
                "decided_at",
                "observability_context",
            },
        )
        return cls(
            decision_id=_require_optional_str(parsed, "decision_id"),
            subject_ref=ObjectReference.from_json_compatible(parsed["subject_ref"]),
            principal=Principal.from_json_compatible(parsed["principal"]),
            requested_effects=_parse_effect_tuple(parsed["requested_effects"], "requested_effects"),
            resource_refs=_parse_object_ref_tuple(parsed["resource_refs"], "resource_refs"),
            scope=_require_str(parsed["scope"], "scope"),
            outcome=PolicyDecisionOutcome(_require_str(parsed["outcome"], "outcome")),
            reason=_require_str(parsed["reason"], "reason"),
            policy_refs=_parse_object_ref_tuple(parsed.get("policy_refs", ()), "policy_refs"),
            approval_id=_require_optional_str(parsed, "approval_id"),
            decided_at=UtcTimestamp(_require_str(parsed["decided_at"], "decided_at")),
            observability_context=(
                ObservabilityContext.from_json(parsed["observability_context"])
                if parsed.get("observability_context") is not None
                else None
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "decision_id": self.decision_id,
            "subject_ref": to_json_compatible(self.subject_ref),
            "principal": to_json_compatible(self.principal),
            "requested_effects": to_json_compatible(self.requested_effects),
            "resource_refs": to_json_compatible(self.resource_refs),
            "scope": self.scope,
            "outcome": self.outcome.value,
            "reason": self.reason,
            "policy_refs": to_json_compatible(self.policy_refs),
            "approval_id": self.approval_id,
            "decided_at": to_json_compatible(self.decided_at),
            "observability_context": to_json_compatible(self.observability_context),
        }


@dataclass(frozen=True, slots=True)
class Approval:
    """Scoped approval fact that does not imply permanent authority."""

    approval_id: str
    requested_by: Principal
    subject_ref: ObjectReference
    action: str
    requested_effects: tuple[EffectClassification, ...]
    scope: str
    reason: str
    outcome: ApprovalOutcome
    requested_at: UtcTimestamp
    expires_at: UtcTimestamp
    approved_by: Principal | None = None
    rejected_by: Principal | None = None
    decided_at: UtcTimestamp | None = None
    conditions: Mapping[str, object] | None = None
    evidence_refs: tuple[EvidenceReference | EvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "approval_id",
            _validate_identifier_text(self.approval_id, "approval_id"),
        )
        if not isinstance(self.requested_by, Principal):
            msg = "requested_by must be a Principal"
            raise TypeError(msg)
        if not isinstance(self.subject_ref, ObjectReference):
            msg = "subject_ref must be an ObjectReference"
            raise TypeError(msg)
        object.__setattr__(self, "action", validate_safe_token(self.action, "action"))
        object.__setattr__(
            self,
            "requested_effects",
            _normalize_effects(self.requested_effects, "requested_effects"),
        )
        object.__setattr__(
            self, "scope", _validate_public_text(self.scope, "scope", max_length=256)
        )
        object.__setattr__(
            self,
            "reason",
            _validate_public_text(self.reason, "reason", max_length=1024),
        )
        outcome = ApprovalOutcome(self.outcome)
        object.__setattr__(self, "outcome", outcome)
        object.__setattr__(self, "requested_at", UtcTimestamp(self.requested_at))
        expires_at = UtcTimestamp(self.expires_at)
        if expires_at.to_datetime() <= self.requested_at.to_datetime():
            msg = "expires_at must be after requested_at"
            raise ValueError(msg)
        object.__setattr__(self, "expires_at", expires_at)

        if self.approved_by is not None and not isinstance(self.approved_by, Principal):
            msg = "approved_by must be a Principal when provided"
            raise TypeError(msg)
        if self.rejected_by is not None and not isinstance(self.rejected_by, Principal):
            msg = "rejected_by must be a Principal when provided"
            raise TypeError(msg)
        if self.approved_by is not None and self.rejected_by is not None:
            msg = "approval cannot have both approved_by and rejected_by"
            raise ValueError(msg)
        if self.decided_at is not None:
            decided_at = UtcTimestamp(self.decided_at)
            if decided_at.to_datetime() < self.requested_at.to_datetime():
                msg = "decided_at must not be before requested_at"
                raise ValueError(msg)
            object.__setattr__(self, "decided_at", decided_at)

        _validate_approval_actor_state(outcome, self.approved_by, self.rejected_by, self.decided_at)
        object.__setattr__(self, "conditions", normalize_details(self.conditions))
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_evidence_refs(self.evidence_refs, "evidence_refs"),
        )

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        parsed = _require_mapping(value, "approval JSON")
        _reject_unexpected_keys(
            parsed,
            {
                "approval_id",
                "requested_by",
                "approved_by",
                "rejected_by",
                "subject_ref",
                "action",
                "requested_effects",
                "scope",
                "reason",
                "outcome",
                "requested_at",
                "decided_at",
                "expires_at",
                "conditions",
                "evidence_refs",
            },
        )
        return cls(
            approval_id=_require_str(parsed["approval_id"], "approval_id"),
            requested_by=Principal.from_json_compatible(parsed["requested_by"]),
            approved_by=(
                Principal.from_json_compatible(parsed["approved_by"])
                if parsed.get("approved_by") is not None
                else None
            ),
            rejected_by=(
                Principal.from_json_compatible(parsed["rejected_by"])
                if parsed.get("rejected_by") is not None
                else None
            ),
            subject_ref=ObjectReference.from_json_compatible(parsed["subject_ref"]),
            action=_require_str(parsed["action"], "action"),
            requested_effects=_parse_effect_tuple(parsed["requested_effects"], "requested_effects"),
            scope=_require_str(parsed["scope"], "scope"),
            reason=_require_str(parsed["reason"], "reason"),
            outcome=ApprovalOutcome(_require_str(parsed["outcome"], "outcome")),
            requested_at=UtcTimestamp(_require_str(parsed["requested_at"], "requested_at")),
            decided_at=(
                UtcTimestamp(_require_str(parsed["decided_at"], "decided_at"))
                if parsed.get("decided_at") is not None
                else None
            ),
            expires_at=UtcTimestamp(_require_str(parsed["expires_at"], "expires_at")),
            conditions=(
                _require_mapping(parsed["conditions"], "conditions")
                if parsed.get("conditions") is not None
                else None
            ),
            evidence_refs=_parse_evidence_ref_tuple(
                parsed.get("evidence_refs", ()),
                "evidence_refs",
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "approval_id": self.approval_id,
            "requested_by": to_json_compatible(self.requested_by),
            "approved_by": to_json_compatible(self.approved_by),
            "rejected_by": to_json_compatible(self.rejected_by),
            "subject_ref": to_json_compatible(self.subject_ref),
            "action": self.action,
            "requested_effects": to_json_compatible(self.requested_effects),
            "scope": self.scope,
            "reason": self.reason,
            "outcome": self.outcome.value,
            "requested_at": to_json_compatible(self.requested_at),
            "decided_at": to_json_compatible(self.decided_at),
            "expires_at": to_json_compatible(self.expires_at),
            "conditions": to_json_compatible(self.conditions),
            "evidence_refs": to_json_compatible(self.evidence_refs),
        }


def _validate_public_text(value: str, field_name: str, *, max_length: int) -> str:
    normalized = validate_safe_text(value, field_name, max_length=max_length)
    reject_secret_shaped_text(normalized, field_name)
    if _CREDENTIAL_URL_RE.search(normalized) is not None:
        msg = f"{field_name} must not contain credential-bearing URLs"
        raise ValueError(msg)
    return normalized


def _validate_identifier_text(value: str, field_name: str) -> str:
    normalized = validate_safe_text(value, field_name, max_length=128)
    reject_secret_shaped_text(normalized, field_name)
    if _CREDENTIAL_URL_RE.search(normalized) is not None:
        msg = f"{field_name} must not contain credential-bearing URLs"
        raise ValueError(msg)
    return normalized


def _require_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        msg = f"{field_name} must be an object"
        raise TypeError(msg)
    for key in value:
        if not isinstance(key, str):
            msg = f"{field_name} keys must be strings"
            raise TypeError(msg)
    return value


def _reject_unexpected_keys(value: Mapping[str, object], allowed_keys: set[str]) -> None:
    unexpected = set(value) - allowed_keys
    if unexpected:
        msg = f"unexpected field(s): {', '.join(sorted(unexpected))}"
        raise ValueError(msg)


def _require_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    return value


def _require_optional_str(value: Mapping[str, object], field_name: str) -> str | None:
    raw_value = value.get(field_name)
    if raw_value is None:
        return None
    return _require_str(raw_value, field_name)


def _parse_optional_reference(
    value: Mapping[str, object],
    field_name: str,
) -> ObjectReference | None:
    raw_value = value.get(field_name)
    if raw_value is None:
        return None
    return ObjectReference.from_json_compatible(raw_value)


def _require_reference_kind(
    value: object,
    expected_kind: ReferenceKind,
    field_name: str,
) -> None:
    if not isinstance(value, ObjectReference):
        msg = f"{field_name} must be an ObjectReference"
        raise TypeError(msg)
    if value.kind is not expected_kind:
        msg = f"{field_name} must reference {expected_kind.value}"
        raise ValueError(msg)


def _normalize_effects(
    values: Sequence[EffectClassification],
    field_name: str,
) -> tuple[EffectClassification, ...]:
    effects = tuple(EffectClassification(value) for value in values)
    if not effects:
        msg = f"{field_name} must contain at least one effect"
        raise ValueError(msg)
    return effects


def _parse_effect_tuple(value: object, field_name: str) -> tuple[EffectClassification, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        msg = f"{field_name} must be a list"
        raise TypeError(msg)
    return _normalize_effects(
        tuple(EffectClassification(_require_str(item, field_name)) for item in value),
        field_name,
    )


def _normalize_permissions(values: Sequence[Permission]) -> tuple[Permission, ...]:
    permissions = tuple(values)
    if not permissions:
        msg = "permissions must contain at least one permission"
        raise ValueError(msg)
    for permission in permissions:
        if not isinstance(permission, Permission):
            msg = "permissions must contain Permission values"
            raise TypeError(msg)
    return permissions


def _parse_permission_tuple(value: object) -> tuple[Permission, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        msg = "permissions must be a list"
        raise TypeError(msg)
    return tuple(Permission.from_json_compatible(item) for item in value)


def _normalize_object_refs(
    values: Sequence[ObjectReference],
    field_name: str,
) -> tuple[ObjectReference, ...]:
    refs = tuple(values)
    for ref in refs:
        if not isinstance(ref, ObjectReference):
            msg = f"{field_name} must contain ObjectReference values"
            raise TypeError(msg)
    return refs


def _parse_object_ref_tuple(value: object, field_name: str) -> tuple[ObjectReference, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        msg = f"{field_name} must be a list"
        raise TypeError(msg)
    return tuple(ObjectReference.from_json_compatible(item) for item in value)


def _normalize_evidence_refs(
    values: Sequence[EvidenceReference | EvidenceId],
    field_name: str,
) -> tuple[EvidenceReference | EvidenceId, ...]:
    refs = tuple(values)
    for ref in refs:
        if not isinstance(ref, EvidenceReference | EvidenceId):
            msg = f"{field_name} must contain EvidenceReference or EvidenceId values"
            raise TypeError(msg)
    return refs


def _parse_evidence_ref_tuple(
    value: object,
    field_name: str,
) -> tuple[EvidenceReference | EvidenceId, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        msg = f"{field_name} must be a list"
        raise TypeError(msg)
    parsed: list[EvidenceReference | EvidenceId] = []
    for item in value:
        if isinstance(item, str):
            parsed.append(EvidenceId(item))
        else:
            parsed.append(EvidenceReference.from_json_compatible(item))
    return tuple(parsed)


def _normalize_evidence_object_refs(
    values: Sequence[EvidenceReference | EvidenceId | ObjectReference],
    field_name: str,
) -> tuple[EvidenceReference | EvidenceId | ObjectReference, ...]:
    refs = tuple(values)
    for ref in refs:
        if not isinstance(ref, EvidenceReference | EvidenceId | ObjectReference):
            msg = f"{field_name} must contain evidence or object references"
            raise TypeError(msg)
    return refs


def _parse_evidence_object_ref_tuple(
    value: object,
    field_name: str,
) -> tuple[EvidenceReference | EvidenceId | ObjectReference, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        msg = f"{field_name} must be a list"
        raise TypeError(msg)
    parsed: list[EvidenceReference | EvidenceId | ObjectReference] = []
    for item in value:
        if isinstance(item, str):
            parsed.append(EvidenceId(item))
        elif isinstance(item, Mapping) and "evidence_id" in item:
            parsed.append(EvidenceReference.from_json_compatible(item))
        else:
            parsed.append(ObjectReference.from_json_compatible(item))
    return tuple(parsed)


def _validate_approval_actor_state(
    outcome: ApprovalOutcome,
    approved_by: Principal | None,
    rejected_by: Principal | None,
    decided_at: UtcTimestamp | None,
) -> None:
    if outcome is ApprovalOutcome.PENDING:
        if approved_by is not None or rejected_by is not None or decided_at is not None:
            msg = "pending approvals must not include decision actor or decided_at"
            raise ValueError(msg)
        return
    if decided_at is None:
        msg = "resolved approvals must include decided_at"
        raise ValueError(msg)
    if outcome is ApprovalOutcome.APPROVED and approved_by is None:
        msg = "approved approvals must include approved_by"
        raise ValueError(msg)
    if outcome is ApprovalOutcome.REJECTED and rejected_by is None:
        msg = "rejected approvals must include rejected_by"
        raise ValueError(msg)


CONFIGURATION_PROFILE_VALUES: tuple[str, ...] = tuple(
    member.value for member in ConfigurationProfileName
)
PRINCIPAL_TYPE_VALUES: tuple[str, ...] = tuple(member.value for member in PrincipalType)
EFFECT_CLASSIFICATION_VALUES: tuple[str, ...] = tuple(
    member.value for member in EffectClassification
)
GOVERNED_EFFECT_VALUES: tuple[str, ...] = EFFECT_CLASSIFICATION_VALUES
RISK_CLASSIFICATION_VALUES: tuple[str, ...] = tuple(member.value for member in RiskClassification)
POLICY_DECISION_OUTCOME_VALUES: tuple[str, ...] = tuple(
    member.value for member in PolicyDecisionOutcome
)
APPROVAL_OUTCOME_VALUES: tuple[str, ...] = tuple(member.value for member in ApprovalOutcome)
