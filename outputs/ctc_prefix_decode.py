"""Lexicon-free CTC prefix beam decoder; inputs are log probabilities, blank=0."""
import numpy as np


def decode(log_probs, width=10):
    if width<1:raise ValueError('Beam width must be positive')
    beam={(): (0.,-np.inf)}
    for row in log_probs:
        next_beam={}
        def add(prefix, blank=-np.inf, nonblank=-np.inf):
            a,b=next_beam.get(prefix,(-np.inf,-np.inf))
            next_beam[prefix]=(np.logaddexp(a,blank),np.logaddexp(b,nonblank))
        for prefix,(pb,pn) in beam.items():
            total=np.logaddexp(pb,pn)
            add(prefix,blank=total+row[0])
            for c in range(1,len(row)):
                if prefix and c==prefix[-1]:
                    add(prefix,nonblank=pn+row[c])
                    add(prefix+(c,),nonblank=pb+row[c])
                else:add(prefix+(c,),nonblank=total+row[c])
        beam=dict(sorted(next_beam.items(),key=lambda item:np.logaddexp(*item[1]),reverse=True)[:width])
    return max(beam,key=lambda p:np.logaddexp(*beam[p]))
