import tempfile,unittest
from pathlib import Path
from openpyxl import Workbook
from excelqa.workbook import Book
from excelqa.local import local_plan
from excelqa.solver import execute
class SemanticTests(unittest.TestCase):
    def book(self,rows,merges=(),offset=0):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        w=Workbook();s=w.active;s.title='Renamed'
        for _ in range(offset):s.append([])
        col_offset=getattr(self,'col_offset',0)
        for row in rows:s.append([None]*col_offset+row)
        from openpyxl.worksheet.cell_range import CellRange
        for rg in merges:
            cr=CellRange(rg);cr.shift(row_shift=offset,col_shift=col_offset);s.merge_cells(str(cr))
        p=Path(tmp.name)/'arbitrary.xlsx';w.save(p);return Book(p)
    def answer(self,b,q):
        p=local_plan(b,q);self.assertIsNotNone(p);return execute(b,p,q)[0]
    def test_sex_gap_by_population_and_age(self):
        b=self.book([['Employment of Group X'],['Status','Total(1)',None,'Other group',None],[None,2020,2021,2020,2021],['Men, 18 years and over'],['Participation rate',50,80,1,2],['Women, 18 years and over'],['Participation rate',40,55,3,4]],['B2:C2','D2:E2'],3)
        q='For Group X people aged 18 years and over, how many percentage points higher was the labor force participation rate of men than that of women in 2021? Answer with only the number using exactly one decimal place.'
        self.assertEqual(self.answer(b,q),'25.0')
    def test_occupation_rank_changed_groups_values_and_position(self):
        b=self.book([['Occupation','Women',None,'Men',None],[None,2020,2021,2020,2021],['Group A'],['Technical occupations',3,20,99,99],['Group B'],['Technical occupations',5,50,0,0],['Group C'],['Technical occupations',8,30,0,0]],['B1:C1','D1:E1'],4)
        q='In 2021, among employed women who are Group A, Group B, or Group C, which group had the highest percentage working in technical occupations? Answer with only the group name: Group A, Group B, or Group C.'
        self.assertEqual(self.answer(b,q),'Group B')
    def test_all_races_absolute_year_difference(self):
        b=self.book([['Occupation','Women',None],[None,2020,2021],['TOTAL'],['Technical occupations',10.5,7.25],['Group A'],['Technical occupations',99,1]],['B1:C1'])
        q='For employed women of all races combined, what is the absolute difference between 2020 and 2021 in the share working in technical occupations? Answer with only the number using exactly two decimal places.'
        self.assertEqual(self.answer(b,q),'3.25')
    def quartiles(self):
        return self.book([['Industry, NAICS code, and establishment employment size','Average incidence rates for all establishments:','One-half','Three-fourths'],[None,'(mean)','(median)','(3rd quartile)'],['Widget production (NAICS 999111)'],['Total all sizes',100,1,99],['11 - 49',2,3,4],['50 - 249',5,1,8],['250 - 999','-',2,3],['Another industry'],['50 - 249',9,2,5]],offset=2)
    def test_quartile_gap_excludes_total_and_missing(self):
        q="Within the 'Widget production' industry, excluding the overall 'Total all sizes' row, which employment size class has the largest gap between its 3rd quartile and its median incidence rate, and what is that gap? Answer as `size class, gap`, separated by a comma and one space, with the gap using exactly one decimal place."
        self.assertEqual(self.answer(self.quartiles(),q),'50 - 249, 7.0')
    def test_industry_ranking_uses_requested_size(self):
        q="Which industry has the highest average (mean) incidence rate among establishments in the '50 - 249' employment size class? Ignore industries without data for that class. Answer with only the industry name exactly as it appears in the table."
        self.assertEqual(self.answer(self.quartiles(),q),'Another industry')
    def test_quartile_threshold_uses_naics_from_question(self):
        q="Within the Widget production (NAICS 999111) industry, does the rate below which three-fourths of the '11 - 49' establishments fall exceed 3.0? Answer with only Yes or No."
        self.assertEqual(self.answer(self.quartiles(),q),'Yes')
    def test_reported_combined_rate_not_sum_components(self):
        b=self.book([['Industry','Cases with days away from work, job restriction, or transfer',None,None],[None,'Total','Days away','Transfer'],['Example manufacturing',2.4,2,3]],['B1:D1'],5)
        q='What is the combined incidence rate of cases with days away from work, job restriction, or transfer in the Example manufacturing industry, as reported in the table (not summed from its components)? Answer with only the number using exactly two decimal places.'
        self.assertEqual(self.answer(b,q),'2.40')
    def test_vietnamese_unmet_sum_excludes_named_total(self):
        b=self.book([['Need','unmet','partially met','fully met'],['any',90,9,1],['Care A',20,15,65],['Care B','..',40,60],['Care C',10,30,60]],offset=3)
        q='Trong các loại hình chăm sóc cần thiết (không tính dòng `any`), tổng tỷ lệ chưa được đáp ứng và đáp ứng một phần cao nhất là bao nhiêu phần trăm? Chỉ trả lời bằng số với đúng một chữ số thập phân.'
        self.assertEqual(self.answer(b,q),'40.0')
    def test_french_range_uses_only_requested_groups(self):
        b=self.book([['female population aged 15 and over'],['Identity','mood disorder'],['total aboriginal identity female population',99],['off-reserve first nations',25],['metis',15],['inuit',10],['non-aboriginal identity female population',0]],offset=2)
        q="Parmi les femmes autochtones de 15 ans et plus, quel est l'écart (en points de pourcentage) entre la prévalence la plus élevée et la plus faible du trouble de l'humeur parmi les trois groupes autochtones (Premières Nations hors réserve, Métis, Inuits) ? Répondez uniquement par le nombre avec une décimale, sans le symbole %."
        self.assertEqual(self.answer(b,q),'15.0')
    def test_korean_year_decrease_uses_number_not_change_column(self):
        b=self.book([['Year','total cases',None],[None,'number','percent change from previous year'],['2000/2001','1,000',99],['2009/2010',800,77]],['B1:C1'],3)
        q='2000/2001년 대비 2009/2010년에 성인 형사 법원에서 완료된 총 사건(total cases) 수는 몇 퍼센트 감소했습니까? 소수점 둘째 자리까지, % 기호 없이 숫자만 답하십시오.'
        self.assertEqual(self.answer(b,q),'20.00')
    def test_chinese_scope_excludes_other_metric_and_marital_group(self):
        b=self.book([['指标','已婚或同居','单身或曾结婚'],['劳动参与率'],['原住民',99,80],['非原住民',99,90],['就业率'],['原住民',99,40],['非原住民',99,65],['失业率'],['原住民',99,1],['非原住民',99,2]],offset=4)
        q='对于单身或曾结婚的人群，原住民的就业率比非原住民低多少个百分点？只回答数字，保留一位小数。'
        self.assertEqual(self.answer(b,q),'25.0')

