"""M0 provider-inventory executor.

This module implements the sole concrete M0 executor capability:
``provider_inventory``. It plugs into the frozen ``SingleStepExecutor`` seam
without adding scheduling, routing, model generation, or provider-native
semantics.
"""

from __future__ import annotations

from dataclasses import dataclass

from curios_contracts import (
    ContractError,
    EffectClassification,
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    EvidenceId,
    EvidenceKind,
    EvidenceReference,
    ObjectReference,
    ProviderDescriptor,
    Result,
    ResultStatus,
)
from curios_core import CoreContext, CoreServices, ProviderCatalog
from curios_policy import M0_PROVIDER_INVENTORY_WORK_TYPE

from curios_runtime.single_step_runtime import (
    SingleStepExecutionOutcome,
    SingleStepExecutionRequest,
)

_READ_ONLY_EFFECTS = (EffectClassification.READ_ONLY,)


@dataclass(frozen=True, slots=True)
class ProviderInventoryExecutor:
    """Concrete M0 executor for deterministic provider descriptor inventory."""

    provider_catalogs: tuple[ProviderCatalog, ...] = ()

    def __post_init__(self) -> None:
        catalogs = tuple(self.provider_catalogs)
        for catalog in catalogs:
            if not isinstance(catalog, ProviderCatalog):
                msg = "provider_catalogs must contain ProviderCatalog values"
                raise TypeError(msg)
        object.__setattr__(self, "provider_catalogs", catalogs)

    def execute(self, request: SingleStepExecutionRequest) -> SingleStepExecutionOutcome:
        """Return canonical provider descriptors for one authorized inventory work step."""
        if not isinstance(request, SingleStepExecutionRequest):
            msg = "request must be a SingleStepExecutionRequest"
            raise TypeError(msg)

        capability_error = _capability_error(request)
        if capability_error is not None:
            return SingleStepExecutionOutcome(Result.failure((capability_error,)))

        descriptors: list[ProviderDescriptor] = []
        context = CoreContext(observability=request.observability_context)
        for catalog_index, catalog in enumerate(self.provider_catalogs):
            catalog_result = _list_catalog(catalog, context, request, catalog_index)
            if catalog_result.status is ResultStatus.FAILURE:
                return SingleStepExecutionOutcome(Result.failure(catalog_result.errors))
            assert catalog_result.value is not None
            descriptors.extend(catalog_result.value)

        duplicate_error = _duplicate_provider_error(descriptors, request)
        if duplicate_error is not None:
            return SingleStepExecutionOutcome(Result.failure((duplicate_error,)))

        ordered_descriptors = tuple(sorted(descriptors, key=_descriptor_sort_key))
        evidence = EvidenceReference(
            evidence_id=EvidenceId.generate(),
            kind=EvidenceKind.PROVIDER_REPORT,
            subject_ref=ObjectReference.from_id(request.work.work_id),
            collected_at=request.execution.started_at,
            summary=(
                f"Provider inventory returned {len(ordered_descriptors)} provider descriptor(s)."
            ),
            trace_id=request.observability_context.trace_id,
        )
        return SingleStepExecutionOutcome(
            Result.success(
                {
                    "work_type": M0_PROVIDER_INVENTORY_WORK_TYPE,
                    "provider_count": len(ordered_descriptors),
                    "providers": [
                        descriptor.to_json_compatible() for descriptor in ordered_descriptors
                    ],
                },
                evidence_refs=(evidence,),
            ),
            evidence_refs=(evidence,),
        )


