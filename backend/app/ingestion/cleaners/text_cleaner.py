import re
class TextCleaner:
    def clean(self,text:str)->str:
        text=text.replace('\x00',' '); text=re.sub(r'\r\n?','\n',text); text=re.sub(r'[ \t]+',' ',text); text=re.sub(r'\n{3,}','\n\n',text); return text.strip()
