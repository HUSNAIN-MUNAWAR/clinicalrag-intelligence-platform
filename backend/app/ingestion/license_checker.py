from dataclasses import dataclass

ALLOWED = [
    'cc by',
    'cc-by',
    'cc0',
    'creative commons',
    'public domain',
    'open government licence',
    'open government license',
    'government work',
    'medlineplus',
    'pmc open access',
    'pubmed central open access',
    'openfda',
    'dailyMed'.lower(),
    'cdc',
    'attribution required',
    'nih',
    'nlm',
]

REVIEW_REQUIRED = [
    'cc by-nc',
    'cc-by-nc',
    'non-commercial',
    'noncommercial',
    'cc by-nc-sa',
    'cc by-nc-nd',
    'cc by-nc-sa 3.0 igo',
    'who',
]

DENY = [
    'all rights reserved',
    'copyrighted textbook',
    'textbook',
    'commercial use prohibited',
    'ai use not covered',
    'permission required for ai',
]

@dataclass
class LicenseDecision:
    status:str
    reason:str
    @property
    def allowed(self):
        return self.status == 'allowed'
class LicenseChecker:
    def validate(self, license_text:str|None, source_url:str|None=None):
        text=' '.join([license_text or '', source_url or '']).lower()
        if not text.strip(): return LicenseDecision('unknown','No license metadata supplied; manual review required.')
        if any(x in text for x in DENY): return LicenseDecision('blocked','License appears restricted or copyrighted.')
        if any(x in text for x in REVIEW_REQUIRED): return LicenseDecision('review_required','License can be usable with restrictions; review commercial/AI terms before redistribution.')
        if any(x in text for x in ALLOWED): return LicenseDecision('allowed','Open/public license hint matched allowlist.')
        return LicenseDecision('review_required','Unrecognized license; review before redistribution.')
