from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.utils.encoding import iri_to_uri

import nltk
import re, os, sys
import pandas as pd
from collections import defaultdict
# import camelot
import difflib as dl
import numpy as np
from tqdm import tqdm
import spacy 
# from spacy import displacy

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# local libraries

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),'pdfproc'))
from .pdfproc import * #pdf processing functions
from .contentproc import process_text #labeling content processing functions
from .termcall import * #AE term processing functions


# Create your views here.
def home(request):
    error_msg = ''
    if request.method == 'POST' :
        if 'user' in request.POST:
            user = request.POST.get('user')
        else:
            user = 'test'
        if not os.path.exists(os.path.join(BASE_DIR, 'static/history', user)):
            error_msg = 'User not existed! please contact admin to create your account.'
        else:    
            if 'oldfile' in request.FILES:
                # get two files
                myfile = request.FILES['oldfile']
                old_filename_origin = myfile.name
                fs = FileSystemStorage()
                old_file_name = os.path.join(BASE_DIR, 'static/history', user, old_filename_origin)
                if os.path.exists(old_file_name): os.remove(old_file_name)
                old_filename = fs.save(old_file_name, myfile)
                # old_file_url = fs.url(filename)
            else: # using blank template
                old_filename = ''
                old_filename_origin = None

            if  'newfile' in request.FILES:
                myfile = request.FILES['newfile']
                new_filename_origin = myfile.name
                fs = FileSystemStorage()
                new_file_name = os.path.join(BASE_DIR, 'static/history', user, new_filename_origin)
                if os.path.exists(new_file_name): os.remove(new_file_name)
                new_filename = fs.save(new_file_name, myfile)
                # new_file_url = fs.url(filename)
            else:
                new_filename = '' 

            if ('newfile' not in request.FILES) and ('old_pdf' in request.POST) and ('new_pdf' in request.POST):
                old_filename_origin = request.POST.get('old_pdf')
                if old_filename_origin:
                    old_filename = os.path.join(BASE_DIR, 'static/history', user, old_filename_origin)
                else:  # using blank template
                    old_filename = ''
                new_filename_origin = request.POST.get('new_pdf')
                new_filename = os.path.join(BASE_DIR, 'static/history', user, new_filename_origin)
            
            if not os.path.exists(new_filename) or (old_filename and not os.path.exists(old_filename)): 
                error_msg= 'File not existed! '+new_filename + '|'+ old_filename
            elif new_filename:
                ## processing pdf to get section-level texts
                if old_filename:
                    if request.POST.getlist('oldfile_format'):
                        highlights_old, toc_old, fulltext_old, tables_old, w_old = pdf_process(old_filename, max_page=None)
                    else:
                        error_msg= 'old file is not PLR format!!'
                        context = {'error_msg':error_msg}
                        return render(request, "pdf.html", context)
                else:
                    highlights_old, toc_old, fulltext_old, tables_old, w = '','','',[], 0
               
                if request.POST.getlist('newfile_format'):
                    highlights_new, toc_new, fulltext_new, tables_new, w_new = pdf_process(new_filename, max_page=None)
                else:
                    error_msg= 'new file is not PLR format!!'
                    context = {'error_msg':error_msg}
                    return render(request, "pdf.html", context)
                
                hl_level,fulltext_level,AE_sections = predefine() #predefine levels
                
                toc_res_old, ae_res_old = process_text(highlights_old, toc_old, fulltext_old, hl_level,fulltext_level,AE_sections, w_old)
                toc_res_new, ae_res_new = process_text(highlights_new, toc_new, fulltext_new, hl_level,fulltext_level,AE_sections, w_new)
                
                sections_avail = list(set(list(ae_res_old.keys()) + list(ae_res_new.keys())))
                sections_avail_sorted = []
                for x in sections_avail:
                    tmp = re.split(r'\.', str(x))
                    if len(tmp)>1:
                        sections_avail_sorted.append([x, int(tmp[0]), int(tmp[1])])
                    else:
                        sect_num = re.search(r'\d+', tmp[0])[0]
                        sections_avail_sorted.append([tmp[0], int(sect_num), 0])
                sections_avail_sorted = [x[0] for x in sorted(sections_avail_sorted, key=lambda x: [x[1], x[2]])]
                
                text_old, text_new, summary, change_summary, sections_avail = show_section_change(ae_res_old, ae_res_new, 
                                              check_sections = sections_avail_sorted, comp_display=True, show_nochange = True)
                
                ae_method = request.POST.get('ae_method')
                change_summary, old_ae, new_ae = AE_annotation(change_summary, method = ae_method)
                 
                add_aes, rem_aes, unchanged_aes, text_old, text_new = prep_aes(old_ae, new_ae, text_old, text_new)

                toc_changes = tocchanges(toc_res_old, toc_res_new)

                context = {'toc_changes': toc_changes, 
                           'summary': summary, 'text_old': text_old, 'text_new':text_new, 
                           'fulltext_summary':change_summary.to_html(escape=False, table_id='summary_table',classes="table table-striped"),
                           'sections':sections_avail, 'old_file':old_filename_origin, 'new_file':new_filename_origin,
                           'add_aes':add_aes, 'rem_aes':rem_aes, 'unchanged_aes': unchanged_aes
                          }

                return render(request, "pdf_search.html", context)
        
    default_folder = 'history'
    history_folder = os.path.join(BASE_DIR, 'static', default_folder)
    files=[]
    for user in os.listdir(history_folder):
        curr_records = os.listdir(history_folder+'/'+user)
        for r in curr_records:
            files.append([user, r])
    context = {'files':sorted(files, key=lambda x:x[1]), 'error_msg':error_msg}
    return render(request, "pdf.html", context)

def search(request):
    return render(request, "pdf_search.html")   
    
