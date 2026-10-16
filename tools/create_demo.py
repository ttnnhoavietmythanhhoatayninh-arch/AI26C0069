"""Create synthetic local demo, never public/hidden contest answers."""
import argparse,json
from pathlib import Path
from openpyxl import Workbook

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',default='demo_data');a=p.parse_args()
    root=Path(a.out);(root/'xlsx_files').mkdir(parents=True,exist_ok=True)
    w=Workbook();s=w.active;s.title='Industry example'
    for r in [['Industry','NAICS code','Total recordable cases'],['Example A',123456,7],['Example B',234567,3],['Parent group',1234,9]]:s.append(r)
    w.save(root/'xlsx_files'/'example.xlsx')
    (root/'queries.json').write_text(json.dumps([{'id':1,'file_name':'example.xlsx','query':'How many industries with a 6-digit NAICS code have a total recordable cases incidence rate above 5.0? Answer with only the integer.'}],indent=2),encoding='utf-8')
    print(root.resolve())
if __name__=='__main__':main()
