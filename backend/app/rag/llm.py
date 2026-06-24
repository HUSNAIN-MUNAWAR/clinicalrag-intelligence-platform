import httpx
from app.core.config import settings
SYSTEM='You are ClinicalRAG. Use only provided evidence. Refuse diagnosis, dosage, prescription, emergency, and personal medical advice. Include citation IDs.'
class LLMClient:
    def model_name(self): return settings.openai_compatible_model if settings.llm_provider=='openai_compatible' else (settings.ollama_model if settings.llm_provider=='ollama' else 'retrieval-only-extractive')
    async def generate(self,question,evidence):
        if settings.llm_provider=='openai_compatible' and settings.openai_compatible_base_url and settings.openai_compatible_api_key:
            payload={'model':settings.openai_compatible_model,'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':f'Question: {question}\nEvidence:\n{evidence}'}],'temperature':0}
            async with httpx.AsyncClient(timeout=45) as c:
                r=await c.post(settings.openai_compatible_base_url.rstrip('/')+'/chat/completions',json=payload,headers={'Authorization':f'Bearer {settings.openai_compatible_api_key}'}); r.raise_for_status(); return r.json()['choices'][0]['message']['content']
        if settings.llm_provider=='ollama':
            async with httpx.AsyncClient(timeout=90) as c:
                r=await c.post(settings.ollama_base_url.rstrip('/')+'/api/generate',json={'model':settings.ollama_model,'prompt':SYSTEM+'\n'+evidence,'stream':False}); r.raise_for_status(); return r.json().get('response','')
        return None
class ExtractiveAnswerer:
    def answer(self,question,retrieved,evidence):
        if not retrieved: return 'I could not find enough indexed evidence to answer with citations. Please ingest open medical sources first.'
        parts=[]
        for i,item in enumerate(retrieved[:3],1):
            txt=' '.join(item.get('text','').split()); sent=next((p.strip()+'.' for p in txt.split('. ') if len(p.strip())>40), txt[:260])
            parts.append(f'{sent} [S{i}]')
        return 'Based on the retrieved educational sources, '+' '.join(parts)+' This is educational only and not medical advice.'

class LLMProvider:
    """Synchronous provider facade used by API services.

    Default mode is retrieval-only extractive generation so the project can run
    locally without paid API keys. OpenAI-compatible/Ollama async hooks are kept
    in LLMClient for extension.
    """
    def __init__(self):
        self.model_name = LLMClient().model_name()
        self.extractive = ExtractiveAnswerer()
    def generate_grounded_answer(self, question: str, retrieved: list[dict], citations: list) -> str:
        if not retrieved:
            return 'I could not find enough indexed evidence to answer with citations. Please ingest open medical sources first.'
        # Retrieval-only deterministic answer. It quotes/condenses retrieved evidence and always cites IDs.
        parts=[]
        for i,item in enumerate(retrieved[:3],1):
            txt=' '.join((item.get('text') or '').split())
            sentence=next((p.strip() for p in txt.split('. ') if len(p.strip())>45), txt[:240])
            parts.append(f'{sentence} [C{i}]')
        return 'Based only on the retrieved educational sources: ' + ' '.join(parts) + ' This is educational information only, not diagnosis, prescription, dosage, or personalized medical advice.'
