"""CI/local Docker smoke test; synthetic data only, no external API."""
import csv,json,subprocess,tempfile
from pathlib import Path
from openpyxl import Workbook

def main():
    image='ai26c0069:check'
    subprocess.run(['docker','build','--platform','linux/amd64','-t',image,'.'],check=True)
    size=int(subprocess.check_output(['docker','image','inspect',image,'--format','{{.Size}}'],text=True))
    if size>1_000_000_000:raise RuntimeError('Docker image exceeds conservative 1 GB check')
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);data=root/'input';out=root/'output';(data/'xlsx_files').mkdir(parents=True);out.mkdir()
        w=Workbook();w.active.append(['Industry','NAICS code','Total recordable cases']);w.active.append(['Example',123456,7]);w.save(data/'xlsx_files'/'fresh.xlsx')
        (data/'queries.json').write_text(json.dumps([{'id':1,'file_name':'fresh.xlsx','query':'How many industries with a 6-digit NAICS code have a total recordable cases incidence rate above 5.0? Answer with only the integer.'}]))
        subprocess.run(['docker','run','--rm','--platform','linux/amd64','--memory=4g','--cpus=2','--network=none','--read-only','--tmpfs','/tmp:rw,size=64m',
            '--mount',f'type=bind,source={data},target=/input,readonly','--mount',f'type=bind,source={out},target=/output',image,
            '--xlsx-dir','/input/xlsx_files','--queries','/input/queries.json','--output','/output/submission.csv',
            '--openrouter-key','synthetic-unused-key','--openrouter-model','qwen/qwen3.7-flash','--openrouter-base-url','https://openrouter.ai/api/v1','--solver','offline'],check=True,timeout=120)
        with (out/'submission.csv').open(newline='',encoding='utf-8') as f:assert list(csv.DictReader(f))==[{'id':'1','answer':'1'}]
    print(json.dumps({'docker_smoke':'passed','image_bytes':size}))
if __name__=='__main__':main()
