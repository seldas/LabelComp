import cx_Oracle
import json, re
import pandas as pd
from xml.etree import ElementTree as ET
from itertools import islice

def OutputTypeHandler(cursor, name, defaultType, size, precision, scale):
    if defaultType == cx_Oracle.CLOB:
        return cursor.var(cx_Oracle.LONG_STRING, arraysize = cursor.arraysize)
    elif defaultType == cx_Oracle.BLOB:
        return cursor.var(cx_Oracle.LONG_BINARY, arraysize = cursor.arraysize)
    
dsnStr = cx_Oracle.makedsn('ncsvmscidevl.nctr.fda.gov','1521','scidevl')
con = cx_Oracle.connect(user="lwu", password="lwu", dsn=dsnStr)
con.outputtypehandler = OutputTypeHandler
cursor=con.cursor()

def spl_process(file_name, max_page=None):
    sid = file_name
    d = return_data(file_name)
    if not d: continue
    
    indication_main = ET.fromstring(d[0]).findall('./xlmns:text',{'xlmns':'urn:hl7-org:v3'})
    indication_text = indication_main + ET.fromstring(d[0]).findall('.//xlmns:component/xlmns:section',{'xlmns':'urn:hl7-org:v3'})
    indication_text = [ET.tostring(x, method='text').decode('ISO8859-1') for x in indication_text]
    indication_text = '\n'.join(indication_text)

    highlights = ET.fromstring(d[0]).findall('.//xlmns:highlight',{'xlmns':'urn:hl7-org:v3'})
    highlights = [ET.tostring(x, method='text').decode('ISO8859-1') for x in highlights]
    highlights = '\n'.join(highlights)

    ind_text = proc_text(indication_text)
    hl_text  = proc_text(highlights)

    df.loc[ind,'Indication And Usage']=ind_text
    df.loc[ind,'Indication And Usage - Highlights']= hl_text
            
    return hl, tc, ft, tables

def return_data(setid):
    if not setid:
        return None
    cursor=con.cursor()
    # \'34066-1\' boxed warning, \'34070-3\' contraindication, \'43685-7\' warnings and precautions, 
    # \'34084-4\' adverse reactions, \'34073-7\ drug interactions'
    cursor.execute('select sec.content_XML.getClobVal() from druglabel.spl_sec sec'+
                   ' join druglabel.sum_spl spl on spl.spl_id=sec.spl_id '+
                   ' where sec.loinc_code in (\'34066-1\', \'34070-3\', \'43685-7\', \'34084-4\', \'34073-7\') '+
                   ' and spl.set_id =\''+setid+'\' '
                   )
    res = [r for r in cursor.fetchall()]

    return res
    
def proc_text(text):
    text = re.sub('\n',' ',text)
    text = re.sub(r'&#\d+;',' ',text)
    text = re.sub(r'\s+',' ',text).strip()
    return text