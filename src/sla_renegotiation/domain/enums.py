from enum import StrEnum


class RenegotiationStatus(StrEnum):
    PENDING = "pending"
    CONTEXT_GATHERING = "context_gathering"
    PROFILING = "profiling"
    ZOPA_CALCULATION = "zopa_calculation"
    NEGOTIATING = "negotiating"
    AGREED = "agreed"
    FAILED = "failed"
    MAX_ROUNDS_REACHED = "max_rounds_reached"
    DEADLOCK = "deadlock"
    ACTIVATED = "activated"
    REJECTED = "rejected"


class EventType(StrEnum):
    LATENCY_VIOLATION = "latency_violation"
    THROUGHPUT_VIOLATION = "throughput_violation"
    AVAILABILITY_VIOLATION = "availability_violation"
    ERROR_RATE_VIOLATION = "error_rate_violation"
    COST_OVERAGE = "cost_overage"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    BUSINESS_REQUIREMENT_CHANGE = "business_requirement_change"

    @property
    def is_low_better(self) -> bool:
        return self in (
            self.LATENCY_VIOLATION,
            self.ERROR_RATE_VIOLATION,
        )


class NegotiationRole(StrEnum):
    CLIENT = "client"
    PROVIDER = "provider"