def _list_catalog(
    catalog: ProviderCatalog,
    context: CoreContext,
    request: SingleStepExecutionRequest,
    catalog_index: int,
) -> Result[tuple[ProviderDescriptor, ...]]:
    try:
        result = CoreServices(provider_catalog=catalog).list_provider_descriptors(context)
    except Exception as exc:
        return Result.failure(
            (
                _executor_error(
                    "PROVIDER_INVENTORY_CATALOG_EXCEPTION",
                    "Provider inventory catalog raised an unexpected bounded failure.",
                    category=ErrorCategory.DEPENDENCY,
                    retryable=False,
                    request=request,
                    details={
                        "catalog_index": catalog_index,
                        "cause_type": type(exc).__name__,
                    },
                ),
            )
        )
    if result.status is ResultStatus.FAILURE:
        return Result.failure(
            (
                _executor_error(
                    "PROVIDER_INVENTORY_CATALOG_FAILURE",
                    "Provider inventory catalog returned a bounded failure.",
                    category=ErrorCategory.DEPENDENCY,
                    retryable=any(error.retryable for error in result.errors),
                    request=request,
                    details={
                        "catalog_index": catalog_index,
                        "catalog_error_codes": tuple(
                            str(error.error_code) for error in result.errors
                        ),
                    },
                ),
            )
        )
    if result.value is None:
        return Result.failure(
            (
                _executor_error(
                    "PROVIDER_INVENTORY_MALFORMED_RESULT",
                    "Provider inventory catalog returned no descriptor collection.",
                    category=ErrorCategory.VALIDATION,
                    retryable=False,
                    request=request,
                    details={"catalog_index": catalog_index},
                ),
            )
        )
    descriptors = tuple(result.value)
    for descriptor in descriptors:
        if not isinstance(descriptor, ProviderDescriptor):
            return Result.failure(
                (
                    _executor_error(
                        "PROVIDER_INVENTORY_MALFORMED_RESULT",
                        "Provider inventory catalog returned a non-canonical descriptor.",
                        category=ErrorCategory.VALIDATION,
                        retryable=False,
                        request=request,
                        details={
                            "catalog_index": catalog_index,
                            "descriptor_type": type(descriptor).__name__,
                        },
                    ),
                )
            )
    return Result.success(descriptors)


def _capability_error(request: SingleStepExecutionRequest) -> ContractError | None:
    if request.work.work_type != M0_PROVIDER_INVENTORY_WORK_TYPE:
        return _executor_error(
            "PROVIDER_INVENTORY_UNSUPPORTED_WORK",
            "Provider inventory executor supports only provider_inventory work.",
            category=ErrorCategory.VALIDATION,
            retryable=False,
            request=request,
            details={"work_type": request.work.work_type},
        )
    if tuple(request.policy_decision.requested_effects) != _READ_ONLY_EFFECTS:
        return _executor_error(
            "PROVIDER_INVENTORY_UNSUPPORTED_EFFECT",
            "Provider inventory executor supports only READ_ONLY effects.",
            category=ErrorCategory.AUTHORIZATION,
            retryable=False,
            request=request,
            details={
                "requested_effects": tuple(
                    effect.value for effect in request.policy_decision.requested_effects
                )
            },
        )
    if not request.policy_decision.is_authorizing:
        return _executor_error(
            "PROVIDER_INVENTORY_NOT_AUTHORIZED",
            "Provider inventory executor requires an authorizing policy decision.",
            category=ErrorCategory.AUTHORIZATION,
            retryable=False,
            request=request,
            details={"policy_outcome": request.policy_decision.outcome.value},
        )
    return None


def _duplicate_provider_error(
    descriptors: list[ProviderDescriptor],
    request: SingleStepExecutionRequest,
) -> ContractError | None:
    seen: set[str] = set()
    for descriptor in descriptors:
        provider_id = str(descriptor.provider_id)
        if provider_id in seen:
            return _executor_error(
                "PROVIDER_INVENTORY_DUPLICATE_PROVIDER",
                "Provider inventory contains duplicate provider descriptors.",
                category=ErrorCategory.CONFLICT,
                retryable=False,
                request=request,
                details={"provider_id": provider_id},
            )
        seen.add(provider_id)
    return None


def _descriptor_sort_key(descriptor: ProviderDescriptor) -> tuple[str, str, str]:
    return (
        str(descriptor.provider_id),
        descriptor.provider_type.value,
        str(descriptor.version),
    )


def _executor_error(
    code: str,
    message: str,
    *,
    category: ErrorCategory,
    retryable: bool,
    request: SingleStepExecutionRequest,
    details: dict[str, object] | None = None,
) -> ContractError:
    return ContractError(
        error_code=ErrorCode(code),
        message=message,
        category=category,
        severity=ErrorSeverity.ERROR,
        retryable=retryable,
        subject_ref=ObjectReference.from_id(request.work.work_id),
        trace_id=request.observability_context.trace_id,
        details=details,
    )
