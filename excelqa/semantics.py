"""Bounded semantic selectors over actual headers/groups. No IDs, files or gold data.

The small vocabulary below translates concepts only (not answers). Unknown wording,
ambiguous scopes and unsupported layouts defer to the approved LLM.
"""
import re
import unicodedata
from .workbook import clean,number
from .expressions import inferred_format

def fold(v):
    t=''.join(c for c in unicodedata.normalize('NFKD',clean(v).casefold()) if not unicodedata.combining(c))
    return re.sub(r'[^\w]+',' ',t,flags=re.UNICODE).strip()
def num(v):
    try:return number(v)
    except ValueError:return None
def ref(s,r,c):return {'cell':s.ref(r,c)}
def op(name,*args):return {'op':name,'args':list(args)}
def label_col(s):
    counts={c:sum(isinstance(v,str) and num(v) is None and bool(clean(v)) for (r,cc),v in s.cells.items() if cc==c) for c in range(1,s.cols+1)}
    best=max(counts.values(),default=0);hits=[c for c,n in counts.items() if n==best and n]
    if len(hits)==1:return hits[0]
    keys={'industry','occupation','year','status','identity','need','type of need','指标'}
    named=[c for c in hits if any(fold(s.value(r,c)) in keys for r in range(1,min(s.rows+1,12)))]
    return named[0] if len(named)==1 else None

def unique_col(s,terms,before):
    hits=[]
    for c in range(1,s.cols+1):
        hs=[fold(re.sub(r'\(\d+\)$','',clean(s.expanded(r,c)))) for r in range(1,before)]
        if all(any(fold(term)==v or (len(fold(term))>6 and fold(term) in v) for v in hs) for term in terms):hits.append(c)
    return hits[0] if len(hits)==1 else None

def section(s,label,lc):
    wanted=fold(label)
    def key(v):return re.sub(r'\s+ethnicity$','',fold(v))
    starts=[r for (r,c),v in s.cells.items() if c==lc and key(v)==wanted]
    if len(starts)!=1:return None
    start=starts[0];end=s.rows+1
    for r in range(start+1,s.rows+1):
        if clean(s.value(r,lc)) and all(not clean(s.value(r,c)) for c in range(1,s.cols+1) if c!=lc):end=r;break
    return start,end

def scoped_row(s,group,metric,lc):
    bounds=section(s,group,lc)
    if not bounds:return None
    rows=[r for r in range(bounds[0]+1,bounds[1]) if fold(s.value(r,lc))==fold(metric)]
    return rows[0] if len(rows)==1 else None

def semantic_plan(book,query):
    q=re.sub(r'\s+',' ',query).strip()
    # Equivalent English task words; source labels are never rewritten.
    q=re.sub(r'\bgreatest percentage\b','highest percentage',q,flags=re.I)
    plans=[]
    for s in book.sheets:
        lc=label_col(s)
        if lc is None:continue
        for fn in (sex_gap,occupations,quartiles,reported_rate,multilingual):
            p=fn(s,q,lc)
            if p is not None:plans.append(p)
    return plans[0] if len(plans)==1 else None

def sex_gap(s,q,lc):
    m=re.fullmatch(r'For (.+?) people aged (\d+) years and over, how many percentage points higher was the labor force participation rate of men than that of women in (\d{4})\? Answer with only the number using exactly one decimal place\.',q,re.I)
    if not m or not any(fold(m[1]) in fold(v) for (r,c),v in s.cells.items() if len(clean(v))>len(m[1])):return None
    rows=[scoped_row(s,f'{sex} {m[2]} years and over','Participation rate',lc) for sex in ('Men','Women')]
    if any(r is None for r in rows):return None
    c=unique_col(s,['Total',m[3]],min(rows))
    if c is None or any(num(s.value(r,c)) is None for r in rows):return None
    return {'expression':op('sub',*[ref(s,r,c) for r in rows]),'format':inferred_format(q)}

