import csv
import io
import urllib.parse
import urllib.request
from app.ingestion.source_adapters.base import SourceAdapter, SourceDownloadResult

class PMCOAAdapter(SourceAdapter):
    id='pmc_oa_sample'; name='PMC Open Access Sample'
    oa_file_list='https://pmc-oa-opendata.s3.amazonaws.com/deprecated/oa_comm/xml/metadata/csv/oa_comm.filelist.csv'
    object_base_url='https://pmc-oa-opendata.s3.amazonaws.com/'
    allowed_licenses={'CC0','CC BY','CC BY-SA','CC BY-ND'}

    def download(self,target_dir,limit=5):
        target_dir.mkdir(parents=True, exist_ok=True)
        files = []
        req = urllib.request.Request(self.oa_file_list, headers={'User-Agent':'ClinicalRAG-PMCAdapter/1.0'})
        with urllib.request.urlopen(req, timeout=120) as response:
            reader = csv.reader(io.TextIOWrapper(response, encoding='utf-8', errors='ignore', newline=''))
            for row in reader:
                if len(files) >= limit:
                    break
                if len(row) < 8 or row[0].lower() == 'key':
                    continue
                license_type = row[6].strip().upper()
                retracted = row[7].strip().lower()
                if license_type not in self.allowed_licenses or retracted == 'yes':
                    continue
                pmcid = row[3]
                object_url = urllib.parse.urljoin(self.object_base_url, row[0])
                out = target_dir / f'{pmcid}.xml'
                urllib.request.urlretrieve(object_url, out)
                files.append(out)
        return SourceDownloadResult(self.name,target_dir,files,'PMC Open Access commercial-use XML sample; article-level Creative Commons license retained in metadata.','Downloaded XML files from PMC AWS Open Data.')
