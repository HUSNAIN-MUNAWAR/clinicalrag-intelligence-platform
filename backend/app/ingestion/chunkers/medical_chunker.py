from dataclasses import dataclass
import re
from app.ingestion.metadata import detect_section

@dataclass
class ParentChunk:
    local_id: str
    text: str
    section: str
    start_char: int
    end_char: int

@dataclass
class ChildChunk:
    text: str
    section: str
    start_char: int
    end_char: int
    parent_local_id: str

@dataclass
class ChunkResult:
    parents: list[ParentChunk]
    children: list[ChildChunk]

class MedicalSectionDetector:
    heading_pattern = re.compile(r'^(#{1,4}\s*)?([A-Z][A-Za-z0-9 ,/&\\-]{2,80}:?)$', re.MULTILINE)
    def split_sections(self, text: str):
        matches = list(self.heading_pattern.finditer(text or ''))
        if not matches:
            return [('body', text or '', 0, len(text or ''))]
        out = []
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i+1].start() if i+1 < len(matches) else len(text)
            body = text[start:end].strip()
            if body:
                out.append((detect_section(m.group(2)), body, start, end))
        return out or [('body', text, 0, len(text))]

class MedicalChunker:
    def __init__(self, chunk_size=900, overlap=160):
        self.chunk_size = int(chunk_size)
        self.overlap = min(int(overlap), max(0, self.chunk_size // 2))
        self.detector = MedicalSectionDetector()
    def chunk(self, text: str, document_id: str | None = None) -> ChunkResult:
        parents: list[ParentChunk] = []
        children: list[ChildChunk] = []
        idx = 0
        for section, body, start, end in self.detector.split_sections(text):
            idx += 1
            pid = f'parent-{idx}'
            parents.append(ParentChunk(pid, body[:6000], section, start, end))
            if len(body) <= self.chunk_size:
                children.append(ChildChunk(body, section, start, end, pid))
                continue
            step = max(1, self.chunk_size - self.overlap)
            loc = 0
            while loc < len(body):
                ct = body[loc:loc+self.chunk_size].strip()
                if ct:
                    children.append(ChildChunk(ct, section, start+loc, start+loc+len(ct), pid))
                loc += step
        return ChunkResult(parents, children)

MedicalAwareChunker = MedicalChunker
