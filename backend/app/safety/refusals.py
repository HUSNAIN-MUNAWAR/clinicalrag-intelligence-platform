from app.safety.classifier import SafetyDecision

EMERGENCY_LINE = 'If this may be an emergency, contact local emergency services immediately.'

def safe_refusal(question: str, decision: SafetyDecision) -> str:
    base = (
        'I cannot provide diagnosis, emergency triage, prescription, dosage, or personalized medical advice. '
        'This platform is for educational and research-focused medical knowledge retrieval only.'
    )
    if decision.category == 'emergency':
        return base + ' ' + EMERGENCY_LINE + ' You can ask for general educational information about a condition once urgent care needs are addressed.'
    return base + ' Please contact a qualified healthcare professional for personal medical decisions. I can still provide general, citation-grounded educational information.'
