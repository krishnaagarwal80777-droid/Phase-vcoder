def pitchshift(wavfile,pitch_ratio,mode):
    import wave 
    import pyaudio
    import struct
    import time 
    import numpy as np
    from peak import locate_peaks
    from resample import resample 
    import os
    
    wf=wave.open(wavfile,'rb')

    channel=wf.getnchannels()
    Fs=wf.getframerate()
    signal_length=wf.getnframes()
    width=wf.getsampwidth()
    if channel>1:
        print ("multichannel not allowed.")
        return
    
    window_size=2048
    synthesis_hop=int(window_size//4)
    analysis_hop = max(1, int(synthesis_hop / pitch_ratio))


    delta_pahse=np.zeros(window_size//2 +1)
    syn_phase=np.zeros(window_size//2 +1, dtype=complex)

    k=np.linspace(0,window_size//2,window_size//2+1)
    last_phase=np.zeros(window_size//2+1)
    accum_phase=np.zeros(window_size//2+1)
    current_frame=np.zeros(window_size//2+1)
    expected_phase=2*np.pi*k*analysis_hop/window_size


    window = np.hanning(window_size)

    
    indata  = np.zeros(4*analysis_hop+window_size)
    indata[0:window_size] = np.array(struct.unpack('h'*window_size,wf.readframes(window_size)))
    indata[window_size:] = np.array(struct.unpack('h'*4*analysis_hop,wf.readframes(4*analysis_hop)))
     
    blocksize=window_size+synthesis_hop
    pk_indices = list(range(window_size//2 + 1))
    outbuffer=np.zeros(4*synthesis_hop+window_size)
    zero_pad=np.zeros(blocksize)
    dataout= b''
    amp_max=2**15-1
    N = window_size // 2 + 1

    for i in range((signal_length-window_size)//(4*analysis_hop)):
        write_pt=0
        read_pt=0
        while read_pt + window_size <= len(indata):

            current_frame=np.fft.rfft(window*indata[read_pt:window_size+read_pt])
            current_phase=np.angle(current_frame)
            current_mag=abs(current_frame)
            delta_pahse=current_phase-last_phase
            last_phase=np.copy(current_phase)

            delta_pahse-=expected_phase
            delta_pahse=np.unwrap(delta_pahse)

            accum_phase[pk_indices] = accum_phase[pk_indices] + (delta_pahse[pk_indices] + expected_phase[pk_indices])*synthesis_hop/analysis_hop

            rot_phase= accum_phase[pk_indices]-current_phase[pk_indices]
            start_p=0

             
            for k2 in range(len(pk_indices)-1):
                peak = pk_indices[k2]
                next_peak = pk_indices[k2+1]
                end_point = int((peak + next_peak)//2)+1
                ri_indices = list(range(start_p,peak))+ list(range(peak+1,end_point))
                accum_phase[ri_indices] = rot_phase[k2] + current_phase[ri_indices]
                start_p = end_point

            ri_indices = list(range(start_p,next_peak))
            accum_phase[ri_indices] = rot_phase[len(pk_indices)-1] + current_phase[ri_indices]
            pk_indices=locate_peaks(current_mag)
         
            if len(pk_indices) == 0:
                pk_indices = [1]

            syn_phase.real,syn_phase.imag=np.cos(accum_phase),np.sin(accum_phase)

            outbuffer[write_pt:write_pt+window_size]+=window*np.fft.irfft(current_mag*syn_phase)
            read_pt+=analysis_hop
            write_pt+=synthesis_hop
        outframe=outbuffer[0:blocksize]
        outframe[outframe>amp_max]=amp_max
        outframe = np.int16(np.clip(outframe, -amp_max, amp_max))
        dataout += struct.pack('h'*len(outframe), *list(outframe))

        
        outbuffer= np.concatenate((outbuffer[blocksize:],zero_pad))
        indata[0:window_size-analysis_hop] = np.copy(indata[read_pt:])
        next_frame = wf.readframes(5*analysis_hop)

        if len(next_frame)<10*analysis_hop:
            pad=np.zeros(5*analysis_hop-len(next_frame)//2)
            pad = np.int16(pad)
            pad=struct.pack('h'*len(pad),*list(pad))
            next_frame=next_frame+pad
        indata[window_size-analysis_hop:]=np.array(struct.unpack('h'*5*analysis_hop,next_frame))

    if mode == "tune" :
        if  abs(pitch_ratio - 1.0) > 1e-6:
         sample_length=len(dataout)//2
         resamp=np.int16(resample(np.array(struct.unpack('h'*sample_length,dataout)),pitch_ratio))
         output_data=struct.pack('h'*len(resamp),*list(resamp))
        else:
            output_data = dataout
    
    elif mode=="stretch":
        output_data= dataout
        


    name, ext = os.path.splitext(wavfile)

    if mode == "tune":
     output_wavefile = name + "_tuned" + ext
    elif mode == "stretch":
     output_wavefile = name + "_stretched" + ext

    print("writting to file after strect/tunning")
    wf1=wave.open(output_wavefile,'w')
    wf1.setnchannels(1)
    wf1.setsampwidth(width)
    wf1.setframerate(Fs)
    wf1.writeframes(output_data)
    wf1.close()

    time.sleep(0.1)


    wf2=wave.open(output_wavefile,'rb')

        #callback function for audio playing 
        
    def callback(input_string,block_size,time_info,status):
        output_string=wf2.readframes(block_size)
        return(output_string,pyaudio.paContinue)
    p2=pyaudio.PyAudio()
    stream=p2.open(format=p2.get_format_from_width(width),
                     channels=1,
                       rate=Fs,
                       input=False,
                       output=True,
                       frames_per_buffer=1024,
                       stream_callback=callback)
    print("playing now")
    stream.start_stream()
    while stream.is_active():
           time.sleep(0.1)
    stream.stop_stream()
    print("done and dusted")

    stream.close()
    p2.terminate()


        