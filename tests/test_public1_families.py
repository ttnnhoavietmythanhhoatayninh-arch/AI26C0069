import test_semantics as helpers
import unittest,datetime
class PublicOneFamilies(unittest.TestCase):
    book=helpers.SemanticTests.book
    answer=helpers.SemanticTests.answer
    def test_person_event_age_and_top_subset(self):
        d=datetime.datetime
        b=self.book([['Last','Birth','Admission','Score'],['A',d(2000,1,1),d(2020,1,1),10],['B',d(1990,1,1),d(2025,1,1),22],['C',d(1995,1,1),d(2010,1,1),88]],offset=15)
        self.assertEqual(self.answer(b,'What score did the second-oldest person receive? Answer with only the integer score.'),'10')
        self.assertEqual(self.answer(b,'Among the two youngest people, what was the highest score? Answer with only the integer score.'),'88')
    def test_fiscal_scope_and_year_order(self):
        b=self.book([[None,'Fiscal years',None,'Fiscal year-to-date',None],[None,2020,2021,2020,2021],['Agricultural exports',999,1,5,8],[],[None,'Calendar years',None,'Calendar year-to-date',None],[None,2020,2021,2020,2021],['Agricultural exports',1,999,10,2]],['B1:C1','D1:E1','B5:C5','D5:E5'],4)
        self.assertEqual(self.answer(b,'Is the agricultural export value for the fiscal year-to-date 2021 greater than that for the fiscal year-to-date 2020? Answer with only Yes or No.'),'Yes')
    def test_absolute_month_change_uses_unadjusted_interval(self):
        b=self.book([['Indent Level','Expenditure category','Unadjusted percent change','Unadjusted percent change','Seasonally adjusted percent change'],[None,None,'Oct. 2022-Oct. 2023','Sep. 2023-Oct. 2023','Sep. 2023-Oct. 2023'],[1,'A',999,2,999],[2,'B',0,-9,1],[2,'C',0,5,2]],offset=3)
        self.assertEqual(self.answer(b,'Considering all categories, infer which category experienced the highest absolute change in "Unadjusted percent change" between September 2023 and October 2023. Answer with only the category name.'),'B')
    def test_hours_count_not_percent_or_all_industries(self):
        b=self.book([['Hours of work','Persons at work',None,None,'Percent distribution',None],[None,'All industries','Agriculture and related industries','Nonagricultural industries','All industries','Agriculture and related industries'],['7 to 16 hours',100,23,77,50,80]],['B1:D1','E1:F1'],4)
        self.assertEqual(self.answer(b,'What is the number of persons at work in all industries who work 7-16 hours and in agriculture? Answer with only the integer, without commas or units.'),'23')
    def test_marital_average_total_not_full_time(self):
        b=self.book([['Characteristic','Average hours',None],[None,'Total at work','Persons who usually work full time'],['MARITAL STATUS'],['Men, 16 years and over'],['Widowed, divorced, or separated(2)',31.2,99],['Women, 16 years and over'],['Widowed, divorced, or separated(2)',29.8,88]],['B1:C1'],5)
        self.assertEqual(self.answer(b,'What are the "Average hours" worked by widowed, divorced, or separated men and women aged 16 years and over? Answer as `men, women`, using exactly two decimal places and separating the values with a comma and one space.'),'31.20, 29.80')
class ShiftedFamilies(PublicOneFamilies):col_offset=2