class ShiftedColumnSemanticTests(SemanticTests):
    col_offset=2

class AmbiguityTests(unittest.TestCase):
    book=SemanticTests.book
    answer=SemanticTests.answer
    def test_ambiguous_tied_ranking_defers(self):
        from excelqa.semantics import semantic_plan
        b=self.book([['Industry, NAICS code, and establishment employment size','Average incidence rates for all establishments:'],[None,'(mean)'],['Industry A'],['50 - 249',5],['Industry B'],['50 - 249',5]])
        q="Which industry has the highest average (mean) incidence rate among establishments in the '50 - 249' employment size class? Ignore industries without data for that class. Answer with only the industry name exactly as it appears in the table."
        self.assertIsNone(semantic_plan(b,q))
        self.assertIsNone(local_plan(b,q))
    def test_equivalent_ranking_wording(self):
        b=self.book([['Occupation','Women',None],[None,2020,2021],['Group A'],['Technical occupations',3,20],['Group B'],['Technical occupations',5,50]],['B1:C1'])
        q='In 2021, among employed women who are Group A or Group B, which group had the greatest percentage working in technical occupations? Answer with only the group name: Group A, or Group B.'
        self.assertEqual(self.answer(b,q),'Group B')
    def test_existing_naics_planner_after_column_shift(self):
        self.col_offset=2
        b=self.book([['Industry','NAICS code','Total recordable cases'],['One',123456,7],['Two',234567,3]],offset=5)
        q='How many industries with a 6-digit NAICS code have a total recordable cases incidence rate above 5.0? Answer with only the integer.'
        self.assertEqual(self.answer(b,q),'1')

    def test_existing_annual_planner_after_column_shift(self):
        self.col_offset=2
        b=self.book([['Year','Employed',None],[None,'Total','Agriculture'],[2018,100,3],[2019,120,9],[2020,70,4]],offset=5)
        q='In which year did the number of employed people fall the most compared with the previous year, and by how many thousand? Answer as year, decrease, as integers.'
        self.assertEqual(self.answer(b,q),'2020, 50')
