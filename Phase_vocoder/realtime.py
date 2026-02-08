# realtimePV.py
running = False

def realtimePitchshift(pitch_ratio):
    global running
    running = True

    import pyaudio
    import numpy as np
    import struct
    from peak import locate_peaks
    from resample import resample

    Fs = 16000
    window_size = 2048
    synthesis_hop = window_size // 4
    analysis_hop = max(1, int(synthesis_hop / pitch_ratio))

    win = np.hanning(window_size)
    k = np.linspace(0, window_size//2, window_size//2 + 1)
    expected_phase = 2*np.pi*k*analysis_hop/window_size

    last_phase  = np.zeros(window_size//2 + 1)
    accum_phase = np.zeros(window_size//2 + 1)
    syn_phase   = np.zeros(window_size//2 + 1, dtype=complex)

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=Fs,
                    input=True,
                    output=True,
                    frames_per_buffer=analysis_hop)

    indata = np.zeros(4*analysis_hop + window_size)
    outbuf = np.zeros(4*synthesis_hop + window_size)
    zero   = np.zeros(window_size + synthesis_hop)

    indata[:window_size] = np.frombuffer(stream.read(window_size), np.int16)
    indata[window_size:] = np.frombuffer(stream.read(4*analysis_hop), np.int16)

    pk_indices = list(range(window_size//2 + 1))
    dataout = b''

    while running:
        read_pt = write_pt = 0

        while read_pt + window_size <= len(indata):
            frame = np.fft.rfft(win * indata[read_pt:read_pt+window_size])
            mag = np.abs(frame)
            phase = np.angle(frame)

            delta = phase - last_phase
            last_phase = phase.copy()
            delta -= expected_phase
            delta = np.unwrap(delta)

            accum_phase[pk_indices] += \
                (delta[pk_indices] + expected_phase[pk_indices]) * synthesis_hop / analysis_hop

            rot = accum_phase[pk_indices] - phase[pk_indices]
            start = 0
            for i in range(len(pk_indices)-1):
                p1, p2 = pk_indices[i], pk_indices[i+1]
                end = (p1 + p2)//2
                accum_phase[start:end] = rot[i] + phase[start:end]
                start = end

            pk_indices = locate_peaks(mag) or [1]

            syn_phase.real = np.cos(accum_phase)
            syn_phase.imag = np.sin(accum_phase)

            outbuf[write_pt:write_pt+window_size] += \
                win * np.fft.irfft(mag * syn_phase)

            read_pt += analysis_hop
            write_pt += synthesis_hop

        block = outbuf[:window_size+synthesis_hop]
        block = np.clip(block, -32768, 32767).astype(np.int16)
        dataout += block.tobytes()

        outbuf = np.concatenate((outbuf[window_size+synthesis_hop:], zero))
        indata[:window_size-analysis_hop] = indata[read_pt:]
        indata[window_size-analysis_hop:] = \
            np.frombuffer(stream.read(5*analysis_hop), np.int16)

        if len(dataout)//2 > Fs//2:
            samples = np.frombuffer(dataout, np.int16)
            resamp = resample(samples, pitch_ratio)
            stream.write(resamp.astype(np.int16).tobytes())
            dataout = b''

    stream.stop_stream()
    stream.close()
    p.terminate()


def stop():
    global running
    running = False