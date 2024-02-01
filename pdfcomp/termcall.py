import nltk
import re, os, sys
import pandas as pd
from collections import defaultdict
# import camelot
import difflib as dl
import numpy as np
import spacy 
import openai
import pickle

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cur_model = os.path.join(BASE_DIR, 'static', 'ners', 'ner_model')
spacy.prefer_gpu()
nlp = spacy.load(cur_model)
llt_dict = pickle.load(open(BASE_DIR+'/static/ners/llt_dict_ptname.pkl','rb'))
 
def predefine():
    hl_level = ['HIGHLIGHTS OF PRESCRIBING INFORMATION','WARNING:','RECENT MAJOR CHANGES','INDICATIONS AND USAGE','DOSAGE AND ADMINISTRATION','DOSAGE FORMS AND STRENGTHS',
                'CONTRAINDICATIONS','WARNINGS AND PRECAUTIONS','ADVERSE REACTIONS','DRUG INTERACTIONS','USE IN SPECIFIC POPULATIONS','See 17']
    ft_level = ['WARNING:','INDICATIONS AND USAGE','DOSAGE AND ADMINISTRATION','DOSAGE FORMS AND STRENGTHS','CONTRAINDICATIONS','WARNINGS AND PRECAUTIONS',
                       'ADVERSE REACTIONS','DRUG INTERACTIONS','USE IN SPECIFIC POPULATIONS','DRUG ABUSE AND DEPENDENCE','OVERDOSAGE','DESCRIPTION','CLINICAL PHARMACOLOGY',
                       'NONCLINICAL TOXICOLOGY','CLINICAL STUDIES','REFERENCES','HOW SUPPLIED/STORAGE AND HANDLING','PATIENT COUNSELING INFORMATION']
    ae_sections = ['~~~0 WARNING:~~~', '~~~4 CONTRAINDICATIONS~~~', '~~~5 WARNINGS AND PRECAUTIONS~~~',
                     '~~~6 ADVERSE REACTIONS~~~', '~~~7 DRUG INTERACTIONS~~~',]

    return hl_level, ft_level, ae_sections

def show_section_change(ae_res_old, ae_res_new, check_sections, comp_display=False, show_nochange = True):
    text_old, text_new = [], []
    summary = []
    diff_report_summary = []
    sections_avail = []
    for k in check_sections:
        c_old = ae_res_old[k]
        c_new = ae_res_new[k]
        section_num = re.search(r'\d+\.*\d*', k)[0]
        if not c_old and not c_new:
            # summary.append([k, 'invalid', 'Section '+k+' is not a valid section number.'])
            continue
        c_old_process = [re.sub(r'\s+',' ', re.sub(r'\W',' ', x)).strip().lower() for x in c_old]
        c_new_process = [re.sub(r'\s+',' ', re.sub(r'\W',' ', x)).strip().lower() for x in c_new]
        if c_old_process == c_new_process:
            summary.append([section_num, 'same', 'Section '+k+' is mostly the same!'])
        else:
            summary.append([section_num, 'updated', 'Section '+k+' has been updated!'])
            sections_avail.append(section_num)
            dff = list(dl.ndiff(c_old, c_new))
            old_version, new_version=[], []
            diff_report=[]
            for idx, x in enumerate(dff):
                curr_type = 'other'
                if comp_display == True:
                    if re.match(r'[\-]',x):
                        final = ''
                        if idx+1<len(dff):
                            if re.match(r'[\?]',dff[idx+1]):
                                for char, tag in zip(x, dff[idx+1]):
                                    if tag =='?':
                                        continue
                                    elif tag == '^':
                                        final += '<mark2>'+char+'</mark2>'
                                    elif tag == '-':
                                        final += '<mark2>'+char+'</mark2>'
                                    else:
                                        final += char
                                if len(dff[idx+1])<len(x):
                                    final += x[-(len(x)-len(dff[idx+1])):]
                            elif idx+2<len(dff) and re.match(r'[\+]',dff[idx+1]) and re.match(r'[\?]',dff[idx+2]) :
                                final = x[1:]
                            else:
                                # final = '<mark>!!</mark>' + x 
                                final = x[1:]
                                curr_type = 'old'
                        else:
                            final = x[1:]
                            curr_type = 'old'
                        final = re.sub('</mark1><mark1>','',final)
                        final = re.sub('</mark2><mark2>','',final)
                        text_old.append([section_num, curr_type, final])
                    elif re.match(r'[\+]',x):
                        final = ''
                        if idx+1<len(dff):
                            if re.match(r'[\?]',dff[idx+1]):
                                for char, tag in zip(x, dff[idx+1]):
                                    if tag =='?':
                                        continue
                                    elif tag == '^':
                                        final += '<mark3>'+char+'</mark3>'
                                    elif tag == '+':
                                        final += '<mark3>'+char+'</mark3>'
                                    else:
                                        final += char
                                if len(dff[idx+1])<len(x):
                                    final += x[-(len(x)-len(dff[idx+1])):]
                            elif idx-2>=0 and re.match(r'[\-]',dff[idx-2]) and re.match(r'[\?]',dff[idx-1]):
                                final = x[1:]
                            else:
                                # final = '<mark>!!</mark>' + x
                                final = x[1:]
                                curr_type = 'new'
                        else:
                            final = x[1:]
                            curr_type = 'new'
                        final = re.sub('</mark1><mark1>','',final)
                        final = re.sub('</mark3><mark3>','',final)
                        text_new.append([section_num, curr_type, final])
                    elif re.match(r'[\?]',x):
                        continue
                    else:
                        if show_nochange == True:
                            text_old.append([section_num, curr_type, x])
                            text_new.append([section_num, curr_type, x])
                        else:
                            continue
                diff_report.append(x)
            for x in diff_report:
                if re.match(r'\-', x):
                    diff_report_summary.append([section_num, 'Old', x])
                elif re.match(r'\+', x):
                    diff_report_summary.append([section_num, 'New', x])
    
    if len(diff_report_summary):
        total_res = pd.DataFrame(diff_report_summary)
        total_res.columns = ['Section', 'Type', 'Sentence']
    else:
        total_res = pd.DataFrame(columns = ['Section', 'Type', 'Sentence'])
    
    return text_old, text_new, summary, total_res, sections_avail

