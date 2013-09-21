# ---------Code Thomas, start --------------
# -*- coding: utf-8 -*-

r"""Smooth (and optionally differentiate) data with a Savitzky-Golay filter.
The Savitzky-Golay filter removes high frequency noise from data.
It has the advantage of preserving the original shape and
features of the signal better than other types of filtering
approaches, such as moving averages techhniques.

Parameters
----------
y : array_like, shape (N,)
    the values of the time history of the signal.
window_size : int
    the length of the window. Must be an odd integer number.
order : int
    the order of the polynomial used in the filtering.
    Must be less then `window_size` - 1.
deriv: int
    the order of the derivative to compute (default = 0 means only smoothing)
rate: sampling rate (in Hz; only used for derivatives)

Returns
-------
ys : ndarray, shape (N)
    the smoothed signal (or it's n-th derivative).

Notes
-----
The Savitzky-Golay is a type of low-pass filter, particularly
suited for smoothing noisy data. The main idea behind this
approach is to make for each point a least-square fit with a
polynomial of high order over a odd-sized window centered at
the point.

The data at the beginning / end of the sample are deterimined from
the best polynomial fit to the first / last datapoints. This makes the code
a bit more complicated, but avoids wild artefacts at the beginning and the
end.

"Cutoff-frequencies":
	for smoothing (deriv=0), the frequency where
	the amplitude is reduced by 10% is approximately given by
		f_cutoff = sampling_rate / (1.5 * look)

	for the first derivative (deriv=1), the frequency where 
	the amplitude is reduced by 10% is approximately given by
		f_cutoff = sampling_rate / (4 * look)

Examples
--------
t = np.linspace(-4, 4, 500)
y = np.exp( -t**2 ) + np.random.normal(0, 0.05, t.shape)
ysg = savitzky_golay(y, window_size=31, order=4)
import matplotlib.pyplot as plt
plt.plot(t, y, label='Noisy signal')
plt.plot(t, np.exp(-t**2), 'k', lw=1.5, label='Original signal')
plt.plot(t, ysg, 'r', label='Filtered signal')
plt.legend()
plt.show()

References
----------
.. [1] A. Savitzky, M. J. E. Golay, Smoothing and Differentiation of
   Data by Simplified Least Squares Procedures. Analytical
   Chemistry, 1964, 36 (8), pp 1627-1639.
.. [2] Numerical Recipes 3rd Edition: The Art of Scientific Computing
   W.H. Press, S.A. Teukolsky, W.T. Vetterling, B.P. Flannery
   Cambridge University Press ISBN-13: 9780521880688
.. [3] Siegmund Brandt, Datenanalyse, pp 435
"""

"""
Author: Thomas Haslwanter
Version: 1.0
Date: 25-July-2012
"""

import numpy as np
from numpy import dot
from math import factorial

def savgol(x, window_size=3, order=2, deriv=0, rate=1):
    ''' Savitzky-Golay filter '''
        
    # Check the input
    try:
        window_size = np.abs(np.int(window_size))
        order = np.abs(np.int(order))
    except ValueError:
        raise ValueError("window_size and order have to be of type int")
    if window_size > len(x):
        raise TypeError("Not enough data points!")
    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")
    if window_size < order + 1:
        raise TypeError("window_size is too small for the polynomials order")
    if order <= deriv:
        raise TypeError("The 'deriv' of the polynomial is too high.")


    # Calculate some required parameters
    order_range = range(order+1)
    half_window = (window_size -1) // 2
    num_data = len(x)
    
    # Construct Vandermonde matrix, its inverse, and the Savitzky-Golay coefficients   
    a = [[ii**jj for jj in order_range] for ii in range(-half_window, half_window+1)]
    pa = np.linalg.pinv(a)
    sg_coeff = pa[deriv] * rate**deriv * factorial(deriv)
      
    # Get the coefficients for the fits at the beginning and at the end
    # of the data
    coefs = np.array(order_range)**np.sign(deriv)
    coef_mat = np.zeros((order+1, order+1))
    row = 0
    for ii in range(deriv,order+1):
        coef = coefs[ii]
        for jj in range(1,deriv):
            coef *= (coefs[ii]-jj)
        coef_mat[row,row+deriv]=coef
        row += 1
    coef_mat *= rate**deriv
    
    # Add the first and last point half_window times
    firstvals = np.ones(half_window) * x[0] 
    lastvals  = np.ones(half_window) * x[-1]
    x_calc = np.concatenate((firstvals, x, lastvals))

    y = np.convolve( sg_coeff[::-1], x_calc, mode='full')
    
    # chop away intermediate data
    y = y[window_size-1:window_size+num_data-1]

    # filtering for the first and last few datapoints
    y[0:half_window] = dot(dot(dot(a[0:half_window], coef_mat), 
np.mat(pa)),x[0:window_size])
    y[len(y)-half_window:len(y)] = dot(dot(dot(a[half_window+1:window_size],
coef_mat), pa), x[len(x)-window_size:len(x)])
    
    return y

    
# --------- code thomas, stop ------------
