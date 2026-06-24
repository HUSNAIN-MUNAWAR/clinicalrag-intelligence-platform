import re
from dataclasses import dataclass
from app.safety.rules import RULES, SafetyRule

@dataclass
class SafetyDecision:
    allowed: bool
    category: str | None = None
    severity: str = 'low'
    reason: str | None = None
    matched_patterns: list[str] | None = None

class MedicalSafetyClassifier:
    """Deterministic safety classifier for portfolio demo.

    This is deliberately conservative and explainable. In production, this could be
    augmented with a policy LLM classifier, but hard rules remain the source of truth.
    """
    def check(self, text: str) -> SafetyDecision:
        q = (text or '').lower()
        matched: list[tuple[SafetyRule, str]] = []
        for rule in RULES:
            for pat in rule.patterns:
                if re.search(r'\b' + re.escape(pat.lower()) + r'\b', q) or pat.lower() in q:
                    matched.append((rule, pat))
        if not matched:
            return SafetyDecision(True, matched_patterns=[])
        # critical/high wins over medium
        order = {'critical': 3, 'high': 2, 'medium': 1, 'low': 0}
        rule, _ = sorted(matched, key=lambda x: order.get(x[0].severity,0), reverse=True)[0]
        return SafetyDecision(
            allowed=False,
            category=rule.id,
            severity=rule.severity,
            reason=rule.refusal_reason,
            matched_patterns=[p for r,p in matched if r.id == rule.id],
        )
