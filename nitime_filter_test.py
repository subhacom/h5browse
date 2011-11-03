# test.py --- 
# 
# Filename: test.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Created: Sat Oct 29 22:19:59 2011 (+0530)
# Version: 
# Last-Updated: Thu Nov  3 16:09:48 2011 (+0530)
#           By: Subhasis Ray
#     Update #: 121
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# 
# 
# 

# Change log:
# 
# 
# 

# Code:
import numpy
import pylab
import h5py
import nitime
from nitime.timeseries import TimeSeries
from nitime.analysis import FilterAnalyzer, SpectralAnalyzer, NormalizationAnalyzer
from analyzer import blackmann_windowedsinc_filter
filename = '/media/sda6/cortical_data/2011_10_21/data_20111021_143831_21310.h5'
fhandle = h5py.File(filename, 'r')
sampling_interval = fhandle.attrs['plotdt']
stim_dur = 0.5
sample_count = int(stim_dur/sampling_interval+0.5)
stim_start = 3.5
start_index = int(stim_start / sampling_interval + 0.5)
datanode = fhandle['/lfp/electrode_1000um']
data = numpy.zeros(2000)
data[:] = datanode[start_index:start_index+sample_count] # first entry is 0.0 causing errors in analysis
data = blackmann_windowedsinc_filter([data], sampling_interval)

# numpy.savetxt('electrode1mm.dat', data)
def test_filtering(data, sampling_interval):
    print 'sampling interval = ', sampling_interval
    T = TimeSeries([data], sampling_interval=sampling_interval)
    S_original = SpectralAnalyzer(T)
    pylab.figure()
    print len(S_original.psd[0]), len(S_original.psd[1][0])
    pylab.subplot(2, 3, 1)
    pylab.plot(S_original.psd[0], S_original.psd[1][0], 'r.', label='Welch PSD')
    pylab.legend()
    pylab.subplot(2, 3, 2)
    pylab.plot(S_original.spectrum_fourier[0],
              S_original.spectrum_fourier[1][0], 'r.', label='FFT')
    pylab.legend()
    pylab.subplot(2, 3, 3)
    pylab.plot(S_original.periodogram[0],
              S_original.periodogram[1][0], 'r.', label='Periodogram')
    pylab.legend()
    pylab.subplot(2, 3, 4)
    pylab.plot(S_original.spectrum_multi_taper[0],
              S_original.spectrum_multi_taper[1][0], 'r.', label='Multi_taper')
    pylab.legend()

    F = FilterAnalyzer(T, ub=400, lb=1.0)
    pylab.subplot(2, 3, 5)
    pylab.plot(F.data[0], label='Unfiltered')
    pylab.legend()
    # ax01.set_xlabel('Frequency (Hz)')
    # ax01.set_ylabel('Power')    
    # ax01.legend( )   
    # ax02.legend( )   
    # ax03.legend( )   
    # ax04.legend( )
    # ax05.legend()
    # fig02 = pylab.figure()
    # ax11 = fig02.add_subplot(1, 1, 1)
    # ax11.plot(F.filtered_boxcar.data[0], label='Boxcar filter')
    # ax11.plot(F.fir.data[0], label='FIR')
    # ax11.plot(F.iir.data[0], label='IIR')
    # ax11.plot(F.filtered_fourier.data[0], label='Fourier filter')
    # ax11.legend()
    pylab.show()

if __name__ == '__main__':
    test_filtering(data[0], sampling_interval)
# 
# test.py ends here
