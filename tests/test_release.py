import tempfile,time,unittest
from pathlib import Path
from openpyxl import Workbook
from excelqa.workbook import Book,number
from excelqa.local import local_plan
from excelqa.solver import execute
from excelqa.expressions import Evaluator,PlanError

class ReleaseTests(unittest.TestCase):
    def book(self,sheets):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        w=Workbook();w.remove(w.active)
        for name,rows in sheets.items():
            s=w.create_sheet(name)
            for row in rows:s.append(row)
        p=Path(tmp.name)/'changed.xlsx';w.save(p);return Book(p)
    def test_currency_source_numbers(self):
        self.assertEqual(number('$1,234'),1234)
        self.assertEqual(number('($12.50)'),-12.5)
        with self.assertRaises(ValueError):number('12%')
    def test_conditional_selects_question_label_from_cell_comparison(self):
        b=self.book({'x':[['a','b'],[9,3]]})
        p={'expression':{'op':'if','args':[{'op':'gt','args':[{'cell':'x!A2'},{'cell':'x!B2'}]},{'constant':'first group'},{'constant':'second group'}]}}
        self.assertEqual(execute(b,p,'Answer first group or second group.')[0],'first group')
    def test_cross_sheet_revenue_uses_changed_values(self):
        b=self.book({'North':[['Revenue','Fiscal2024'],['Total segment revenue','$300']], 'South':[['Revenue','Fiscal2024'],['Total segment revenue','$500']]})
        q='In Fiscal2024, what was the combined Total segment revenue of all the segments reported in this workbook, in millions of dollars? Answer with only the integer, without commas or units.'
        p=local_plan(b,q);self.assertIsNotNone(p);self.assertEqual(execute(b,p,q)[0],'800')
    def test_sheet_ranking_returns_actual_sheet_name(self):
        b=self.book({'North':[['Revenue','Fiscal2024'],['Service and other revenue',300]],'South':[['Revenue','Fiscal2024'],['Service and other revenue','$500']]})
        q='Which sheet reports the higher Service and other revenue in Fiscal2024, and what was that value in millions of dollars? Answer as `sheet name, integer value`, separated by a comma and one space, without commas inside the number and without units.'
        p=local_plan(b,q);self.assertIsNotNone(p);self.assertEqual(execute(b,p,q)[0],'South, 500')
    def test_grouped_activity_preserves_group_headers_and_shifted_rows(self):
        b=self.book({'New':[[None],['Activity','Average hours per day spent in primary activities'],[None,'Married mothers'],[None,'Employed full time'],['Own household children group A'],['Housework',0.2],['Own household children group B'],['Housework',0.9]]})
        q="Across the three groups of own household children shown in the table, for which group do full-time employed married mothers spend the most average hours per day on 'Housework'? Answer with only the group name exactly as it appears in the table."
        p=local_plan(b,q);self.assertIsNotNone(p);self.assertEqual(execute(b,p,q)[0],'Own household children group B')
    def test_ratio_uses_year_end_not_average_column(self):
        b=self.book({'Funding':[['At December 31, 2024',None,'Average'],[None,2024,2024],['Other borrowed funds','$40','$999'],['Preferred stock(h)','$80','$1']]})
        q='What is the ratio of Other borrowed funds at December 31, 2024 to Preferred stock at December 31, 2024? Answer with only the number rounded to three decimal places.'
        p=local_plan(b,q);self.assertIsNotNone(p);self.assertEqual(execute(b,p,q)[0],'0.500')
    def test_relative_importance_selects_label_column_not_first_column(self):
        b=self.book({'Index':[['Indent Level','Item and group','Relative importance 2024'],[0,'Housing',40.2],[0,'Food and beverages',10.123]]})
        q='How many percentage points larger is the relative importance of Housing than that of Food and beverages? Answer with only the number using exactly three decimal places.'
        p=local_plan(b,q);self.assertIsNotNone(p);self.assertEqual(execute(b,p,q)[0],'30.077')
    def test_year_change_uses_reported_change_column(self):
        b=self.book({'Index':[['Item','Unadjusted percent change to Jan. 2025 from--',None],[None,'Jan. 2024','Dec. 2024'],['Services',9.5,99],['Commodities',2.2,88]]})
        b.sheets[0].merged=[(1,2,1,3)]
        q='How many percentage points higher was the unadjusted percent change from Jan. 2024 to Jan. 2025 for Services than for Commodities? Answer with only the number using exactly one decimal place.'
        p=local_plan(b,q);self.assertIsNotNone(p);self.assertEqual(execute(b,p,q)[0],'7.3')
    def test_fair_value_change_uses_total_not_level_columns(self):
        b=self.book({'Assets':[[None,'At July 31, 2024',None,'At July 31, 2023',None],['In millions','Level 1','TotalFair Value','Level 1','TotalFair Value'],['Total assets measured at fair value on a recurring basis',999,'$900',888,'$700']]})
        b.sheets[0].merged=[(1,2,1,3),(1,4,1,5)]
        q='By how much did the total assets measured at fair value on a recurring basis increase between July 31, 2023 and July 31, 2024, in millions of dollars? Answer with only the integer, without commas or units.'
        p=local_plan(b,q);self.assertIsNotNone(p);self.assertEqual(execute(b,p,q)[0],'200')
    @unittest.skipUnless(__import__('os').name=='posix','POSIX permissions only')
    def test_csv_can_be_read_after_root_container_writes_it(self):
        import stat
        from excelqa.contract import write_results
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'out.csv';write_results(p,[{'id':1,'answer':'1'}])
            self.assertTrue(stat.S_IMODE(p.stat().st_mode) & stat.S_IROTH)
    def test_no_truncation_at_eighty_rows(self):
        b=self.book({'Long':[['Code','Amount']]+[[i,i*2] for i in range(1,151)]})
        self.assertEqual(b.get('Long!B151'),300)
        self.assertIn('300',str(b.context('last amount')))

if __name__=='__main__':unittest.main()
