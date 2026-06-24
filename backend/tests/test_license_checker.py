from app.ingestion.license_checker import LicenseChecker

def test_license_checker_allows_open():
    r=LicenseChecker().validate('CC BY 4.0', 'https://example.org')
    assert r.allowed

def test_license_checker_blocks_unknown_textbook():
    r=LicenseChecker().validate('copyright all rights reserved textbook', '')
    assert not r.allowed
