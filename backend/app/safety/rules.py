from dataclasses import dataclass

@dataclass(frozen=True)
class SafetyRule:
    id: str
    label: str
    severity: str
    patterns: list[str]
    refusal_reason: str

RULES: list[SafetyRule] = [
    SafetyRule('emergency','Emergency or urgent symptoms','critical',[
        'chest pain','can\'t breathe','cannot breathe','stroke','seizure','suicide','overdose','unconscious','bleeding heavily','severe allergic','anaphylaxis','heart attack','should i go to hospital','er now','emergency room'
    ],'Emergency or urgent medical situations require immediate professional care.'),
    SafetyRule('diagnosis','Personalized diagnosis request','high',[
        'diagnose me','what disease do i have','do i have','am i having','my symptoms are','i have symptoms','what is wrong with me','interpret my symptoms'
    ],'The system cannot provide personalized diagnosis.'),
    SafetyRule('treatment','Personalized treatment request','high',[
        'how should i treat','what should i take','cure my','my treatment','treat me','home remedy for me','should i stop taking','should i start taking'
    ],'The system cannot provide personalized treatment advice.'),
    SafetyRule('prescription','Prescription or dosage advice','high',[
        'dose','dosage','mg should i','prescribe','prescription','how many tablets','how much medicine','increase my medication','decrease my medication'
    ],'The system cannot provide prescription or dosage advice.'),
    SafetyRule('drug_interaction','Patient-specific drug interaction','high',[
        'can i take','safe for me with','interaction with my','i take warfarin','i take insulin','combine these medicines'
    ],'The system cannot assess patient-specific drug interactions.'),
    SafetyRule('lab_result','Personal lab interpretation','high',[
        'my lab result','my blood test','my xray','my mri','my ct scan','my report says','interpret this lab'
    ],'The system cannot interpret personal lab or imaging results.'),
    SafetyRule('phi_upload','Private patient record upload','high',[
        'patient record','medical record','ehr note','real patient','patient name','mrn','cnic','date of birth'
    ],'Do not upload private patient data or personally identifiable health information.'),
    SafetyRule('citation_bypass','Citation bypass or fake source request','medium',[
        'ignore citations','without sources','invent sources','make up references','no evidence needed','fake citation'
    ],'The system must ground every answer in retrieved sources and cannot invent citations.'),
]

def public_rules() -> list[dict]:
    return [{'id':r.id,'label':r.label,'severity':r.severity,'patterns':r.patterns,'refusal_reason':r.refusal_reason} for r in RULES]
