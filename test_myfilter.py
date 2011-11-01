# test_myfilter.py --- 
# 
# Filename: test_myfilter.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Created: Tue Nov  1 10:20:19 2011 (+0530)
# Version: 
# Last-Updated: Tue Nov  1 17:10:44 2011 (+0530)
#           By: Subhasis Ray
#     Update #: 362
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
from datetime import datetime
from scipy import weave
from scipy.weave import inline, converters

filename = '/media/sda6/cortical_data/2011_10_21/data_20111021_143831_21310.h5'
fhandle = h5py.File(filename, 'r')
datanode = fhandle['/lfp/electrode_1000um']
data = numpy.zeros(len(datanode))
data[:] = datanode[:]
sampling_interval = fhandle.attrs['plotdt']

def blackmann_windowedsinc_filter(data, sampling_interval, cutoff, rolloff):
    print 'Sampling rate:', 1/sampling_interval
    print 'Cutoff frequency:', cutoff
    print 'Rolloff frequency:', rolloff
    start = datetime.now()
    m = int(4.0 / (rolloff * sampling_interval) - 0.5)
    if m%2 == 1:
        m += 1
    cutoff = cutoff * sampling_interval
    indices = numpy.linspace(0.0, m+1, m+1)
    syncwin = 2 * cutoff * numpy.sinc(2*cutoff*(indices-m/2))
    # pylab.plot(indices, syncwin, label='sinc window')
    blackmann = 0.42 - 0.5 * numpy.cos(2 * numpy.pi * indices / m) + 0.08 * numpy.cos(4 * numpy.pi * indices / m)
    lowpass = syncwin * blackmann
    lowpass = lowpass/ numpy.sum(lowpass)
    filtered_data = numpy.convolve(lowpass, data, mode='same')
    end = datetime.now()
    delta = end - start
    print 'blackmann', '%g s for sample of length %d' % (delta.days * 86400 + delta.seconds + delta.microseconds * 1e-6, len(data))
    return filtered_data
    # pylab.plot(indices, lowpass, label='kernel')
    # pylab.plot(indices, blackmann, label='Blackmann window')
    # pylab.legend()
    # fig2 = pylab.figure()
    # ax2 = fig2.add_subplot(1, 1, 1)
    # ts = numpy.linspace(0, sampling_interval * len(data), len(data))
    # ax2.plot(ts, data, label='Raw data')
    # ax2.plot(ts, filtered_data, label='Filtered with Blackmann window')
    
    # pylab.show()
    
def c_blackmann_windowedsinc_filter(data, sampling_interval, cutoff, rolloff):
    start = datetime.now()
    m = int(4.0 / (rolloff * sampling_interval) - 0.5)
    if m%2 == 1:
        m += 1
    cutoff = cutoff * sampling_interval
    sample_count = len(data)
    result = numpy.zeros(sample_count, dtype='float64')
    lowpass = numpy.zeros(m);
    code = """
    double sum = 0.0, tmp;
    double pi = 3.141592;
    
    for ( int ii = 0; ii < m; ++ii){
        if ( ii == m / 2 ){
                tmp  = 2 * pi * cutoff;
        } else {
                tmp = sin(2 * pi * cutoff * (ii - m/2))/ (ii - m/2);
        }
        tmp *= (0.42 - 0.5 * cos(2 * pi * ii / m) + 0.08 * cos(4 * pi * ii / m));
        sum += tmp;
        lowpass[ii] = tmp;
    }
    for ( int ii = 0; ii < m; ++ii){
        lowpass[ii] /= sum;        
    }
    for (int jj = 0; jj < sample_count; ++jj){
        result[jj] = 0.0;
        for (int ii = 0; ii < m; ++ii){
            result[jj] += (data[jj - ii] * lowpass[ii]);
        }
    }

    """
    weave.inline(code, ['data', 'sample_count', 'lowpass', 'cutoff', 'm', 'result'])
    end = datetime.now()
    delta = end - start
    print 'cblackmann', '%g s for sample of length %d' % (delta.days * 86400 + delta.seconds + delta.microseconds * 1e-6, len(data))
    # indices = numpy.linspace(0.0, m+1, m+1)
    # ts = numpy.linspace(0, sampling_interval * len(data), len(data))
    # pylab.plot(ts, data, label='raw data')
    # pylab.plot(ts[:sample_count-m/2], result[m/2:], label='filtered data')
    # pylab.legend()
    # pylab.show()
    return result

if __name__ == '__main__':
    cutoff = 450
    rolloff = 10
    filtered = blackmann_windowedsinc_filter(data, sampling_interval, cutoff, rolloff)
    c_filtered = c_blackmann_windowedsinc_filter(data, sampling_interval, cutoff, rolloff)
    ts = numpy.linspace(0, sampling_interval * len(data), len(data))
    m = int(4.0 / (rolloff * sampling_interval) - 0.5)
    if m%2 == 1:
        m += 1
    pylab.plot(ts, data, 'b-', label='raw')
    pylab.plot(ts[:len(data) - m/2], c_filtered[m/2:], 'r-.', label='c')
    pylab.plot(ts, filtered, 'g-', label='numpy filtered')
    pylab.legend()
    pylab.show()

    
    
                         
    
# 
# test_myfilter.py ends here
