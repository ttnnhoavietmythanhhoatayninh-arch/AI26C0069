import json,tempfile,unittest,os
from pathlib import Path
from unittest.mock import patch
from openpyxl import Workbook
from local_runner import prepare_run
from excelqa.contract import InputError
class RunnerTests(unittest.TestCase):
    def fixture(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);root=Path(t.name)
        data=root/'data';(data/'xlsx_files').mkdir(parents=True)
        w=Workbook();w.active.append(['value',2]);w.save(data/'xlsx_files'/'a.xlsx')
        (data/'queries.json').write_text(json.dumps([{'id':1,'file_name':'a.xlsx','query':'Question'}]))
        return data,root/'out'
    def test_offline_drops_inherited_key_and_does_not_put_it_in_argv(self):
        data,out=self.fixture()
        with patch.dict(os.environ,{'OPENROUTER_API_KEY':'secret'}):args,env,n=prepare_run(data,out)
        self.assertNotIn('OPENROUTER_API_KEY',env);self.assertNotIn('secret',' '.join(args));self.assertEqual(n,1)
    def test_hybrid_key_only_in_environment(self):
        data,out=self.fixture();args,env,n=prepare_run(data,out,'hybrid','test-secret')
        self.assertEqual(env['OPENROUTER_API_KEY'],'test-secret');self.assertNotIn('test-secret',' '.join(args))
    def test_rejects_output_inside_input(self):
        data,out=self.fixture()
        with self.assertRaises(InputError):prepare_run(data,data/'output')
