"""Regenerate entirely fictional fixtures and the original demonstration PDF."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from workflow.core import COLORS,render_annotations
from workflow.cli import default_config
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
root=Path(__file__).resolve().parents[1]
base={'key':'PAPER001','data':{'itemType':'journalArticle','title':'A small experiment in careful reading','citationKey':'exampleReading2026',
    'creators':[{'firstName':'Alex','lastName':'Example','creatorType':'author'}],'date':'2026','DOI':'',
    'publicationTitle':'Fictional demonstration — not scientific evidence','collections':['DEMO0002'],'tags':[{'tag':'reading/unread'},{'tag':'🌱 origin/personal'}]}}
attachment={'key':'PDF00001','data':{'itemType':'attachment','parentItem':'PAPER001','contentType':'application/pdf','title':'Original demonstration PDF'}}
items=[base,attachment,{'key':'PURPOSE1','data':{'itemType':'note','parentItem':'PAPER001','note':'<p>This fictional document helps me learn the annotation workflow. #method/useful</p>'}},
 {'key':'ATTNOTE1','data':{'itemType':'note','parentItem':'PDF00001','note':'<p>These notes concern this attachment only.</p>'}},
 {'key':'PAPER002','data':{'itemType':'journalArticle','title':'A second fictional paper without annotations','citationKey':'exampleUnmarked2026','collections':['DEMO0001'],'tags':[]}}]
comments=['Context for this exercise.','The result is a demonstration only.','A definition in my own words.','Try this reading method. #method/useful','What would count as better evidence? #question/open','Connect this to a project. #idea/project','Read the next section. #read/next','Remember this distinction. #card/candidate']
for i,(color,(name,meaning)) in enumerate(COLORS.items()):
    items.append({'key':f'ANNOT{i:03d}','data':{'itemType':'annotation','parentItem':'PDF00001','annotationType':'highlight' if i%2 else 'note',
        'annotationColor':color,'annotationText':'This document is a synthetic example, not a scientific paper.' if i%2 else '',
        'annotationComment':comments[i],'annotationPageLabel':'1','annotationSortIndex':f'{i:05d}',
        'annotationPosition':json.dumps({'pageIndex':0,'rects':[[50,50,200,70]]}),'tags':[{'tag':'Knowledge'}] if i==0 else []}})
fixture={'collections':[{'key':'DEMO0001','data':{'name':'Reading Library'}},{'key':'DEMO0002','data':{'name':'Example Topic','parentCollection':'DEMO0001'}}],
 'items':items,'files':{'PDF00001':'examples/demonstration.pdf'}}
(root/'examples/library.json').write_text(json.dumps(fixture,ensure_ascii=False,indent=2)+'\n')
(root/'config.example.json').write_text(json.dumps(default_config(),ensure_ascii=False,indent=2)+'\n')
c=canvas.Canvas(str(root/'examples/demonstration.pdf'),pagesize=(612,792),invariant=1)
c.setTitle('A small experiment in careful reading');c.setAuthor('Zotero–Obsidian Workflow contributors')
c.setFillColor(HexColor('#173B42'));c.rect(0,674,612,118,fill=1,stroke=0)
c.setFillColor(HexColor('#FFFFFF'));c.setFont('Helvetica-Bold',22);c.drawString(46,738,'A small experiment in careful reading')
c.setFont('Helvetica',11);c.drawString(46,712,'Original demonstration document | Fictional content | Page 1')
y=635
sections=[('Overview','This document is a synthetic example, not a scientific paper.'),
 ('Methods','The fictional reader grouped eight annotations by color and reviewed them.'),
 ('Results','Eight color groups were represented in the demonstration.'),
 ('Limitations','No people were studied and no scientific conclusions can be drawn.')]
for title,body in sections:
 c.setFillColor(HexColor('#173B42'));c.setFont('Helvetica-Bold',14);c.drawString(46,y,title)
 c.setFillColor(HexColor('#25313A'));c.setFont('Helvetica',10);c.drawString(46,y-24,body);y-=87
c.setFillColor(HexColor('#567277'));c.setFont('Helvetica',10);c.drawString(46,218,'Try a highlight, a sticky note, and a paper-level child note in Zotero.')
c.drawString(46,198,'Use the reading guide to choose colors and tags. Keep your own comments separate.')
c.line(46,90,566,90);c.drawString(46,70,'MIT-licensed example. This file contains no personal notes or third-party paper text.')
c.save()
