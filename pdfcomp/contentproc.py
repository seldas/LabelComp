import nltk
import re, os
from collections import defaultdict

def process_text(highlights, toc, fulltext, hl_level,fulltext_level,AE_sections, w):
    highlight_res = process_highlights(highlights, hl_level)
    toc_res = process_toc(toc)
    fulltext_res = process_fulltext(fulltext)
    ae_res = process_AEsections(fulltext_res, w)
    # return highlight_res, toc_res, fulltext_res, ae_res
    return toc_res, ae_res

def process_highlights(hl, hl_level):
    whole_text = ' '.join([x[4] for x in hl if x[4].strip()])
    whole_text = re.sub(r' *\-+ *', '-', whole_text).strip()
    
    res = defaultdict(str)
    if not whole_text: return res
    
    for key in hl_level:
        whole_text = re.sub('-'+key+'-', '~~~'+key+'~~~', whole_text)
    sections = re.split(r'(~~~[\w\d ]+~~~)', whole_text)
    for i, x in enumerate(sections):
        if re.match(r'~~~[\w\d ]+~~~', x):
            res[x] = sections[i+1].strip()
    return res

def process_toc(toc):
    whole_text = ' '.join([x[4] for x in toc if x[4].strip()])
    whole_text = re.sub('\s+',' ', whole_text)
    whole_text = re.sub(r'(?<=\s)(\d+[\.\d]*)(?=\s[A-Z])', r'~~~\1~~~', whole_text)
    res = defaultdict(str)
    if not whole_text: return res
    
    whole_text = re.sub(r'(\d+[\.\d]*)(?=\s[A-Z])', r'~~~\1~~~',whole_text[0]) + whole_text[1:]
    sections = re.split(r'(~~~\d+[\.\d]*~~~)', whole_text)
    # print(sections)
    for i, x in enumerate(sections):
        if re.match(r'~~~\d+[\.\d]*~~~', x):
            fulltxt = re.split(r'\*', sections[i+1])[0]
            res[x] = re.sub(r'~','',x)+' '+re.sub(r'\s+' , ' ',fulltxt).strip()
    return res

def process_fulltext(fulltext):
    whole_text = defaultdict(list)
    curr_title = 'LabelHead'
    # seperate blocks if it contains a pre-defined section title
    section_titles = {'WARNING:':0,
                      'INDICATIONS AND USAGE':1,
                      'DOSAGE AND ADMINISTRATION':2,
                      'DOSAGE FORMS AND STRENGTHS':3,
                      'CONTRAINDICATIONS':4,
                      'WARNINGS AND PRECAUTIONS':5,
                      'ADVERSE REACTIONS':6,
                      'DRUG INTERACTIONS':7,
                      'USE IN SPECIFIC POPULATIONS':8,
                      'DRUG ABUSE AND DEPENDENCE':9,
                      'OVERDOSAGE':10,
                      'DESCRIPTION':11,
                      'CLINICAL PHARMACOLOGY':12, 
                      'NONCLINICAL TOXICOLOGY':13, 
                      'CLINICAL STUDIES':14, 
                      'REFERENCES':15, 
                      'HOW SUPPLIED/STORAGE AND HANDLING':16, 
                      'PATIENT COUNSELING INFORMATION':17
                     }
    
    curr_section = -1
    for b in fulltext:
        context = b[4].strip()
        for sec_t in section_titles.keys():
            if section_titles[sec_t] <= curr_section: continue # sections once finished, never back :)
            
            if (sec_t == 'WARNING:' and re.search(r'\s+'+sec_t, context)):
                contexts = re.split(r'\s+'+sec_t,context)
                if len(contexts)>1:
                    whole_text[curr_section].append((b[0],b[1],b[2],b[3],contexts[0],b[5],b[6],b[7]))
                    b = (b[0],b[1],b[2],b[3],''.join(contexts[1:]),b[5],b[6],b[7])
                curr_section = section_titles[sec_t]
                curr_title = sec_t
            elif re.search(str(section_titles[sec_t])+r'\.*\s+'+sec_t, context):
                contexts = re.split(str(section_titles[sec_t])+r'\.*\s+'+sec_t,context)
                if len(contexts)>1:
                    whole_text[curr_section].append((b[0],b[1],b[2],b[3],contexts[0],b[5],b[6],b[7]))
                    b = (b[0],b[1],b[2],b[3],''.join(contexts[1:]),b[5],b[6],b[7])
                curr_section = section_titles[sec_t]
                curr_title = sec_t
            elif re.search(r'^\s*'+sec_t, context): # very rare cases there is no \d in front
                contexts = re.split(str(section_titles[sec_t])+r'\s+'+sec_t,context)
                if len(contexts)>1:
                    whole_text[curr_section].append((b[0],b[1],b[2],b[3],contexts[0],b[5],b[6],b[7]))
                    b = (b[0],b[1],b[2],b[3],''.join(contexts[1:]),b[5],b[6],b[7])
                curr_section = section_titles[sec_t]
                curr_title = sec_t
                
                
        whole_text[curr_section].append(b)  
        
    return whole_text