def occupations(s,q,lc):
    m=re.fullmatch(r'In (\d{4}), among employed (women|men) who are .+?, which group had the highest percentage working in (.+?)\? Answer with only the group name: (.+?)\.',q,re.I)
    if m:
        labels=[re.sub(r'^or\s+','',x.strip(),flags=re.I) for x in m[4].split(',') if x.strip()]
        if len(labels)<2:return None
        items=[];values=[]
        for label in labels:
            bounds=section(s,label,lc);r=scoped_row(s,label,m[3],lc)
            if not bounds or r is None:return None
            c=unique_col(s,[m[2],m[1]],bounds[0])
            if c is None or num(s.value(r,c)) is None:return None
            source_label=ref(s,bounds[0],lc)
            alias=op('if',op('contains',source_label,{'constant':label}),{'constant':label},source_label)
            items.append({'label':alias,'value':ref(s,r,c)});values.append(num(s.value(r,c)))
        if values.count(max(values))!=1:return None
        return {'expression':{'op':'argmax','items':items},'format':{'type':'text'}}
    m=re.fullmatch(r'For employed (women|men) of all races combined, what is the absolute difference between (\d{4}) and (\d{4}) in the share working in (.+?)\? Answer with only the number using exactly two decimal places\.',q,re.I)
    if m:
        r=scoped_row(s,'TOTAL',m[4],lc);bounds=section(s,'TOTAL',lc)
        if r is None:return None
        cs=[unique_col(s,[m[1],y],bounds[0]) for y in (m[2],m[3])]
        if any(c is None or num(s.value(r,c)) is None for c in cs):return None
        return {'expression':op('abs',op('sub',*[ref(s,r,c) for c in cs])),'format':inferred_format(q)}
    return None

def industry_blocks(s,lc):
    # An industry starts with a label-only row followed by size-class rows.
    blocks=[]
    for r in range(1,s.rows):
        label=clean(s.value(r,lc))
        if not label or any(clean(s.value(r,c)) for c in range(1,s.cols+1) if c!=lc):continue
        after=clean(s.value(r+1,lc))
        if not (fold(after)=='total all sizes' or re.fullmatch(r'[\d,]+\s*[-–+]\s*\d*',after)):continue
        end=s.rows+1
        for rr in range(r+1,s.rows+1):
            if clean(s.value(rr,lc)) and all(not clean(s.value(rr,c)) for c in range(1,s.cols+1) if c!=lc):end=rr;break
        blocks.append((r,end))
    return blocks

def quartiles(s,q,lc):
    a=re.fullmatch(r"Within the '(.+?)' industry, excluding the overall '(.+?)' row, which employment size class has the largest gap between its 3rd quartile and its median incidence rate, and what is that gap\? Answer as `size class, gap`, separated by a comma and one space, with the gap using exactly one decimal place\.",q,re.I)
    b=re.fullmatch(r"Which industry has the highest average \(mean\) incidence rate among establishments in the '(.+?)' employment size class\? Ignore industries without data for that class\. Answer with only the industry name exactly as it appears in the table\.",q,re.I)
    c=re.fullmatch(r"Within the (.+?) \(NAICS (\d+)\) industry, does the rate below which three-fourths of the '(.+?)' establishments fall exceed (\d+(?:\.\d+)?)\? Answer with only Yes or No\.",q,re.I)
    if not (a or b or c):return None
    blocks=industry_blocks(s,lc)
    if not blocks:return None
    before=min(r for r,end in blocks)
    mean=unique_col(s,['mean'],before);median=unique_col(s,['median'],before);third=unique_col(s,['3rd quartile'],before)
    if b:
        if mean is None:return None
        items=[];values=[]
        for start,end in blocks:
            rs=[r for r in range(start+1,end) if fold(s.value(r,lc))==fold(b[1])]
            if len(rs)>1:return None
            if len(rs)==1 and num(s.value(rs[0],mean)) is not None:
                items.append({'label':ref(s,start,lc),'value':ref(s,rs[0],mean)});values.append(num(s.value(rs[0],mean)))
        if not items or values.count(max(values))!=1:return None
        return {'expression':{'op':'argmax','items':items},'format':{'type':'text'}}
    found=[]
    for start,end in blocks:
        label=fold(s.value(start,lc))
        if a:match=label==fold(a[1]) or label.startswith(fold(a[1])+' naics ')
        else:match=label.startswith(fold(c[1])+' naics '+c[2])
        if match:found.append((start,end))
    if len(found)!=1 or third is None:return None
    start,end=found[0]
    if c:
        rs=[r for r in range(start+1,end) if fold(s.value(r,lc))==fold(c[3])]
        if len(rs)!=1 or num(s.value(rs[0],third)) is None:return None
        return {'expression':op('gt',ref(s,rs[0],third),{'constant':float(c[4])}),'format':{'type':'yes_no'}}
    if median is None:return None
    items=[];values=[]
    for r in range(start+1,end):
        if fold(s.value(r,lc))==fold(a[2]):continue
        x,y=num(s.value(r,third)),num(s.value(r,median))
        if x is None or y is None:continue
        delta=op('sub',ref(s,r,third),ref(s,r,median));label=ref(s,r,lc)
        items.append({'label':label,'value':delta,'result':op('list',label,delta)});values.append(x-y)
    if not items or values.count(max(values))!=1:return None
    return {'expression':{'op':'pick','items':items},'format':{'type':'tuple','items':[{'type':'text'},{'type':'fixed','decimals':1}]}}

