import json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from backend.loader import HybridJobLoader

class CacheRecoveryTests(unittest.TestCase):
    def fixture(self, temp):
        return HybridJobLoader(Path(temp)/'missing.csv',Path(temp)/'cache.json','')

    def test_combined_backup_survives_missing_or_corrupt_field_cache(self):
        for corrupt in (False, True):
            with self.subTest(corrupt=corrupt), tempfile.TemporaryDirectory() as temp:
                loader=self.fixture(temp)
                backup={'id':'health-backup','title':'Health assistant','company':'Example','skills':{'Communication':5},'search_fields':['healthcare']}
                loader.cache_path.write_text(json.dumps([backup]),encoding='utf-8')
                if corrupt: loader.cache_path.with_name('cache-healthcare.json').write_text('{broken',encoding='utf-8')
                loader.api_url='https://jsearch.p.rapidapi.com/search-v2'
                loader.search_mode='fields'
                def fetch():
                    if loader.active_search_field=='healthcare': return []
                    return [{'id':loader.active_search_field,'title':'Example role','company':'Example','skills':{'Communication':5},'source_kind':'live','search_fields':[loader.active_search_field]}]
                with patch.object(loader,'read_single_api',side_effect=fetch): jobs=loader.read_api()
                self.assertEqual(len(jobs),9)
                self.assertEqual(loader.query_status['healthcare'],{'source':'cache','returned_jobs':1})
                self.assertEqual(next(j for j in jobs if j['id']=='health-backup')['source_kind'],'cache')
                self.assertEqual(len(json.loads(loader.cache_path.read_text(encoding='utf-8'))),9)

    def test_failed_replace_preserves_previous_file_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as temp:
            loader=self.fixture(temp)
            loader.cache_path.write_text('["old snapshot"]',encoding='utf-8')
            with patch.object(Path,'replace',side_effect=OSError('locked')):
                self.assertFalse(loader.write_cache(loader.jobs))
            self.assertEqual(loader.cache_path.read_text(encoding='utf-8'),'["old snapshot"]')
            self.assertEqual(list(Path(temp).glob('*.tmp')),[])
            self.assertEqual(loader.cache_write_failures,1)

    def test_storage_deduplicates_backups_and_is_independent_of_serving(self):
        with tempfile.TemporaryDirectory() as temp:
            loader=self.fixture(temp)
            self.assertTrue(loader.write_cache(loader.jobs))
            loader.cache_path.with_name('cache-technology.json').write_text(loader.cache_path.read_text(encoding='utf-8'),encoding='utf-8')
            loader.cache_path.with_name('cache-broken.json').write_text('{broken',encoding='utf-8')
            status=loader.cache_status()
            self.assertEqual(status['stored_jobs'],12)
            self.assertEqual(status['served_jobs'],0)
            self.assertEqual(status['usable_files'],2)
            self.assertEqual(status['invalid_files'],1)
            self.assertIsNotNone(status['last_saved_at'])

    def test_match_keeps_one_snapshot_during_refresh(self):
        from backend import main
        with tempfile.TemporaryDirectory() as temp:
            original=self.fixture(temp); replacement=self.fixture(temp)
            replacement.jobs=[];replacement.matrix=replacement.matrix[:0]
            class SwapOnIteration(list):
                def __iter__(self):
                    main.loader=replacement
                    return super().__iter__()
            original.jobs=SwapOnIteration(original.jobs)
            with patch.object(main,'loader',original):
                result=main.match(main.MatchRequest(skill_vector={'Python':5},limit=10))
            self.assertEqual(len(result),10)
