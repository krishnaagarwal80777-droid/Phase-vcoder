import numpy as np

def locate_peaks(signal):
    k = 2
    indices =[]
    while k<len(signal)-2:
     seg=signal[k-2:k+3]
     if np.amax(seg)<150:
        k=k+2
     else:
        if seg.argmax()==2:
           indices.append(k)
           k=k+2
     k=k+1
    return indices