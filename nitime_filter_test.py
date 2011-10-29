# test.py --- 
# 
# Filename: test.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Created: Sat Oct 29 22:19:59 2011 (+0530)
# Version: 
# Last-Updated: Sat Oct 29 23:12:43 2011 (+0530)
#           By: Subhasis Ray
#     Update #: 63
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

filename = '/media/sda6/cortical_data/2011_10_21/data_20111021_143831_21310.h5'
fhandle = h5py.File(filename, 'r')
datanode = fhandle['/lfp/electrode_1000um']
data = numpy.zeros(3999)
data[:] = datanode[1:4000] # first entry is 0.0 causing errors in analysis
sampling_interval = fhandle.attrs['plotdt']
# numpy.savetxt('electrode1mm.dat', data)
def test_filtering(data, sampling_interval):
    print 'sampling interval = ', sampling_interval
    T = TimeSeries([data], sampling_interval=sampling_interval)
    S_original = SpectralAnalyzer(T)
    fig01 = pylab.figure()
    
    ax01 = fig01.add_subplot(5, 1, 1)
    ax01.plot(S_original.psd[0], S_original.psd[1][0], label='Welch PSD')
    ax02 = fig01.add_subplot(5, 1, 2)
    ax02.plot(S_original.spectrum_fourier[0],
              S_original.spectrum_fourier[1][0], label='FFT')
    ax03 = fig01.add_subplot(5, 1, 3)
    ax03.plot(S_original.periodogram[0],
              S_original.periodogram[1][0], label='Periodogram')
    ax04 = fig01.add_subplot(5, 1, 4)
    ax04.plot(S_original.spectrum_multi_taper[0],
              S_original.spectrum_multi_taper[1][0], label='Multi_taper')
    F = FilterAnalyzer(T, ub=400, lb=1.0)
    ax05 = fig01.add_subplot(5, 1, 5)
    ax05.plot(F.data[0], label='Unfiltered')
    # ax01.set_xlabel('Frequency (Hz)')
    # ax01.set_ylabel('Power')    
    ax01.legend( )   
    ax02.legend( )   
    ax03.legend( )   
    ax04.legend( )
    ax05.legend()
    fig02 = pylab.figure()
    ax11 = fig02.add_subplot(1, 1, 1)
    ax11.plot(F.filtered_boxcar.data[0], label='Boxcar filter')
    ax11.plot(F.fir.data[0], label='FIR')
    ax11.plot(F.iir.data[0], label='IIR')
    ax11.plot(F.filtered_fourier.data[0], label='Fourier filter')
    ax11.legend()
    pylab.show()

if __name__ == '__main__':
    test_filtering(data, sampling_interval)
# 
# test.py ends here
