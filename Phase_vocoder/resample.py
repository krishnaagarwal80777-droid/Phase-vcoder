import numpy as np 
def resample(signal,pitchRatio):
    outputlen= int((len(signal)-1)/pitchRatio) #The -1 ensures that when performing linear interpolation using signal[ix+1], we never exceed the valid index range of the input signal.
    output=np.zeros(outputlen)
    for i in range (outputlen-1):
        x=float(i*pitchRatio)
        x1=int(np.floor(x))
        dx=x-x1
        output[i]=signal[x1]*(1.0-dx)+signal[x1+1]*dx #interpolation as if the output index lie between x and x+1 then output will have contribution of both x and x+1
    return output
