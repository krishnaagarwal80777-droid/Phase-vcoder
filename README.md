# Phase-vcoder
# Phase Vocoder Pitch Shifting Project

## 1. Project Overview

This project implements a **Phase Vocoder–based pitch shifting system**, designed and built from scratch as part of a deep exploration into **digital signal processing (DSP)** concepts. The system supports **offline pitch shifting** of audio files as well as **real-time pitch shifting** using streaming audio input.

The core motivation behind this project is to **change the pitch of an audio signal without changing its duration**, something that cannot be achieved by naïve time-domain techniques. The project dives deeply into *why* frequency-domain processing is required, *how* phase plays a critical role in pitch perception, and *what* trade-offs arise when different pitch-shifting methods are used.

This README consolidates **all major technical discussions, design decisions, limitations, and alternatives** that were explored throughout the project.

---

## 2. Problem Statement: Why Pitch Shifting Is Non‑Trivial

Pitch is fundamentally tied to **frequency content**, not just waveform shape. A simple time-domain trick such as speeding up or slowing down an audio signal:

* Changes **both pitch and duration** simultaneously
* Cannot independently control pitch

### Naïve Approach (What Does NOT Work)

1. Stretch signal in time
2. Resample to original length

This causes:

* Phase discontinuities
* Audible artifacts
* Loss of spectral coherence

To truly decouple **pitch** from **time**, we must work in the **frequency domain**.

---

## 3. Why FFT and Frequency Analysis Are Necessary

The interviewer-style question addressed during this project:

> *"If pitch can be changed by time stretching and resampling, why do we need FFT at all?"*

### Answer:

Pitch is encoded in **frequency peaks and their phase evolution over time**. FFT allows us to:

* Observe **individual frequency bins**
* Track how frequencies **move across frames**
* Maintain **phase continuity**, which is essential for natural sound

Without FFT:

* You cannot distinguish overlapping frequencies
* Harmonic relationships are destroyed
* Output becomes noisy or metallic

---

## 4. Core Method Used: Phase Vocoder

### 4.1 High-Level Pipeline

1. Convert audio file (WAV/MP3) → discrete-time signal
2. Frame the signal using overlapping windows
3. Apply windowing function (Hann)
4. Compute FFT (STFT)
5. Extract magnitude and phase
6. Estimate true frequencies using phase differences
7. Modify frequencies for pitch shifting
8. Reconstruct phase coherently
9. Apply inverse FFT
10. Overlap-add frames

---

### 4.2 Why STFT (Short-Time Fourier Transform)

Audio signals are **non-stationary**. STFT allows us to:

* Analyze short time slices where signal is approximately stationary
* Preserve temporal evolution of phase

Key parameters:

* Frame size (N)
* Hop size (H)
* Window function

Trade-off:

* Larger N → better frequency resolution
* Smaller N → better time resolution

---

## 5. Phase: The Most Important Concept in This Project

Magnitude tells *what frequencies exist*.

Phase tells *where the waveform is in time*.

### Why Phase Matters

If phase is ignored:

* Harmonics drift
* Transients smear
* Sound becomes robotic or watery

### Phase Accumulation

The vocoder estimates **instantaneous frequency**:

ω_true = ω_bin + Δφ / Δt

This preserves:

* Harmonic locking
* Natural pitch perception

---

## 6. Pitch Shifting Strategy Used

Pitch shifting factor = α

We do:

* Frequency scaling in the spectral domain
* Time correction using resampling

This allows:

* Pitch change without duration change

Why this works:

* Pitch change = frequency scaling
* Duration preservation handled separately

---

## 7. Alternative Pitch Shifting Methods Compared

This section explains **in depth** what actually went wrong (both theoretically and practically) when alternative methods were implemented or discussed during the project, and *why their artifacts appear*, not just that they appear.

---

### 7.1 Bin-Based Method (Naïve FFT Bin Shifting)

#### What the Bin Method Assumes

In the bin-based approach, **each FFT bin is implicitly treated as an independent sinusoid**:

* One bin → one fixed-frequency sine wave
* Magnitude and phase of each bin are processed independently
* Bins are shifted or reindexed to change pitch

This assumption is **fundamentally incorrect** for real signals.

---

#### What Actually Happens in Real Signals

A real sinusoid **does not live in one FFT bin** unless:

* Its frequency exactly matches a bin center
* The window length is infinite (which never happens)

Instead:

* One sinusoid spreads energy across **multiple neighboring bins** (spectral leakage)
* These bins together represent **one physical sinusoid**

When we treat each bin independently, we destroy this relationship.

---

#### Core Problem 1: Phase Discontinuity Across Frames

In the bin method:

* Phase is copied or shifted directly from bin to bin
* No attempt is made to track **phase evolution over time**

Result:

* Phase at frame *n* has no coherent relationship with phase at frame *n+1*
* Instantaneous frequency becomes undefined

Audible effect:

* Buzzing
* Metallic noise
* Grainy textures

This is because **human hearing is extremely sensitive to phase continuity**, especially for harmonic sounds.

---

#### Core Problem 2: Harmonic Destruction

Harmonics are **locked together** in real sounds:

* If the fundamental shifts, all harmonics shift proportionally

In bin shifting:

* Harmonics fall into unrelated bins
* Integer harmonic ratios are broken

Result:

* Inharmonic spectrum
* Bell-like or robotic tones

This is one of the main reasons the output sounded "unnatural" during early experiments.

