import tempfile,unittest
from pathlib import Path
from openpyxl import Workbook
from excelqa.workbook import Book
from excelqa.local import local_plan
from excelqa.solver import execute
from excelqa.expressions import PlanError
class LiveRegressionTests(unittest.TestCase):
    def book(self,rows,merges=()):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        w=Workbook();s=w.active;s.title='Different'
        for row in rows:s.append(row)
        for rg in merges:s.merge_cells(rg)
        p=Path(t.name)/'new.xlsx';w.save(p);return Book(p)
    def test_direct_children_rank_excludes_grandchildren_and_uses_new_values(self):
        b=self.book([['Indent Level','Item and group','Unadjusted percent change to Jan. 2025 from--',None],[None,None,'Jan. 2024','Dec. 2024'],[1,'Group X',0,0],[2,'Child A',-3,99],[3,'Grandchild',100,0],[2,'Child B',7,0],[2,'Child C',1,0],[1,'Next group',55,0]],['C1:D1'])
        q='Rank the categories directly under “Group X” by their unadjusted percent change to Jan. 2025 from Jan. 2024, from highest to lowest. Answer with the category names in that order, separated by a comma and one space, without numbering.'
        p=local_plan(b,q);self.assertIsNotNone(p);self.assertEqual(execute(b,p,q)[0],'Child B, Child C, Child A')
    def test_model_ranking_cannot_reverse_explicit_question_order(self):
        b=self.book([['Name','Value'],['A',3],['B',8]])
        p={'expression':{'op':'rank_labels','descending':False,'items':[{'label':{'cell':'Different!A2'},'value':{'cell':'Different!B2'}},{'label':{'cell':'Different!A3'},'value':{'cell':'Different!B3'}}]}}
        self.assertEqual(execute(b,p,'Rank from highest to lowest.')[0],'B, A')
        p['expression']['descending']=True
        self.assertEqual(execute(b,p,'Rank from lowest to highest.')[0],'A, B')
    def test_ethnic_increase_uses_correct_sex_age_and_year(self):
        b=self.book([['Status','Ethnic groups',None,None,None,None,None],[None,'Group A',None,'Group B',None,'Group C',None],[None,2020,2021,2020,2021,2020,2021],['Men, 16 years and over'],['Unemployed',1,999,1,2,1,2],['Women, 16 years and over'],['Unemployed',20,22,10,18,15,12],['Women, 20 years and over'],['Unemployed',1,888,1,2,1,2]],['B1:G1','B2:C2','D2:E2','F2:G2'])
        q='Among Group A, Group B and Group C women aged 16 years and over, which group had the largest increase in the number of unemployed people from 2020 to 2021, and by how many thousand? Answer as `group, increase`, separated by a comma and one space, with the increase as an integer.'
        p=local_plan(b,q);self.assertIsNotNone(p);self.assertEqual(execute(b,p,q)[0],'Group B, 8')
    def test_missing_cell_error_identifies_coordinate_for_repair(self):
        b=self.book([['x',1]])
        with self.assertRaisesRegex(ValueError,'Different!C9'):b.get('Different!C9')
