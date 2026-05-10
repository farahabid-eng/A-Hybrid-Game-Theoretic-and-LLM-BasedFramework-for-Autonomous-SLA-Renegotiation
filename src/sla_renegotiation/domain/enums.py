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
    REJECTED = "rejected"


class AdaptationType(StrEnum):
    RELAX = "relax"
    STRICTEN = "stricthen"
    REPLACE = "replace"
    REMOVE = "remove"


class EventType(StrEnum):
    LATENCY_VIOLATION = "latency_violation"
    THROUGHPUT_VIOLATION = "throughput_violation"
    AVAILABILITY_VIOLATION = "availability_violation"
    ERROR_RATE_VIOLATION = "error_rate_violation"
    COST_OVERAGE = "cost_overage"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    BUSINESS_REQUIREMENT_CHANGE = "business_requirement_change"


class NegotiationRole(StrEnum):
    CLIENT = "client"
    PROVIDER = "provider"
