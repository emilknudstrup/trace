#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 17:33:55 2019

@author: emil
"""

import numpy as np
import subprocess
import itertools
## path to this script
import os

def time2phase(time,per,T0):
    '''Convert time to phase.

    :param time: Times to convert.
    :type time: array
    :param per: Period.
    :param per: float
    :param T0: Reference time (mid-transit time).
    :param T0: float

    :rerturn: Phase.
    :rtype: array

    '''
	phase = ((time-T0)%per)/per
	for ii in range(len(phase)):
		if phase[ii] > 0.5: phase[ii] = phase[ii] - 1
	return phase

# =============================================================================
# Parameters 
# =============================================================================
class OrbitalParams(object):
    '''
    The orbital parameters:
        Rp    : float       - planet-to-star ratio (in units of stellar radius).
        ecc   : float       - eccentricity of orbit.
        per   : float       - period of orbit (in days).
        w     : float       - argument of periastron (in degrees).
        T0    : float       - time of inferior conjunction (in days).
        Tw    : float       - time of periastron passage (in days).
        K     : float       - velocity amplitude (in km/s).
        RVsys : float       - systemic velocity (in km/s).
        inc   : float       - inclination (in degrees).
        a     : float       - semi-major axis (in units of stellar radius).
        imp   : float       - impact parameter.
        dur   : float       - transit duration (in hours).
        lam   : float       - planetary obliquity (in deg).
        LD    : str         - Limb-darkening law see StellarParams, default 'uni'.
        cs    : list        - Limb-darkening coefficients.

    Set the parameters by calling
        stelparams = OrbitalParams()
        stelparams.ecc = 0.0
    '''
    def __init__(self):
        self.Rp = 0.1
        self.ecc = 0.0
        self.per = 2.8
        self.w = 90.
        self.T0 = 0.0
        self.Tw = 0.0
        self.K = 10.
        self.RVsys = 0.0
        self.inc = 87.
        self.a = 15.
        self.imp = 0.3
        self.dur = None
        self.lam = 0.
        self.LD = 'uni'
        self.cs = None

class StellarParams(object):
    '''Class to hold the stellar parameters.

	The stellar parameters:
		Teff    : float       - effective temperature (in K).
		logg    : float       - surface gravity (in cm/s2).
		MeH     : float       - metallicity [Fe/H] (in dex).
        vsini   : float       - projected rotational velocity (in km/s).
        inc     : float       - inclination of steller soin axis (in deg).
		LD      : string      - limb darkening law used; 
								'uni'  - uniform, no LD.
							    'quad' - quadratic, default.
								'nl'   - non-linear.
								'small'- LD for a small planet. 
		xi      : float       - micro-turbulence (in km/s);
        zeta    : float       - macro-turbulence (in km/s).
        gamma   : float       - Lorentzian dispersion of spectral lines (in km/s).
        beta    : float       - Gaussian dispersion of spectral lines (in km/s).
        alpha   : float       - coefficient of differential rotation.

    Set the parameters by calling
        stelparams = StellarParams()
        stelparams.Teff = 5000.0

    Default is a sun-like star in terms of Teff, logg, and [Fe/H]. 
    '''
    def __init__(self):
        self.Teff = 5750
        self.logg = 4.5
        self.MeH = 0.0
        self.vsini = 10.0
        self.inc = 90.
        self.LD = 'quad'
        self.xi = 2.0
        self.zeta = 1.0
        self.gamma = 1.0
        self.beta = 3.0
        self.alpha = 0.0

class InstrumentParams(object):
    '''
	The stellar parameters:
		res     : float       - resolution of spectrograph

    Set the parameters by calling
        insparams =InstrumentParams()
        insparams.res = 67000

    Default is a sun-like star in terms of Teff, logg, and [Fe/H]. 
    '''
    def __init__(self):
        self.res = 115000

def get_LDcoeff(stelpars,cat='TESS'):
    '''Get Limb darkening coefficients.

	Function that collects limb darkening coefficients from Vizier.
	
    Catalogs:
    ----------
        J/A+A/600/A30/
        -Calculated by A. Claret using ATLAS atmospheres for TESS [5]_.
    
        J/A+A/552/A16/
        -Calculated by A. Claret using Phoenix atmospheres for Kepler, 
        CoRot, Spitzer, uvby, UBVRIJHK, Sloan, and 2MASS [6]_.
            

	The limb darkening law is decided by the one specified in `stelpars.LD`.

	:param stelpars: stellar parameters from class :py:class:`StellarParams`.
    :type stelpars: object 
    :param cat: Catalog from which to extract LD coefficients.
    :type cat: str

	:return	coeffs: List of LD coefficients in ascending order.
    :rtype: list

   References
    ----------
    [5] A. Claret in ADS:2017A&A...600A..30C.
    [6] A. Claret in ADS:2013A&A...552A..16C.

    '''
    Teff, logg, MeH = stelpars.Teff, stelpars.logg, stelpars.MeH
    xi, LD = stelpars.xi, stelpars.LD

    xis = np.arange(0,9,2,dtype=np.float)

    xi_idx = np.argmin(abs(xis-float(xi)))
    xi = '{:0.1f}'.format(xis[xi_idx])

    from astroquery.vizier import Vizier


    cats = {'TESS' : 'J/A+A/600/A30/',
            'V' :'J/A+A/552/A16/',
            'B' :'J/A+A/552/A16/'}
    if cat == 'TESS':
        LDs = {'lin' : 'table24', 'quad' : 'table25', 'sqrt' : 'table26',
	          'log' : 'table27', 'nl' : 'table28', 'small' : 'table28'}
        LDs['vals'] = {'Teff' : [3500,250,50000], 'logg' : [0.0,0.5,5.0], 
                       'MeH' : [-5.0,0.5,1.0]}
        tab = 'J/A+A/600/A30/'
    else:
        LDs = {'quad' : 'limb1-4', 'sqrt' : 'limb1-4', 'log' : 'limb1-4'}
        LDs['vals'] = {'Teff' : [5000,200,10000], 'logg' : [0.0,0.5,5.5], 
                       'MeH' : [-5.0,0.5,1.0]}
        tab = 'J/A+A/552/A16/'


    for par in LDs['vals']:
      vals = np.arange(LDs['vals'][par][0],LDs['vals'][par][-1]+0.01,LDs['vals'][par][1])
      if par == 'Teff':
        minimum = np.argmin(abs(vals-stelpars.Teff))
        Teff = int(vals[minimum])
      elif par == 'logg':
        minimum = np.argmin(abs(vals-stelpars.logg))
        logg = vals[minimum]
      elif par == 'MeH':
        minimum = np.argmin(abs(vals-stelpars.MeH))
        MeH = vals[minimum]

    catalog = Vizier.query_constraints(catalog=tab+'{}'.format(LDs[LD]),
		                               Teff='{:d}'.format(Teff), 
		                               logg='{:0.1f}'.format(logg),
		                               Z='{:0.1f}'.format(MeH), xi=xi)
                                       #Filt=cat)
    
    try:
      cols = catalog[0][:][0].colnames
    except IndexError:
      print('\nWARNING! No LD coefficients found for star with')
      print('Teff = {} K, logg = {} cm/s^2, [Fe/H] = {}\n'.format(Teff,logg,MeH))
      stelpars = StellarParams()
      print('Using Teff = {} K, logg = {} cm/s^2, [Fe/H] = {}'
            .format(stelpars.Teff,stelpars.logg,stelpars.MeH))
      print('(Solar-like values)')
      catalog = Vizier.query_constraints(catalog=tab+'{}'.format(LDs[LD]),
                                         Teff='{}'.format(stelpars.Teff), 
                                         logg='{}'.format(stelpars.logg),
                                         Z='{}'.format(stelpars.MeH), 
                                         xi='{}'.format(stelpars.xi))
      cols = catalog[0][:][0].colnames
	
    coeffs = []
    if cat == 'TESS':
        for name in cols:
          if name.endswith('LSM'):
            coeff = catalog[0][:][0][name]
            coeffs.append(coeff)
    else:
        idx = np.where(catalog[0][:]['Filt'] == cat)[0][0]
        if LD == 'quad':
            coeffs = [catalog[0][:][idx]['a'], catalog[0][:][idx]['b']]
        elif LD == 'sqrt':
            coeffs = [catalog[0][:][idx]['c'], catalog[0][:][idx]['d']]
        elif LD == 'log':
            coeffs = [catalog[0][:][idx]['e'], catalog[0][:][idx]['f']]

    return coeffs

# =============================================================================
# Keplerian motion 
# =============================================================================
def solve_keplers_eq(mean_anomaly, ecc, tolerance=1.e-5):
	'''Solves Kepler's equation.

    Function that solves Kepler's equation:
	.. math:: M = E - \sin(E) ,
	where M is the mean anomaly and E the eccentric anomaly.

	This is done following the Newton-Raphson method as described in [1]_.

	:param mean_anomaly: The mean anomaly.
    :type mean_anomaly: array
    :param ecc: Eccentricity.
    :type ecc: float
    :param tolerance: The tolerance for convergene. Defaults to 1.e-5.
    :type tolerance: float (,optional).

    :return: The new eccentric anomaly.
	:rtype: array 

    References
    ----------
    [1] Carl D. Murray and Alexandre C. M. Correia in arXiv:1009.1738v2.


	'''
	## Circular orbit
	if ecc == 0: return mean_anomaly 

	new_ecc_anomaly = mean_anomaly
	converged = False

	for ii in range(300):
		old_ecc_anomaly = new_ecc_anomaly

		new_ecc_anomaly = old_ecc_anomaly - (old_ecc_anomaly - ecc*np.sin(old_ecc_anomaly) - mean_anomaly)/(1.0 - ecc*np.cos(old_ecc_anomaly))

		if np.max(np.abs(new_ecc_anomaly - old_ecc_anomaly)/old_ecc_anomaly) < tolerance:
			converged = True
			break

	if not converged:
		print('Calculation of the eccentric anomaly did not converge!')

	return new_ecc_anomaly

def true_anomaly(time, Tw, ecc, P, w):#, T0=True):
    '''Function that returns the true anomaly.

    The approach follows [1].
	
    Parameters
    ----------
    :param time: Times of observations.
    :type time: array
    :param Tw: Time of periastron.
    :type Tw: float
    :param ecc: Eccentricity.
    :type ecc: float
    :param P: Orbital period.
    :type P: float
    :param ww: Argument of periastron in radians.
    :type ww: float


    :return: cosine, sine of the true anomaly.
    :rtype: (array, array)

    
    References
    ----------
    [1] Carl D. Murray and Alexandre C. M. Correia in arXiv:1009.1738v2.


    '''
    
    n = 2.0*np.pi/P
    
    # ## With this you supply the mid-transit time 
    # ## and then the time of periastron is calculated
    # ## from S. R. Kane et al. (2009), PASP, 121, 886. DOI: 10.1086/648564
    # if T0:
    #     f_Tw = np.pi/2.0 - w
    #     E = 2.0*np.arctan(np.tan(f_Tw/2.0)*np.sqrt((1.0 - ecc)/(1.0 + ecc)))
    #     M = E - ecc*np.sin(E)
    #     Tc = Tw - M/n
    # else:
    #     Tc = Tw
    mean_anomaly = n*(time-Tw)
    ecc_anomaly = solve_keplers_eq(mean_anomaly,ecc)

    cos_E = np.cos(ecc_anomaly)
    sin_E = np.sin(ecc_anomaly)

    ## Cosine and sine of the true anomaly
    cos_f = (cos_E - ecc)/(1.0 - ecc*cos_E)
    sin_f = (np.sqrt(1 - ecc**2)*sin_E)/(1.0 - ecc*cos_E)

    return cos_f, sin_f
    

# =============================================================================
# Sky projected distance 
# =============================================================================
def proj_dist(cos_f,sin_f,ww,inc,ar,ecc):
    '''The separation of the centers of the two orbiting objects.
    
    Function that returns the separation of the centers of the two orbiting objects.
    The approach follows [2]_.
    
    
    :param cos_f: cosine of the true anomaly
    :type cos_f: array
    :param sin_f: sine of the true anomaly
    :type sin_f: array            
    :param ww: Argument of periastron in radians.
    :type ww: float
    :param inc: Inclination in radians.
    :type inc: float
    :param ar: Semi-major axis in stellar radii.
    :type ar: float
    :param ecc: Eccentricity.
    :type ecc: float
    
    :return: separation of centers.
    :rtype: array
    
    References
    ----------
    [2] L. Kreidberg in arXiv:1507.08285.


    '''

    nn = len(cos_f)
    sep = np.zeros(nn)
    for ii in range(nn):
        ## Huge value for separation to make sure not to model planet passing behind star
        ## NOTE: Expressions like sin(w + f) are expanded to stay clear of arctan
        if np.sin(inc)*(np.sin(ww)*cos_f[ii] + np.cos(ww)*sin_f[ii]) <= 0:
            sep[ii] = 1000.
        else:
            nom = ar*(1.0 - ecc**2)
            nom *= np.sqrt(1.0 - (np.sin(ww)*cos_f[ii] + np.cos(ww)*sin_f[ii])**2*np.sin(inc)**2)
            den = 1.0 + ecc*cos_f[ii]
            sep[ii] = nom/den

    return sep

# =============================================================================
# x,y-position on the stellar disk 
# =============================================================================
def xy_pos(cos_f,sin_f,ecc,ww,ar,inc,lam):
    '''Position of planet on stellar disk.

    Function to calculate the position on the stellar disk.
    Stellar disk goes from 0 to 1 in x and y.

    :param cos_f: cosine of the true anomaly
    :type cos_f: array
    :param sin_f: sine of the true anomaly
    :type sin_f: array            
    :param ecc: Eccentricity.
    :type ecc: float
    :param ww: Argument of periastron in radians.
    :type ww: float
    :param ar: Semi-major axis in stellar radii.
    :type ar: float
    :param inc: Inclination in radians.
    :type inc: float
    :param lam: Projected obliquity in radians.
    :type lam: float

    :return: x,y position of planet on stellar disk.
    :rtype: (array,array)
    

    '''
    r = ar*(1.0 - ecc**2)/(1.0 + ecc*cos_f)
    f = np.arctan2(sin_f,cos_f)
    
    ## x and y are lists of the positions of the transitting planet on the stellar disk 
    ## normalized to stellar radius (using a/Rs), corresponding to each RV-point
    x_old = -1*r*np.cos(ww + f)
    y_old = -1*r*np.sin(ww + f)*np.cos(inc)

    ## Rotate our coordinate system, such that the projected obliquity becomes the new y-axis
    x = x_old*np.cos(lam) - y_old*np.sin(lam)
    y = x_old*np.sin(lam) + y_old*np.cos(lam)   
    return x, y


# =============================================================================
# Rossiter-McLaughlin effect 
# =============================================================================
def get_RM(cos_f,sin_f,ww,ecc,ar,inc,rp,c1,c2,lam,vsini,
    beta=3.,gamma=1.,zeta=1.0,alpha=0.,cos_is=0.0,
    mpath='./'):
    '''The Rossiter-McLaughlin effect

    Function to calculate the Rossiter-McLaughlin effect for transiting exoplanets.

    The approach follows [3]_.

    :param cos_f: cosine of the true anomaly
    :type cos_f: array
    :param sin_f: sine of the true anomaly
    :type sin_f: array            
    :param ww: Argument of periastron in radians.
    :type ww: float
    :param ecc: Eccentricity.
    :type ecc: float
    :param ar: Semi-major axis in stellar radii.
    :type ar: float
    :param inc: Inclination in radians.
    :type inc: float
    :param rp: Planet-to-star radius ratio.
    :type rp: float
    :param c1: Linear limb-darkening coefficient.
    :type c1: float
    :param c2: Quadratic limb-darkening coefficient.
    :type c2: float
    :param lam: Projected obliquity in radians.
    :type lam: float
    :param vsini: Projected stellar rotation in km/s.
    :type vsini: float
    :param beta: Macro-turbulence rotation in km/s. Defaults to 3.
    :type beta: float(, optional)
    :param gamma:  in km/s. Defaults to 1.
    :type gamma: float(, optional)
    :param zeta: Micro-turbulence rotation in km/s. Defaults to 1.0.
    :type zeta: float(, optional)
    :param alpha:  in km/s. Defaults to 0.
    :type alpha: float(, optional)
    :param cos_is:  in . Defaults to 0.
    :type alpha: float(, optional)

    :param mpath: Path to the code by [3]_. Defaults to './'.
    :type mpath: str(, optional)

    :return: The RM signal.
    :rtype: array       

    
    References
    ----------
    [3] Hirano et al. 2011 arXiv:1108.4430, doi:10.1088/0004-637X/742/2/69

    '''
    x, y = xy_pos(cos_f,sin_f,ecc,ww,ar,inc,lam)
    
    try:
        nn = len(cos_f)
        ## Alternates x and y for Hiranos code
        xy = [str(j) for j in itertools.chain.from_iterable(itertools.zip_longest(x,y))]
    except TypeError:
        nn = 1
        xy = [str(x),str(y)]   

    ## Create list of input to subprocess
    wd = os.getcwd()
    os.chdir(mpath)
    run_input = ['./new_analytic7.exe']
    pars = [c1,c2,vsini,rp,beta,gamma,zeta,alpha,cos_is,nn]
    for par in pars: run_input.append(str(par))    
    
    RM = subprocess.check_output(run_input + xy)
    os.chdir(wd)
    
    RM = [float(k)*1000 for k in RM.split()]
    
    return RM


# =============================================================================
# Radial velocity curve 
# =============================================================================

def get_RV(time, orbpars, RM=False, stelpars=None,mpath='./'):
    '''The radial velocity curve

    Function that returns the radial velocity curve of the orbit following [1]_.
    If RM is set to True it will include the RM effect as implemented in :py:func:`get_RM`.
	
    :param time: Times of observations.
    :type time: array

    :param orbpars: Orbital parameters from :py:class:`OrbitalParams`.
    :type orbpars: object

    :param RM: Whether to calculate the RM effect or not. Defaults to ``False``.
    :type RM: bool(, optional)

    :param stelpars: Stellar parameters from :py:class:`StellarParams`. Defaults to ``None``.
    :type stelpars: object(, optional)

    :param mpath: Path to the code by [3]_. Defaults to './'.
    :type mpath: str(, optional)
    
    :return: Radial velocity curve.
    :rtype: array
    
    References
    ----------
    [1] Carl D. Murray and Alexandre C. M. Correia in arXiv:1009.1738v2.

    '''
    Tw = orbpars.Tw
    ecc = orbpars.ecc
    per = orbpars.per
    w = orbpars.w
    K = orbpars.K
    RVsys = orbpars.RVsys

    ## Convert angle from degree to radians
    w *= np.pi/180.

    ## Get cosine and sine of the true anomaly
    cos_f, sin_f = true_anomaly(time,Tw,ecc,per,w)
    
    ## Radial velocity
    vr = K*(np.cos(w)*(ecc + cos_f) - np.sin(w)*sin_f)

    if RM:
        a = orbpars.a
        inc = orbpars.inc
        ## Convert angle from degree to radians
        inc *= np.pi/180.

        Rp = orbpars.Rp
        sep = proj_dist(cos_f,sin_f,w,inc,a,ecc)

        ## Projected stellar rotation
        vsini = stelpars.vsini
        ## Macroturbulence 
        zeta = stelpars.zeta
        ## Microturbulence 
        xi = stelpars.xi
        #beta = 3
        ## The all important obliquity
        lam = orbpars.lam
        lam *= np.pi/180.
        ## LD coefficients
        c1, c2 = orbpars.cs
        ## Impact parameter
        #b = a*np.cos(inc)#*(1 - ecc**2)/(1 + ecc*np.sin(w))

        idxs = []
        for idx, dd in enumerate(sep):
            if 1 + Rp < dd: 
                pass
            else: 
                idxs.append(idx)
        
        if len(idxs) == 0:
            pass 
        elif len(idxs) == 1:
            cos_f, sin_f = np.array(cos_f[idx]), np.array(sin_f[idx])
            RMs = get_RM(cos_f,sin_f,w,ecc,a,inc,Rp,c1,c2,lam,vsini,beta=xi,zeta=zeta,mpath=mpath)
            idx = idxs[0]
            vr[idx] = vr[idx] + RMs
        else:
            RMs = get_RM(cos_f,sin_f,w,ecc,a,inc,Rp,c1,c2,lam,vsini,beta=xi,zeta=zeta,mpath=mpath)
            for idx in idxs: vr[idx] = vr[idx] + RMs[idx]

    return vr + RVsys

# =============================================================================
# 
# =============================================================================
    
# def duration(P,rp,ar,inc,ecc,ww):
#     b = ar*np.cos(inc)*(1 - ecc**2)/(1 + ecc*np.sin(ww))
#     nom = np.arcsin( np.sqrt( (1 + rp)**2 - b**2 )/(np.sin(inc)*ar)  )*np.sqrt(1 - ecc**2)
#     den = (1 + ecc*np.sin(ww))
#     t14 = P/np.pi * nom/den
#     return t14

def total_duration(P,rp,ar,inc,ecc,ww):
    '''The total duration of the transit, i.e., .. math: T41 .

    This is the time from the first to the last contact point.

    :param P: Orbital period.
    :type P: float
    :param rp: Planet-to-star radius ratio.
    :type rp: float
    :param ar: Semi-major axis in stellar radii.
    :type ar: float
    :param inc: Inclination in radians.
    :type inc: float
    :param ecc: Eccentricity.
    :type ecc: float
    :param ww: Argument of periastron in radians.
    :type ww: float

    :return: the total duration of the transit
    :rtype: float

    .. note::
        The output will have the same units as the orbital period.


    '''
    b = ar*np.cos(inc)*(1 - ecc**2)/(1 + ecc*np.sin(ww))
    nom = np.arcsin( np.sqrt( ((1 + rp)**2 - b**2))/(np.sin(inc)*ar)  )*np.sqrt(1 - ecc**2)
    den = (1 + ecc*np.sin(ww))
    t41 = P/np.pi * nom/den
    return t41

def full_duration(P,rp,ar,inc,ecc,ww):
    '''The duration of the transit with the planet completely within the stellar disk, i.e., .. math: T32 .

    This is the time from the second to the third contact point.

    :param P: Orbital period.
    :type P: float
    :param rp: Planet-to-star radius ratio.
    :type rp: float
    :param ar: Semi-major axis in stellar radii.
    :type ar: float
    :param inc: Inclination in radians.
    :type inc: float
    :param ecc: Eccentricity.
    :type ecc: float
    :param ww: Argument of periastron in radians.
    :type ww: float

    :return: the total duration of the transit
    :rtype: float

    .. note::
        The output will have the same units as the orbital period.


    '''
    b = ar*np.cos(inc)*(1 - ecc**2)/(1 + ecc*np.sin(ww))
    nom = np.arcsin( np.sqrt( ((1 - rp)**2 - b**2))/(np.sin(inc)*ar)  )*np.sqrt(1 - ecc**2)
    den = (1 + ecc*np.sin(ww))
    t32 = P/np.pi * nom/den
    return t32


def get_rel_vsini(b, lam):
    '''Relative value of vsini at limbs.

    Function that returns the relative value of vsini at first and last contact
    following [4]_.
    
    :param b: Impact parameter.
    :type b: float
    :param lam: Projected obliquity in radians.
    :type lam: float

    :return: relative value of vsini at x1, x2.
    :rtype: (float,float)

    
    References
    ----------
    [4] Albrecht et al. (2011), bibcode: 2011ApJ...738...50A


    '''

    x1 = np.sqrt(1 - b**2)*np.cos(lam) - b*np.sin(lam)
    x2 = np.sqrt(1 - b**2)*np.cos(lam) + b*np.sin(lam)
    return x1, x2

if __name__=='__main__':
  print('Go!')