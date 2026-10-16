"""Project leading empty columns for planners while preserving source references."""
from types import SimpleNamespace
from openpyxl.utils import column_index_from_string,get_column_letter
from .workbook import Sheet

class ProjectedSheet(Sheet):
    def ref(self,r,c):return self.source.ref(r,c+self.offset)

def project(book):
    sheets=[];offsets={}
    for s in book.sheets:
        offset=min((c for r,c in s.cells),default=1)-1
        if not offset:sheets.append(s);continue
        cells={(r,c-offset):v for (r,c),v in s.cells.items()}
        merged=[(r1,max(1,c1-offset),r2,c2-offset) for r1,c1,r2,c2 in s.merged if c2>offset]
        indents={(r,c-offset):v for (r,c),v in s.indents.items() if c>offset}
        view=ProjectedSheet(s.name,cells,merged,s.rows,s.cols-offset,indents);view.source=s;view.offset=offset
        sheets.append(view);offsets[s.name]=offset
    if not offsets:return book,{}
    return SimpleNamespace(sheets=sheets,_map={s.name:s for s in sheets}),offsets

def restore(plan,offsets):
    def walk(value,bound=0):
        if isinstance(value,list):return [walk(x,bound) for x in value]
        if not isinstance(value,dict):return value
        if value.get('op')=='table':bound=offsets.get(value.get('sheet'),0)
        if set(value)=={'col'} and bound:
            return {'col':get_column_letter(column_index_from_string(value['col'])+bound)}
        return {key:walk(v,bound) for key,v in value.items()}
    return walk(plan)
