from sla_renegotiation.domain.enums import EventType
from sla_renegotiation.domain.models import SLATemplate, SLODefinition

# ---------------------------------------------------------------------------
# Predefined SLA Templates
# Each entry maps violations (EventType) to their SLO target values.
# ---------------------------------------------------------------------------

PREDEFINED_SLAS: dict[str, SLATemplate] = {
    "basic-api": SLATemplate(
        id="basic-api",
        name="Basic API Service",
        description="Standard SLA for REST API services with typical latency, availability, and throughput guarantees.",
        slos=[
            SLODefinition(
                metric="latency",
                target_value=200,
                unit="ms",
                description="P95 response time under normal load",
                event_type=EventType.LATENCY_VIOLATION,
            ),
            SLODefinition(
                metric="availability",
                target_value=99.9,
                unit="%",
                description="Service uptime percentage per month",
                event_type=EventType.AVAILABILITY_VIOLATION,
            ),
            SLODefinition(
                metric="throughput",
                target_value=1000,
                unit="req/s",
                description="Maximum sustained request throughput",
                event_type=EventType.THROUGHPUT_VIOLATION,
            ),
            SLODefinition(
                metric="error_rate",
                target_value=1.0,
                unit="%",
                description="Maximum acceptable error rate",
                event_type=EventType.ERROR_RATE_VIOLATION,
            ),
        ],
    ),
    "premium-db": SLATemplate(
        id="premium-db",
        name="Premium Database Service",
        description="High-performance SLA for managed database instances with strict latency and availability guarantees.",
        slos=[
            SLODefinition(
                metric="latency",
                target_value=50,
                unit="ms",
                description="P99 query response time",
                event_type=EventType.LATENCY_VIOLATION,
            ),
            SLODefinition(
                metric="availability",
                target_value=99.99,
                unit="%",
                description="Monthly uptime guarantee for database cluster",
                event_type=EventType.AVAILABILITY_VIOLATION,
            ),
            SLODefinition(
                metric="throughput",
                target_value=5000,
                unit="qps",
                description="Maximum sustained queries per second",
                event_type=EventType.THROUGHPUT_VIOLATION,
            ),
            SLODefinition(
                metric="error_rate",
                target_value=0.1,
                unit="%",
                description="Maximum query error rate",
                event_type=EventType.ERROR_RATE_VIOLATION,
            ),
        ],
    ),
    "standard-hosting": SLATemplate(
        id="standard-hosting",
        name="Standard Web Hosting",
        description="Shared hosting SLA with modest performance targets suitable for small to medium websites.",
        slos=[
            SLODefinition(
                metric="latency",
                target_value=500,
                unit="ms",
                description="Average page load time",
                event_type=EventType.LATENCY_VIOLATION,
            ),
            SLODefinition(
                metric="availability",
                target_value=99.5,
                unit="%",
                description="Monthly service availability",
                event_type=EventType.AVAILABILITY_VIOLATION,
            ),
            SLODefinition(
                metric="throughput",
                target_value=100,
                unit="req/s",
                description="Sustained request throughput",
                event_type=EventType.THROUGHPUT_VIOLATION,
            ),
        ],
    ),
    "cdn-streaming": SLATemplate(
        id="cdn-streaming",
        name="CDN & Media Streaming",
        description="Content delivery network SLA optimized for low-latency media delivery and high throughput at the edge.",
        slos=[
            SLODefinition(
                metric="latency",
                target_value=100,
                unit="ms",
                description="P95 time-to-first-byte at edge locations",
                event_type=EventType.LATENCY_VIOLATION,
            ),
            SLODefinition(
                metric="availability",
                target_value=99.95,
                unit="%",
                description="Global edge node availability",
                event_type=EventType.AVAILABILITY_VIOLATION,
            ),
            SLODefinition(
                metric="throughput",
                target_value=10000,
                unit="Mbps",
                description="Sustained edge egress throughput per region",
                event_type=EventType.THROUGHPUT_VIOLATION,
            ),
            SLODefinition(
                metric="error_rate",
                target_value=0.5,
                unit="%",
                description="Cache miss / origin fetch error rate",
                event_type=EventType.ERROR_RATE_VIOLATION,
            ),
        ],
    ),
    "enterprise-saas": SLATemplate(
        id="enterprise-saas",
        name="Enterprise SaaS Platform",
        description="Multi-tenant SaaS platform with guaranteed uptime, response times, and cost controls for enterprise customers.",
        slos=[
            SLODefinition(
                metric="latency",
                target_value=300,
                unit="ms",
                description="P95 API response time for critical endpoints",
                event_type=EventType.LATENCY_VIOLATION,
            ),
            SLODefinition(
                metric="availability",
                target_value=99.95,
                unit="%",
                description="Monthly platform uptime (all regions)",
                event_type=EventType.AVAILABILITY_VIOLATION,
            ),
            SLODefinition(
                metric="throughput",
                target_value=2000,
                unit="req/s",
                description="Sustained API request throughput per tenant",
                event_type=EventType.THROUGHPUT_VIOLATION,
            ),
            SLODefinition(
                metric="error_rate",
                target_value=0.5,
                unit="%",
                description="API 5xx error rate",
                event_type=EventType.ERROR_RATE_VIOLATION,
            ),
            SLODefinition(
                metric="cost",
                target_value=1.15,
                unit="x",
                description="Maximum cost overage multiplier vs committed spend",
                event_type=EventType.COST_OVERAGE,
            ),
        ],
    ),
    "managed-kubernetes": SLATemplate(
        id="managed-kubernetes",
        name="Managed Kubernetes Service",
        description="SLA for managed Kubernetes clusters including control plane availability, node scaling, and resource guarantees.",
        slos=[
            SLODefinition(
                metric="latency",
                target_value=100,
                unit="ms",
                description="API server response latency P99",
                event_type=EventType.LATENCY_VIOLATION,
            ),
            SLODefinition(
                metric="availability",
                target_value=99.95,
                unit="%",
                description="Control plane availability per cluster",
                event_type=EventType.AVAILABILITY_VIOLATION,
            ),
            SLODefinition(
                metric="throughput",
                target_value=500,
                unit="pods/min",
                description="Node auto-scaling throughput",
                event_type=EventType.THROUGHPUT_VIOLATION,
            ),
            SLODefinition(
                metric="resource_health",
                target_value=90,
                unit="%",
                description="Minimum guaranteed node health percentage per cluster",
                event_type=EventType.RESOURCE_EXHAUSTION,
            ),
            SLODefinition(
                metric="error_rate",
                target_value=0.1,
                unit="%",
                description="Control plane API error rate",
                event_type=EventType.ERROR_RATE_VIOLATION,
            ),
        ],
    ),
    "fintech-api": SLATemplate(
        id="fintech-api",
        name="Financial Services API",
        description="Strict SLA for payment processing and financial data APIs with sub-millisecond latency and five-nines availability targets.",
        slos=[
            SLODefinition(
                metric="latency",
                target_value=20,
                unit="ms",
                description="P99 payment transaction processing latency",
                event_type=EventType.LATENCY_VIOLATION,
            ),
            SLODefinition(
                metric="availability",
                target_value=99.999,
                unit="%",
                description="Payment gateway monthly availability",
                event_type=EventType.AVAILABILITY_VIOLATION,
            ),
            SLODefinition(
                metric="throughput",
                target_value=10000,
                unit="tps",
                description="Sustained transactions per second",
                event_type=EventType.THROUGHPUT_VIOLATION,
            ),
            SLODefinition(
                metric="error_rate",
                target_value=0.01,
                unit="%",
                description="Payment processing error rate",
                event_type=EventType.ERROR_RATE_VIOLATION,
            ),
            SLODefinition(
                metric="cost",
                target_value=1.05,
                unit="x",
                description="Maximum cost overage vs committed transaction volume pricing",
                event_type=EventType.COST_OVERAGE,
            ),
        ],
    ),
}


def get_all_slas() -> list[SLATemplate]:
    return list(PREDEFINED_SLAS.values())


def get_sla(sla_id: str) -> SLATemplate | None:
    return PREDEFINED_SLAS.get(sla_id)