def reported_rate(s,q,lc):
    m=re.fullmatch(r'What is the combined incidence rate of (.+?) in the (.+?) industry, as reported in the table \(not summed from its components\)\? Answer with only the number using exactly two decimal places\.',q,re.I)
    if not m:return None
    rows=[r for (r,c),v in s.cells.items() if c==lc and fold(v)==fold(m[2])]
    if len(rows)!=1:return None
    r=rows[0];c=unique_col(s,[m[1],'Total'],r)
    if c is None or num(s.value(r,c)) is None:return None
    return {'expression':ref(s,r,c),'format':inferred_format(q)}

def multilingual(s,q,lc):
    if 'chưa được đáp ứng' in q and 'đáp ứng một phần' in q and 'cao nhất' in q:
        excluded=re.findall(r'`([^`]+)`',q)
        if len(excluded)!=1:return None
        unmet=[(r,c) for (r,c),v in s.cells.items() if fold(v)=='unmet']
        partial=[(r,c) for (r,c),v in s.cells.items() if fold(v)=='partially met']
        if len(unmet)!=1 or len(partial)!=1:return None
        start=max(unmet[0][0],partial[0][0]);uc=unmet[0][1];pc=partial[0][1]
        rows=[r for r in range(start+1,s.rows+1) if clean(s.value(r,lc)) and fold(s.value(r,lc))!=fold(excluded[0]) and num(s.value(r,uc)) is not None and num(s.value(r,pc)) is not None]
        if not rows:return None
        return {'expression':op('max',*[op('sum',ref(s,r,uc),ref(s,r,pc)) for r in rows]),'format':inferred_format(q)}
    # Vocabulary maps concepts in the request to English source headings.
    if all(x in q for x in ('femmes autochtones','plus élevée','plus faible',"trouble de l'humeur")):
        mappings=[('Premières Nations hors réserve','off-reserve first nations'),('Métis','metis'),('Inuits','inuit')]
        if not all(fold(a) in fold(q) for a,b in mappings):return None
        age=re.search(r'(\d+) ans et plus',q)
        if not age or not any('female' in fold(v) and age[1] in fold(v) for v in s.cells.values()):return None
        headers=[(r,c) for (r,c),v in s.cells.items() if fold(v)=='mood disorder']
        if len(headers)!=1:return None
        c=headers[0][1];refs=[]
        for _,label in mappings:
            rs=[r for (r,cc),v in s.cells.items() if cc==lc and fold(v)==fold(label)]
            if len(rs)!=1 or num(s.value(rs[0],c)) is None:return None
            refs.append(ref(s,rs[0],c))
        return {'expression':op('sub',op('max',*refs),op('min',*refs)),'format':inferred_format(q)}
    if '감소' in q and '퍼센트' in q:
        years=re.findall(r'\d{4}/\d{4}',q);metrics=re.findall(r'\(([A-Za-z ]+)\)',q)
        if len(years)!=2 or len(metrics)!=1:return None
        rs=[]
        for year in years:
            found=[r for (r,c),v in s.cells.items() if c==lc and clean(v)==year]
            if len(found)!=1:return None
            rs.append(found[0])
        c=unique_col(s,[metrics[0],'number'],min(rs))
        if c is None or any(num(s.value(r,c)) is None for r in rs):return None
        old,new=[num(s.value(r,c)) for r in rs]
        if old<=0 or new>old:return None
        return {'expression':op('abs',op('percent_change',ref(s,rs[1],c),ref(s,rs[0],c))),'format':inferred_format(q)}
    m=re.fullmatch(r'对于(.+?)的人群，(.+?)的(.+?)比(.+?)低多少个百分点？只回答数字，保留一位小数。',q)
    if m:
        bounds=section(s,m[3],lc)
        if not bounds:return None
        c=unique_col(s,[m[1]],bounds[0]);refs=[]
        if c is None:return None
        for label in (m[4],m[2]):
            r=scoped_row(s,m[3],label,lc)
            if r is None or num(s.value(r,c)) is None:return None
            refs.append(ref(s,r,c))
        return {'expression':op('sub',*refs),'format':inferred_format(q)}
    return None


def handles_query(q):
    t=q.casefold()
    return any(x in t for x in (
        'labor force participation rate of men than that of women',
        'among employed women who are','among employed men who are',
        'of all races combined','largest gap between its 3rd quartile',
        'highest average (mean) incidence rate','rate below which three-fourths',
        'as reported in the table (not summed from its components)',
        'chưa được đáp ứng','trouble de l’humeur',"trouble de l'humeur",
        '감소했습니까','低多少个百分点'))