def prep_aes(old_ae, new_ae, text_old, text_new):
    
    add_aes = list(new_ae - old_ae)
    rem_aes = list(old_ae - new_ae)
    
    add_aes_fin = []
    rem_aes_fin = []
    unchanged_aes_fin = defaultdict(str)
    for sect, subsect_id, ae, pt, soc, context in add_aes:
        flag=0
        for sect_id, sent_type, sent in text_old:
            main_sect = re.split(r'\.', sect_id)[0]
            if main_sect == sect and re.search(re.escape(ae), sent, re.IGNORECASE):
                # print(ae, sent)
                flag=1
                break
        if flag==0: 
            add_aes_fin.append([subsect_id, ae, pt, soc, context])
        else:
            if str(subsect_id)+'+'+ae not in unchanged_aes_fin.keys():
                unchanged_aes_fin[str(subsect_id)+'+'+ae] = pt+'+'+soc
            elif pt == 'na' and soc == 'na':
                continue
            else:
                unchanged_aes_fin[str(subsect_id)+'+'+ae] = pt+'+'+soc
    
    for sect, subsect_id, ae, pt, soc, context in rem_aes:
        flag=0
        for sect_id, sent_type, sent in text_new:
            main_sect = re.split(r'\.', sect_id)[0]
            if main_sect == sect and re.search(re.escape(ae), sent, re.IGNORECASE):
                flag=1
                break
        if flag==0: rem_aes_fin.append([subsect_id, ae, pt, soc, context])
        
    add_aes = sorted(add_aes_fin, key=lambda x: [x[0],x[1]])
    rem_aes = sorted(rem_aes_fin, key=lambda x: [x[0], x[1]])
    
    unchanged_aes = sorted([[*re.split(r'\+', k), *re.split(r'\+', v), ] for k, v in unchanged_aes_fin.items()], key=lambda x: [x[0], x[1]])
    
    marked_ae = defaultdict(int)
    for sect, ae, pt, soc, context in add_aes:
        if marked_ae[ae]==1: continue
        for i, (sect, t, sent) in enumerate(text_new): 
            text_new[i][2] = re.sub(re.escape(ae), '<mark_ae>'+re.escape(ae)+'</mark_ae>', sent, flags=re.I)
        marked_ae[ae] = 1

    marked_ae = defaultdict(int)
    for sect, ae, pt, soc, context in rem_aes:
        if marked_ae[ae]==1: continue
        for i, (sect, t, sent) in enumerate(text_old): 
            text_old[i][2] = re.sub(re.escape(ae), '<mark_ae>'+re.escape(ae)+'</mark_ae>', sent, flags=re.I)
        marked_ae[ae] = 1
    
    return  add_aes, rem_aes, unchanged_aes, text_old, text_new
        
