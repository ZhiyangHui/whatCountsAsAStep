"""Build the service section from paired case-level outputs and logged vote offsets."""
from collections import Counter
from pathlib import Path
import argparse
from audit_extended import read,credit,ci
def make(rows,path,preview):
 rs=[r for r in rows if r['ds']=='TauService'];pair=[r for r in rs if 'CHIEF' in r['pred']]
 assert len(pair)==399
 def scores(sub,method):
  return [sum(credit(r,r['pred'][method],k) for r in sub) for k in ('exact','group','turn','near')]
 show=[]
 for m,tag in [('CHIEF','CHIEF archive'),('Qwen14','Local Qwen3-14B'),('Combined','Combined probe'),('Symptom','Symptom cue')]:
  sub=[r for r in pair if m in r['pred']]
  if not preview:assert len(sub)==399
  s=scores(sub,m);valid=sum(0<=r['pred'][m]<len(r['roles']) for r in sub)
  show.append(' & '.join(map(str,[tag,len(sub),valid,*s]))+r'\\')
 marked=[r for r in rs if 'Qwen14' in r['pred']];ns=len(marked);all_scores=scores(marked,'Qwen14')
 valid=[r for r in marked if 0<=r['pred']['Qwen14']<len(r['roles'])]
 by=Counter(r['roles'][r['pred']['Qwen14']] for r in valid)
 pq=[r for r in pair if 'Qwen14' in r['pred']];e,x,t,_=scores(pq,'Qwen14')
 gs=[credit(r,r['pred']['Qwen14'],'turn')-credit(r,r['pred']['Qwen14'],'exact') for r in pq]
 lo,hi=ci(pq,gs)
 text=r"""
\begin{table}[htbp]\centering
\begin{tabular}{lrrrrrr}\toprule
Method & $n$ & Valid & Exact & Tool call & Service turn & Within one\\\midrule
""" + '\n'.join(show)+r"""\bottomrule
\end{tabular}
\caption{Paired service results. Valid counts predictions mapped to an original event. A missing or invalid prediction receives zero across all score columns.}\label{tab:service}
\end{table}

CHIEF has 107 exact hits and 107 call-group hits (Table~\ref{tab:service}). The reference call group has multiple records on 82 of the 399 traces. Nevertheless, the identical CHIEF counts follow from the assistant-only candidate space. Each call group contains at most one assistant action, so a wrong assistant action can never be rescued by a tool response in its group. Under wider service turns, CHIEF gains 53 hits (13.3 points [10.0, 16.8]). """
 text+=f"Local Qwen returned {by['tool']} tool selections among {len(valid)} valid outputs on {ns} runs. On the paired cohort it gains {x-e} hits under call grouping and {t-e} under service-turn grouping ({100*sum(gs)/len(pq):.1f} points [{lo:.1f}, {hi:.1f}]). Across all {ns} local cases the exact, call-group and turn counts are {all_scores[0]}, {all_scores[1]} and {all_scores[2]}. "
 text+=r"""A gap between these rules quantifies a difference in eligible neighboring actions and in the time span of the nominated interaction.

\begin{table}[htbp]\centering
\begin{tabular}{lrrr}\toprule
Reference resolution & Unanimous traces & Agreeing vote pairs & Trace mean (\%)\\\midrule
Exact record &348 / 400&1,074 / 1,190&91.3\\
Tool-call group &348 / 400&1,074 / 1,190&91.3\\
Service turn &358 / 400&1,100 / 1,190&93.2\\\bottomrule
\end{tabular}
\caption{Agreement among existing service annotations. The last column gives equal weight to every trace, first averaging all unordered vote pairs within that trace.}\label{tab:votes}
\end{table}
\paragraph{Human disagreement.} Every service run has at least two votes on its reference. The released data have two votes on 14 runs, three on 380 and four on six. Of 52 exact-disagreement traces, ten become unanimous under service-turn scoring (six airline, four retail). The narrower call groups make none unanimous. Thus a wider rule can conceal differences in which assistant decision the annotators selected. Agreement concerns released votes and need not measure agreement of unaided independent annotators.
"""
 path.write_text(text)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('frozen');p.add_argument('path',type=Path);p.add_argument('--preview',action='store_true');a=p.parse_args();make(read(a.frozen),a.path,a.preview)
