"""Local GUI command builder; never puts secrets in argv or writes them to disk."""
import os
import sys
from pathlib import Path
from excelqa.contract import InputError,read_queries,workbook_path,check_output
ROOT=Path(__file__).resolve().parent

def prepare_run(data_dir,output_dir,solver='offline',key=''):
    if solver not in ('offline','hybrid'):raise InputError('Choose offline or hybrid')
    data=Path(data_dir).resolve();out=Path(output_dir).resolve()
    if out==data or out.is_relative_to(data):raise InputError('Output must be outside the input data directory')
    queries=read_queries(data/'queries.json')
    for q in queries:workbook_path(data/'xlsx_files',q['file_name'])
    check_output(out/'submission.csv',data/'xlsx_files',data/'queries.json')
    env=os.environ.copy();env.pop('OPENROUTER_API_KEY',None)
    if solver=='hybrid':
        key=key or os.environ.get('OPENROUTER_API_KEY','')
        if not key.strip():raise InputError('Hybrid needs an authorized OpenRouter key; may incur API charges')
        if '\n' in key or '\r' in key:raise InputError('Invalid key')
        env['OPENROUTER_API_KEY']=key.strip()
    args=[sys.executable,str(ROOT/'main.py'),'--xlsx-dir',str(data/'xlsx_files'),'--queries',str(data/'queries.json'),
          '--output',str(out/'submission.csv'),'--report',str(out/'run_report.json'),'--solver',solver]
    return args,env,len(queries)
