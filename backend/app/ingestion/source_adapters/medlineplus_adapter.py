import re
import shutil
import urllib.parse
import urllib.request
import zipfile
from app.ingestion.source_adapters.base import SourceAdapter, SourceDownloadResult

class MedlinePlusAdapter(SourceAdapter):
    id='medlineplus'; name='MedlinePlus Health Topic XML'; url='https://medlineplus.gov/xml.html'

    def download(self,target_dir,limit=1):
        target_dir.mkdir(parents=True, exist_ok=True)
        source_url = self.url
        if source_url.endswith('.html'):
            page = urllib.request.urlopen(source_url, timeout=90).read().decode('utf-8', errors='ignore')
            matches = re.findall(r'href="([^"]*mplus_topics_[0-9-]+\.zip)"', page)
            if not matches:
                matches = re.findall(r'href="([^"]*mplus_topics_[0-9-]+\.xml)"', page)
            if not matches:
                raise RuntimeError('Could not locate MedlinePlus health-topic XML link.')
            source_url = urllib.parse.urljoin(source_url, matches[0])
        out = target_dir/'medlineplus_health_topics.xml'
        if source_url.lower().endswith('.zip'):
            downloaded = target_dir / urllib.parse.urlparse(source_url).path.split('/')[-1]
            urllib.request.urlretrieve(source_url, downloaded)
            with zipfile.ZipFile(downloaded) as archive:
                xml_names = [x for x in archive.namelist() if x.lower().endswith('.xml')]
                if not xml_names:
                    raise RuntimeError('MedlinePlus archive did not contain XML.')
                with archive.open(xml_names[0]) as src, out.open('wb') as dst:
                    shutil.copyfileobj(src, dst)
        else:
            urllib.request.urlretrieve(source_url, out)
        return SourceDownloadResult(self.name,target_dir,[out],'MedlinePlus XML data; attribution to MedlinePlus.gov required.','Downloaded latest official XML file.')
