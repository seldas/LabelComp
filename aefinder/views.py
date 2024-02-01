from django.shortcuts import render

import re, os, sys
import pandas as pd
from collections import defaultdict
# import camelot
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from .apicall import * #AE term processing functions

# Create your views here.
def aefinder(request):
    prompt, query, response = '', '', ''
    if request.method == 'POST' :
        option = request.POST.get('prompt_option')
        if option == 'Monograph_CHE':
            prompt = '''
                        Give a Relevant/Irrelevant answer whether you consider this paper is relevant to Chlorine Efficacy Research or not;
                        Also provide the reason in one sentence;
                        the two parts of the answer should be separated by "|".
                        Criteria of relevance: Only articles on chlorine gas and other compounds directly releasing chlorine in its application, 
                        should be considered as a relevant research.
                     '''
        elif option == 'Monograph_CHS':
            prompt = '''
                        Give a Relevant/Irrelevant answer whether you consider this paper is relevant to Chlorine Safety Research or not;
                        Also provide the reason in one sentence;
                        the two parts of the answer should be separated by "|".
                        Criteria of relevance: Only articles on chlorine gas and other compounds directly releasing chlorine in its application, 
                        should be considered as a relevant research.
                     '''
        elif option == 'Monograph_P4HB':
            prompt = '''
                        Determine whether this input document/paragraph is “relevant” or “irrelevant” to immune/inflammatory host responses and pro-oncogenic and oncogenic (tumorigenic and carcinogenic) effects/properties of poly(4-hydroxybutyrate), or P4HB, and its degradation products, return the binary relevant/irrelevant answer;
                        Also provide the reason in one sentence;
                        the two parts of the answer should be separated by "|".
                     '''
        elif option == 'AE_finder':
            prompt = '''I want you to act as drug labeling document reviewer, and I will give you several paragraphs from drug labeling documents. 
                        I need you to find all adverse events terms or interacted drug pairs from these paragraphs. 
                        Return your result starting with the drug name and : like (drug: AE1, AE2, ...). Here is the input: 
                     '''
        
        example = request.POST.get('example')
        if example == "1":
            query = '''
            Diarrheal illness in the USA is a significant contributor to adverse morbidity in children and has a major impact economically, including the utilization of healthcare resources. Viral and bacterial pathogens account for the majority of cases that have an infectious cause; however, intestinal protozoan parasites are important but often under-recognized etiologic agents for infectious diarrhea. Cryptosporidium spp. and Giardia lamblia are the most common intestinal protozoal infections in both resource-limited and resource-abundant countries and predominately affect children, usually those between ages 1–9 years and most often in children less than 4 years of age. Both Cryptosporidium and Giardia are ubiquitous in the environment and transmit primarily through the fecal-oral route after ingestion of oocysts/cysts in contaminated water or food or direct person-to-person contact. Both are environmentally hardy. The chlorine-tolerant Cryptosporidium oocysts in particular have led to more diarrheal outbreaks due to treated recreational water exposure than any other pathogen. Despite notifiable diseases in the USA, reporting is very low and thus general awareness of epidemiology and clinical manifestations is limited. Underdiagnosis can further contribute to under-reporting, especially in asymptomatic patients and where specialty consultation and reliable diagnostics are absent. Once a diagnosis of cryptosporidiosis or giardiasis has been confirmed, in addition to appropriate case reporting and treatment considerations, it is essential to provide educational support to children and their parents or caregivers to prevent further transmission of the disease within the household and throughout the community.
            '''
        elif example == "2":
            query = '''
            Molecular hybridization approach is an emerging tool in drug discovery for designing new pharmacophores with biological activity. A novel, new series of coumarin-benzimidazole hybrids were designed, synthesized and evaluated for their broad spectrum antimicrobial activity. Among all the synthesized molecules, compound (E)-3-(2-1H-benzo[d]imidazol-1-yl)-1-((4-chlorobenzyl)oxy)imino)ethyl)-2H-chromen -2-one showed the most promising broad spectrum antibacterial activity against Pseudomonas aeruginosa, Staphylococcus aureus, Bacillus subtilis and Proteus vulgaris. In addition, it has showed no cytotoxicity and hemolysis at 10 times the MIC concentration. SAR studies indicate that position of the chlorine atom in the hybrid critically determines the antibacterial activity.
            '''
        else:
            query = request.POST.get('text')
        
        response = AE_annotation_chatGPT(prompt, query)
        
        final_response = re.split(r'\|', response['choices'][0]['message']['content'])
        
        context = {'prompt':prompt, 'query':query, 'response':final_response}
    
        return render(request, "aefinder.html", context)
    
    else:
        return render(request, "aefinder.html")
    