def AE_annotation(change_summary, method = 'RxBERT'):
    # MedDRA annotation on changed text
    new_ae, old_ae = set(), set()
    for idx, d in change_summary.iterrows():
        sect_id, sent_type, input_text = d['Section'], d['Type'], d['Sentence']
        main_sect = re.split(r'\.', sect_id)[0]
        result=defaultdict(list)
        if method in ('RxBERT', 'Both'):
            result = RxBERT_match(input_text, result)
        if method in ('MedDRA', 'Both'):
            result = MedDRA_match(input_text, result)
            
        if len(result) == 0:
            change_summary.loc[idx, 'Sent_MedDRA'] = d['Sentence']
            continue
                    
        ## replace the original text to highlighted texts
        annotated_text = input_text
        all_terms = []
        for k in result.keys():
            start, end, text = re.split(r'\|', k)
            dtype, pt, soc = re.split(r'\|', result[k])
            all_terms.append([start, end, text, dtype, pt, soc, input_text])
        all_terms = sorted(all_terms, key=lambda x: int(x[0]), reverse=False)
        curr, curr_end = 0, -1
        for term in all_terms:
            start, end, text, dtype, pt, soc, context = term
            if sent_type=='Old':
                old_ae.add((main_sect, sect_id, text, pt, soc, context))
            else:
                new_ae.add((main_sect, sect_id, text, pt, soc, context))
            start, end = int(start), int(end)
            if start <= curr_end: # this is a repeated/overlapped annotation
                continue 
            new = "<text class='annotation "+dtype+" "+sent_type+"' val='"+text+"'>"+str(annotated_text[curr+start:curr+end])+"</text>"
            annotated_text = annotated_text[:(curr+start)]+new+annotated_text[(curr+end):]
            curr += (len(new) - end + start)
            curr_end = end
        
        annotated_text = re.sub('\n','<br>',annotated_text)
        change_summary.loc[idx, 'Sent_MedDRA'] = annotated_text
        # change_summary.loc[idx, 'AE_terms'] = '; '.join([re.split(r'\|',x)[2] for x in result.keys()])
    change_summary = change_summary.drop(['Sentence'],axis=1)

    return change_summary, old_ae, new_ae
    
def tocchanges(toc_res_old, toc_res_new):
    toc_changes=[]
    for k, v in toc_res_old.items():
        if toc_res_new[k] and toc_res_new[k].strip('. ')==v.strip('. '):
            continue
        else:
            toc_changes.append([re.sub(r'~','', k), v.strip(), toc_res_new[k].strip(), ])
    for k, v in toc_res_new.items():
        if k not in toc_res_old:
            toc_changes.append([re.sub(r'~','', k), ' ', v.strip()])  
    
    toc_changes = sorted(toc_changes, key=lambda x: int(re.split(r'\.', x[0])[0]))

    # only AE sections
    new_toc_changes=[]
    for item in toc_changes:
        if re.match(r'^[4567]\.',item[0]):
            new_toc_changes.append(item)
    
    return new_toc_changes


def RxBERT_match(input_text, result):
    input_text = input_text.strip()
    doc_ents = nlp(nlp.make_doc(input_text))
    for ent in doc_ents.ents:
        if ent.label_ == 'AdverseReaction': # we only care about this category for now.
            cid = str(ent.start_char)+'|'+str(ent.end_char)+'|'+ent.text.lower()
            result[cid] = 'AE_OSE'+'|na|na'
    return result

   
def MedDRA_match(input_text, result):
    t = input_text.lower()
    for start in llt_dict.keys():
        try:
            if start.lower() in t:
                curr_llts = llt_dict[start]
                for curr in curr_llts:
                    for match_tmp in re.finditer(curr[1], input_text):
                        cid = str(match_tmp.start())+'|'+str(match_tmp.end())+'|'+curr[0].lower()
                        result[cid] = 'AE_OSE_MedDRA'+'|'+curr[3]+'|'+curr[4]
                        break
        except:
            # print('error:', start)
            continue
    
    return result