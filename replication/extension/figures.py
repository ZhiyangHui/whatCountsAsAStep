"""Render manuscript vector figures directly from the frozen scoring tables."""
import argparse,csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch,Rectangle
from audit_extended import read
navy='#174763';orange='#C76526';teal='#147D73';dark='#25343C'
def table(p):
 with open(p) as f:return list(csv.DictReader(f))
def produce(data,results,legacy,dest):
 dest.mkdir(exist_ok=True,parents=True)
 plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'text.color':dark,'axes.labelcolor':dark,'pdf.fonttype':42})
 def save(fig,name):
  fig.savefig(dest/(name+'.pdf'),bbox_inches='tight',pad_inches=.07);plt.close(fig)
 # Shared question, two genuinely different executions.
 q='24310552f92bd242c7ed3d0f'
 pair=sorted((r for r in read(data) if r['q']==q and r['ds']=='ElephantTeam'),key=lambda r:r['domain'])
 assert len(pair)==2
 fig,ax=plt.subplots(figsize=(6.4,1.95));maxlen=max(len(r['roles']) for r in pair)
 for row,y,label in zip(pair,[1,0],['CaptainAgent','Magentic-One']):
  roles=row['roles'];g=row['g'];pred=row['pred']['Combined']
  for j,role in enumerate(roles):
   start=row['turn'][j]
   ax.add_patch(Rectangle((j-.46,y-.16),.92,.32,facecolor=('#8BC7BD' if start==row['turn'][g] else '#D9E1E5'),edgecolor='none'))
   if j==start:ax.plot([j-.49,j-.49],[y-.2,y+.2],color='#667984',lw=.75)
  ax.plot(g,y+.23,marker='v',color=orange,ms=6);ax.plot(pred,y-.24,marker='^',color=navy,ms=6)
 ax.set_xlim(-.8,maxlen-.3);ax.set_ylim(-.53,1.58);ax.set_yticks([0,1],['Magentic-One','CaptainAgent']);ax.tick_params(axis='y',length=0);ax.spines['left'].set_visible(False)
 ax.set_xticks(range(0,maxlen,3),[str(i+1) for i in range(0,maxlen,3)]);ax.set_xlabel('Published step ID')
 ax.legend(handles=[Line2D([],[],marker='v',ls='',color=orange,label='Annotated step'),Line2D([],[],marker='^',ls='',color=navy,label='Predicted step'),Patch(facecolor='#8BC7BD',label='Reference speaker turn')],ncol=3,loc='lower center',bbox_to_anchor=(.5,.95),frameon=False,fontsize=8.5)
 save(fig,'case')
 summary=[r for r in table(legacy) if r['scope']=='All']
 fig,ax=plt.subplots(figsize=(6.25,2.4));yy=np.arange(4)
 for i,r in enumerate(summary):
  obs=int(r['exchange'])-int(r['record']);chance=float(r['chance']);adj=int(r['adjacent'])
  ax.hlines(i,0,adj,color='#C6D2D7',lw=2);ax.scatter(adj,i,s=42,facecolor='white',edgecolor='#6B7982',zorder=3)
  ax.scatter(chance,i+.09,s=40,marker='D',color=orange,zorder=3);ax.scatter(obs,i-.09,s=43,color=teal,zorder=4)
 ax.set_yticks(yy,['CHIEF','Qwen3-14B','Bayes','Cue']);ax.invert_yaxis();ax.set_xlim(-2,55)
 ax.set_xlabel('Number of traces');ax.grid(axis='x',alpha=.15)
 ax.legend(handles=[Line2D([],[],marker=x,ls='',color=c,markerfacecolor=f,label=n) for x,c,f,n in [('o',teal,teal,'Observed gains'),('D',orange,orange,'Expected at random'),('o','#6B7982','white','All adjacent misses')]],ncol=3,loc='lower center',bbox_to_anchor=(.5,1),fontsize=8.5,frameon=False)
 save(fig,'boundaries')
 # The same prediction arrays, evaluated once per reference definition.
 refs=table(results/'multi_reference_contrasts.csv')
 fig,axes=plt.subplots(1,2,figsize=(6.4,2.35),sharey=True,layout='constrained')
 for ax,first,title in zip(axes,['CHIEF','Bayes'],['CHIEF minus local Qwen','Bayes minus Cue']):
  ax.axhline(0,color='#77848B',lw=.8,ls='--')
  for scoring,color,marker,lab in [('orig',navy,'o','Original decisive step'),('readers',orange,'s','Three-reader mean')]:
   vs=[float(next(x['gap_pp'] for x in refs if x['first']==first and x['score']==scoring and x['rule']==rule)) for rule in ['exact','group']]
   ax.plot([0,1],vs,color=color,marker=marker,label=lab)
   for x,v in enumerate(vs):ax.annotate(f'{v:+.1f}',(x,v),xytext=(0,6 if scoring=='readers' else -12),textcoords='offset points',ha='center',fontsize=8,color=color)
  ax.set_xlim(-.25,1.25);ax.set_ylim(-8,30);ax.set_xticks([0,1],['Exact','Exchange']);ax.set_title(title,fontsize=11)
 axes[0].set_ylabel('Score gap (points)');axes[1].legend(fontsize=7.5,frameon=False,loc='upper right')
 save(fig,'references')
 expo=table(results/'exposure.csv');scores=table(results/'scores.csv')
 groups=[('WhoWhen','Algorithm-Generated','Algorithm-generated'),('WhoWhen','Hand-Crafted','Hand-crafted'),('ElephantTeam','captain-runs-gaia','Captain / GAIA'),('ElephantTeam','captain-runs-assistantbench','Captain / AssistantBench'),('ElephantTeam','magentic-runs-gaia','Magentic / GAIA'),('ElephantTeam','magentic-runs-assistant-bench','Magentic / AssistantBench'),('ElephantSWE','ALL','SWE-agent'),('TauService','airline','Airline'),('TauService','retail','Retail')]
 fig,(ax,bx)=plt.subplots(1,2,figsize=(7.4,3.55),sharey=True,gridspec_kw={'width_ratios':[1.05,1]},layout='constrained')
 colors=['#DAE3E7','#92C6C0','#408E92','#184E63']
 for j,(ds,d,label) in enumerate(groups):
  r=next(v for v in expo if (v['ds'],v['domain'],v['rule'])==(ds,d,'turn'));start=0
  for col,color in zip(('single','two','three_four','five_plus'),colors):
   val=100*float(r[col])/int(r['n']);ax.barh(j,val,left=start,color=color,height=.59);start+=val
  s=next(v for v in scores if (v['ds'],v['domain'],v['rule'],v['method'])==(ds,d,'turn','Combined'));v=float(s['gain_pp']);bx.hlines(j,float(s['lo']),float(s['hi']),color=navy,lw=1.35);bx.scatter(v,j,s=30,color=teal,zorder=3)
 ax.set_yticks(range(len(groups)),[g[2] for g in groups],fontsize=8);ax.invert_yaxis();ax.set_xlim(0,100);bx.set_xlim(-2,104)
 ax.set_title('A   Reference group width',loc='left',fontsize=10);bx.set_title('B   Additional hits',loc='left',fontsize=10)
 ax.set_xlabel('Share of traces (%)');bx.set_xlabel('Percentage points (95% interval)');bx.grid(axis='x',alpha=.18)
 ax.legend(handles=[Patch(facecolor=c,label=l) for c,l in zip(colors,('1','2','3–4','5+'))],ncol=4,loc='upper center',bbox_to_anchor=(.5,-.19),fontsize=8,frameon=False,columnspacing=1)
 save(fig,'exposure')
 fig,ax=plt.subplots(figsize=(6.35,2.7));bb=table(results/'budget.csv')
 for ds,label,c,m in [('TauService','Service turn',orange,'^'),('ElephantTeam','Team speaker',teal,'o'),('WhoWhen','Who&When speaker',navy,'s'),('ElephantSWE','SWE tool name','#786689','D')]:
  r=next(x for x in bb if (x['ds'],x['domain'],x['method'],x['rule'])==(ds,'ALL','Combined','turn'))
  v=[float(r['budget'+str(i)]) for i in (1,2,4,8,16)]+[100*int(r['group_hits'])/int(r['n'])]
  ax.plot(range(6),v,marker=m,ms=4,color=c,label=label,lw=1.55)
 ax.set_xticks(range(6),['1','2','4','8','16','All']);ax.set_ylabel('Expected reference recovery (%)');ax.set_xlabel('Records inspected within the nominated group');ax.set_ylim(8,51);ax.grid(axis='y',alpha=.2)
 ax.legend(ncol=2,fontsize=8.5,loc='lower right',frameon=False)
 save(fig,'budget')
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for name in ['data','results','legacy','dest']:p.add_argument(name,type=Path)
 a=p.parse_args();produce(a.data,a.results,a.legacy,a.dest)