def process_AEsections(fulltext_res, w):
    AE_res=defaultdict(list)
    for sect_id, blocks in fulltext_res.items():
        if sect_id not in (0, 4, 5, 6, 7): continue
        curr_sectid = str(sect_id)
        for b in blocks:
            context = b[4].strip()
            context = re.sub('\s+',' ', context) # any kind of whitespace or invisible separator
            context = re.sub(r'[\x00-\x1f]', '', context) #any invisible control characters
            context = re.sub(r'[\~\$\^]+', '', context) #punctuation and symbols, ~ $ ^ = < > /
            context = re.sub(r'\'(?=s\s)', '', context) #apostrophe following an "s" at the end of a word
            context = re.sub(r'(?<=[a-zA-Z])- (?=[a-zA-Z])', '-', context) #remove apostrophe following an "s" at the end of a word
            if not context: continue
            if re.search(r'('+str(sect_id)+r'\.\d+)(?=\s[A-Z])', context) and b[0]<= w:
                # there are probably multiple subsections in the same paragraph.
                subids = re.split(r'('+str(sect_id)+r'\.\d+)(?=\s[A-Z])', context)
                for tmp_txt in subids:
                    if re.match('^\d+\.\d+$', tmp_txt):
                        curr_sectid = str(tmp_txt)
                    AE_res[curr_sectid].append(tmp_txt)
                # sub_sectid = re.search(r'('+str(sect_id)+r'\.\d+)(?=\s[A-Z])', context)[1]
                # print(sub_sectid)
                # curr_sectid = sub_sectid
            else:
                AE_res[curr_sectid].append(b[4])
        # if sect_id == 5:
        #    print(AE_res)
            
    # convert blocks into puretexts
    for k in AE_res.keys():
        tmp_txt = re.sub(r'\s+',' ', ' '.join([x for x in AE_res[k]]))
        AE_res[k] = [re.sub(r'[\. ]*\.[\. ]+','. ',x).strip() for x in nltk.tokenize.sent_tokenize(tmp_txt)]
    
    return AE_res

def sentence_prep(curr_title, paragraph):
    paragraph = re.sub('\s+',' ', paragraph) # any kind of whitespace or invisible separator
    conjunct_text = re.sub(r'[\x00-\x1f]', '', paragraph) #any invisible control characters
    conjunct_text = re.sub(r'[\~\$\^]+', '', conjunct_text) #punctuation and symbols, ~ $ ^ = < > /
    conjunct_text = re.sub(r'\'(?=s\s)', '', conjunct_text) #apostrophe following an "s" at the end of a word
    conjunct_text = re.sub(r'(?<=[a-zA-Z])- (?=[a-zA-Z])', '-', conjunct_text) #remove apostrophe following an "s" at the end of a word
    # conjunct_text = re.sub(r'(?<=[a-zA-Z])-(?=[a-zA-Z])', '', conjunct_text) #minus/hyphen (-) when surrounded by alphabetical characters
    
    curr_section = re.match(r'^(\d+)\s', curr_title)
    if not curr_section:
        # print('something wrong:', curr_title)
        return {curr_title:[re.sub(r'[\. ]*\.[\. ]+','. ',x).strip() for x in nltk.tokenize.sent_tokenize(conjunct_text)]}
    else:
        # label all subsections
        conjunct_text = re.sub(curr_section[1]+r'\.\d+(?=\s[A-Z])', r'~~~\g<0>~~~', conjunct_text)
        tmp_res = re.split(r'(~~~[\d+ \.]+~~~)', conjunct_text)

        subsections = {}
        if len(tmp_res)==1:
            return {curr_title:[re.sub(r'[\. ]*\.[\. ]+','. ',x).strip() for x in nltk.tokenize.sent_tokenize(tmp_res[0])]}
        
        for ind, txt in enumerate(tmp_res):
            if ind == 0 and re.match(r'^\d+\s', txt):
                subsections[curr_title] = [txt, ]
            if re.match(r'^~~~\d+\.\d+',txt):
                subsection_id = re.sub(r'~','',txt)
                subsections[subsection_id] = [re.sub(r'[\. ]*\.[\. ]+','. ',x).strip() for x in nltk.tokenize.sent_tokenize(tmp_res[ind+1])]
        # print(subsections, tmp_res)
        return subsections
