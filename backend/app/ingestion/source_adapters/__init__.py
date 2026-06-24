from app.ingestion.source_adapters.demo_adapter import DemoSourceAdapter
from app.ingestion.source_adapters.medlineplus_adapter import MedlinePlusAdapter
from app.ingestion.source_adapters.pmc_adapter import PMCOAAdapter
ADAPTERS={'demo':DemoSourceAdapter(),'medlineplus':MedlinePlusAdapter(),'pmc_oa_sample':PMCOAAdapter()}