---

#### Core Problem 3: Magnitude–Phase Mismatch

Magnitude may appear correct visually, but:

* Phase no longer matches the new frequency location
* Inverse FFT reconstructs a waveform that was never physically possible

This creates:

* Time-domain ringing
* Smearing of transients

---

#### Summary: Why the Bin Method Failed

 Treats bins as physical sinusoids (they are not)
 Ignores phase evolution
 Breaks harmonic relationships
 Produces severe artifacts

This method is fast and simple but **fundamentally flawed for pitch shifting**.

---

### 7.2 Sinusoidal Model (Peak Tracking Method)

The sinusoidal model attempts to fix exactly what the bin method breaks.

---

#### Core Idea

Instead of treating bins independently:

* Detect **spectral peaks** (true sinusoids)
* Track each peak across frames
* Estimate frequency, amplitude, and phase trajectories

Mathematically, the signal is modeled as:

x(t) = Σ A_k(t) cos(φ_k(t))

This aligns much more closely with physical reality.

---

#### Why This Method Works Better

 One sinusoid = one tracked entity
 Phase continuity is preserved
 Harmonics remain locked
 Frequency estimates are accurate

This is why sinusoidal modeling often produces **extremely clean pitch shifting** for simple signals.

---

#### What Goes Wrong in Practice

Despite its elegance, several problems arise.

---

#### Problem 1: Peak Detection Is Fragile

* Peaks merge and split
* Noise creates false peaks
* Windowing affects peak location

This causes:

* Missed partials
* Sudden frequency jumps

---

#### Problem 2: Peak Matching Across Frames

To maintain continuity, peaks must be matched frame-to-frame.

Challenges:

* Peaks cross in frequency
* Harmonics overlap
* Partial disappearance and reappearance

Incorrect matching leads to:

* Phase jumps
* Audible clicks
* Pitch instability

---

#### Problem 3: Dense and Polyphonic Signals

For signals like:

* Vocals
* Chords
* Noise-rich instruments

The spectrum becomes too dense:

* Peaks are not well separated
* Model assumptions break down

This causes:

* Tracking failure
* Warbling artifacts

---

#### Problem 4: Computational Complexity

Compared to phase vocoder:

* Peak detection
* Interpolation
* Matching logic

All add significant computational cost, making **real-time implementation difficult**.

---

#### Summary: Strengths and Weaknesses of the Sinusoidal Model

 Excellent quality for monophonic, harmonic sounds
 Physically meaningful model

 Fragile peak tracking
 Complex implementation
 Poor scalability to dense spectra

---

### 7.2 Sinusoidal Model (Peak Tracking)

#### Method

* Detect spectral peaks
* Track sinusoids over time
* Resynthesize signal

#### Advantages

* Very high quality for monophonic signals
* Excellent harmonic preservation

#### Disadvantages

* Computationally expensive
* Complex peak matching logic
* Poor performance for dense spectra

#### Verdict

 Best for analysis, not real-time simplicity

---

### 7.4 Why Phase Vocoder Was Chosen

 Works for polyphonic signals
 Conceptually rigorous
 Frequency-accurate
 Scales to real-time systems

---

## 8. Real-Time Implementation Challenges

* FIFO buffering
* Frame synchronization
* Latency control
* Phase continuity across buffers

Special care taken to:

* Decouple audio input buffer size from FFT frame size
* Maintain overlap-add consistency

---

## 9. Why It Sounds Good for Some Signals and Bad for Others

### Works Best For:

* Pure sine waves
* Guitar strings
* Whistles
* Flutes
* Slowly varying harmonic signals

### Sounds Robotic For:

* Vocals
* Speech
* Percussive sounds

---

## 10. Why Vocals Sound Robotic

### Root Causes

1. **Formants are not preserved**
2. Phase vocoder treats harmonics independently
3. Transients are smeared
4. Phase locking is incomplete

Speech has:

* Rapid spectral envelope changes
* Strong formant structure
* Non-sinusoidal excitation

The vocoder violates these assumptions.

---

## 11. Known Fixes and Improvements for Vocals

### 11.1 Phase Locking Vocoder

* Lock harmonics to spectral peaks
* Reduces phase dispersion

### 11.2 Identity Phase Locking

* Preserve relative phase of partials

### 11.3 Formant Preservation

* Separate pitch and formants
* Shift pitch, keep spectral envelope

### 11.4 Hybrid Models

* Combine PSOLA + Phase Vocoder

### 11.5 Machine Learning Approaches

* Neural vocoders
* Source-filter models

---

## 12. Summary of Major Learning Outcomes

* Pitch ≠ speed
* FFT is essential for pitch manipulation
* Phase continuity defines audio quality
* Time-frequency trade-offs are unavoidable
* Phase vocoder is powerful but imperfect

---

## 13. Final Notes and Scope Disclaimer

This project:

✔ Demonstrates deep DSP understanding
✔ Is ideal for instrumental sounds
✔ Is educational and extensible

This project is **not intended as a production-grade vocal pitch shifter**.

For vocals, advanced techniques such as **formant-aware processing or neural vocoders** are required.

---

## 14. Conclusion

This Phase Vocoder project serves as a **complete DSP learning pipeline**, covering:

* Signal framing
* Spectral analysis
* Phase mathematics
* Time-scale modification
* Pitch shifting theory

It bridges **theory → implementation → limitations**, making it an ideal academic and interview-ready project.

---

*End of README*
