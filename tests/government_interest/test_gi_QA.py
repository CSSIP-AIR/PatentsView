import pytest

from lib.configuration import get_config


@pytest.fixture()
def config():
    config = get_config()
    yield config


class TestGIQA:
    def test_sampler(self, config):
        from QA.government_interest.GovtInterestTester import GovtInterestTester
        import pandas as pd
        giqc = GovtInterestTester(config)
        giqc.generate_govt_int_samples()
        qc_data = pd.DataFrame(giqc.qa_data['DataMonitor_govtinterestsampler'])
        all_pat = qc_data[qc_data.sample_type == 'All Patents']

        assert (all_pat.shape[0] > 0)
        assert (len(all_pat.patent_id.unique()) == 25)
        us_pat = qc_data[qc_data.sample_type == 'All Patents']

        assert (us_pat.shape[0] > 0)
        assert (len(us_pat.patent_id.unique()) == 25)