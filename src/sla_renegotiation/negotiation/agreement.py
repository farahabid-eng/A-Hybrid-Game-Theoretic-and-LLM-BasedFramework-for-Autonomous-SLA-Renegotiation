import re

from sla_renegotiation.domain.models import Proposal

_NEGATION_PATTERN = re.compile(r"\b(not|n't)\b", re.IGNORECASE)
_ACCEPTANCE_PATTERNS = [
    re.compile(r"\bi\s+accept\b", re.IGNORECASE),
    re.compile(r"\bagreed\b", re.IGNORECASE),
    re.compile(r"\bacceptable\b", re.IGNORECASE),
]


def check_agreement(client_proposal: Proposal, provider_proposal: Proposal) -> bool:
    for proposal in (client_proposal, provider_proposal):
        text = proposal.content
        for pattern in _ACCEPTANCE_PATTERNS:
            for match in pattern.finditer(text):
                start = max(0, match.start() - 15)
                prefix = text[start : match.start()]
                if not _NEGATION_PATTERN.search(prefix):
                    return True
    return False
