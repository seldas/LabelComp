import re, os
from collections import defaultdict

import pandas as pd
import numpy as np

import fitz

# use pymupdf package (fitz)
def pdf_process(file_name, max_page=None):
    hl, tc, ft, tables = '', '', '', [] # initialize
    hl_content, tc_content, ft_content = [], [], []
    current_part = 'hl' # We assume a labeling document always starts with a highlight
    header, footer = 0, 0 # initialize header and footer for filter
    with fitz.open(file_name) as pdf:
        toc_count = 0 # this is the count of blocks of Toc, if it is too small when meet the keywords, will skip.
        for i, page in enumerate(pdf):
            _,_,w,h = page.bound()
            content = page.get_text('blocks')
            
            # define the head and foot part of the page.
            if i == 0 and header==0 and footer==0:
                headers, footers = [0,], [h,]
                for b in content:
                    text = re.sub(r'\s+',' ',b[4]).strip()
                    if re.match('^\d+$',text):
                        if b[1]>0.9 * h:
                            footers.append(b[1]-5)
                        elif b[3]<0.1 * h:
                            headers.append(b[3]+5)
                    elif re.search(r'Page \d+ of \d+', text) and b[1]>0.8 * h:
                        footers.append(b[1]-5)
                    elif re.search('Reference ID:', text) and b[1]>0.8 * h: 
                        footers.append(b[1]-5)
                    # elif re.search('HIGHLIGHTS OF PRESCRIBING INFORMATION', text) and b[1] < 0.2 * h:
                    #    headers.append(b[1]-5)
                
                # print(footers, headers)
                header = max(headers)
                footer = min(footers)
                sect_left_border = 0.1*w
            # remove headers and footers if necessary
            # the first time see 
            content = filter_blocks(content, w, h, header, footer)
            if current_part in ('hl','tc'):
                for b in content:
                    
                    b += (i, )
                    if re.search(r'FULL PRESCRIBING INFORMATION\s*\:\s*CONTENTS', b[4]):
                        if current_part == 'hl':
                            current_part = 'tc'
                        toc_count = 0
                    
                    #if re.search('FULL PRESCRIBING', b[4]):
                        #print(current_part, b, toc_count)
                    
                    if re.search(r'FULL PRESCRIBING INFORMATION\s*(?!:)', b[4]):
                        if current_part == 'tc':
                            if toc_count > 100:
                                current_part = 'ft'
                                sect_left_border += b[0]
                        
                    if current_part == 'tc':
                        toc_count += len(b[4])
                        
                    
                    if current_part == 'hl':
                        hl_content.append(b)
                    elif current_part == 'tc':
                        tc_content.append(b)
                    elif current_part == 'ft':
                        ft_content.append(b)
                    
                    pre_b = b
                    
            elif current_part in ('ft',):
                for b in content:
                    b += (i, )
                    ft_content.append(b)
            
        hl = sort_blocks(hl_content, w, h, s_type='two_columns')
        tc = sort_blocks(tc_content, w, h, s_type='two_columns')
        ft = sort_blocks(ft_content, w, h, s_type='vertical')
    # print(hl, tc, ft)
    return hl, tc, ft, tables, sect_left_border

# sort by vertical then horizontal
def filter_blocks(content, w, h, header, footer):
    content_update=[]
    for x in content:
        if x[1]>footer or x[3]<header: continue
        content_update.append(x)
    return sorted(content_update, key=lambda x: x[1]) # return in vertical (up-to-bottom) order

def sort_blocks(content, w, h, s_type='vertical'):
    if s_type == 'vertical':
        return sorted(content, key=lambda x: [x[7], x[1]], reverse=False)
    elif s_type == 'two_columns':
        return sorted(content, key=lambda x: [x[7], np.floor(x[0]/w/0.4),x[1]], reverse=False)
    
def remove_table(content, tables, h):
    bboxes = []
    for df in tables:
        x0, x1, y0, y1 = min([x[0] for x in df.cols]), max([x[1] for x in df.cols]), min([x[1] for x in df.rows]), max([x[0] for x in df.rows])
        bboxes.append([x0, y0, x1, y1])
    
    res=[]
    for block in content:
        flag = 0
        x0, y0, x1, y1 = block[:4]
        y0, y1 = h-y0, h-y1
        for box in bboxes:
            if box[1]<y0<box[3] or box[1]<y1<box[3]:
                flag = 1
                break
        
        if flag == 0 and block[6]!=1 and block[4].strip():
            res.append(block[4])
    
    return res

def pdf_process_generic(file_name, max_page=None):
    # this function is to get AE sections only based on their titles;
    hl, tc, ft, tables = '', '', '', [] # initialize
    hl_content, tc_content, ft_content = [], [], []
    current_part = 'hl' # We assume a labeling document always starts with a highlight
    header, footer = 0, 0 # initialize header and footer for filter
    with fitz.open(file_name) as pdf:
        toc_count = 0 # this is the count of blocks of Toc, if it is too small when meet the keywords, will skip.
        for i, page in enumerate(pdf):
            _,_,w,h = page.bound()
            content = page.get_text('blocks')
            
            # define the head and foot part of the page.
            if i == 0 and header==0 and footer==0:
                headers, footers = [0,], [h,]
                for b in content:
                    text = re.sub(r'\s+',' ',b[4]).strip()
                    if re.match('^\d+$',text):
                        if b[1]>0.9 * h:
                            footers.append(b[1]-5)
                        elif b[3]<0.1 * h:
                            headers.append(b[3]+5)
                    elif re.search(r'Page \d+ of \d+', text) and b[1]>0.8 * h:
                        footers.append(b[1]-5)
                    elif re.search('Reference ID:', text) and b[1]>0.8 * h: 
                        footers.append(b[1]-5)
                    # elif re.search('HIGHLIGHTS OF PRESCRIBING INFORMATION', text) and b[1] < 0.2 * h:
                    #    headers.append(b[1]-5)
                
                # print(footers, headers)
                header = max(headers)
                footer = min(footers)
                sect_left_border = 0.1*w
            # remove headers and footers if necessary
            # the first time see 
            content = filter_blocks(content, w, h, header, footer)
            
            # here we considered all information are for full_text
            for b in content:
                b += (i, )
                ft_content.append(b)
            
        hl = sort_blocks(hl_content, w, h, s_type='two_columns')
        tc = sort_blocks(tc_content, w, h, s_type='two_columns')
        ft = sort_blocks(ft_content, w, h, s_type='vertical')
    # print(hl, tc, ft)
    return hl, tc, ft, tables, sect_left_border