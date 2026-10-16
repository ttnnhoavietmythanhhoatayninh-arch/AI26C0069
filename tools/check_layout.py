import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from excelqa.workbook import Book
from excelqa.local import local_plan
from excelqa.solver import execute
import argparse
p=argparse.ArgumentParser(description='Offline in-memory layout mutation check; never modifies input XLSX')
p.add_argument('--data-dir',required=True);args=p.parse_args()
root=Path(args.data_dir);queries=json.loads((root/'queries.json').read_text())
if (root/'answers.json').exists():gold={str(x['id']):x['answer'] for x in json.loads((root/'answers.json').read_text())}
else:
 import csv
 with (root/'sample_submission.csv').open(encoding='utf-8-sig',newline='') as f:gold={str(x['id']):x['answer'] for x in csv.DictReader(f)}
results=[]
for q in queries:
 b=Book(root/'xlsx_files'/q['file_name']);b.path=Path('different_workbook.xlsx');b._map={}
 for i,s in enumerate(b.sheets):
  s.name=f'Changed_{i}';s.cells={(r+5,c+2):v for (r,c),v in s.cells.items()};s.merged=[(r1+5,c1+2,r2+5,c2+2) for r1,c1,r2,c2 in s.merged];s.indents={(r+5,c+2):v for (r,c),v in s.indents.items()};s.rows+=5;s.cols+=2;b._map[s.name]=s
 try:
  p=local_plan(b,q['query']);answer=execute(b,p,q['query'])[0] if p else ''
 except Exception as e:answer='ERROR:'+type(e).__name__
 # A question explicitly asking for a sheet name must follow the new sheet name.
 expected=gold[str(q['id'])]
 if 'sheet name' in q['query'].lower():
  import re
  original=Book(root/'xlsx_files'/q['file_name'])
  for i,s in enumerate(original.sheets):expected=expected.replace(s.name,f'Changed_{i}')
 results.append({'id':q['id'],'correct':answer==expected,'answer':answer,'expected':expected})
print(json.dumps({'questions':len(results),'correct':sum(x['correct'] for x in results),'failures':[x for x in results if not x['correct']]},ensure_ascii=False,indent=2))

raise SystemExit(0 if all(x['correct'] for x in results) else 1)
