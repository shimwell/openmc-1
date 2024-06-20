from pathlib import Path

import numpy as np

import openmc.checkvalue as cv


_FILES = {
    ('icrp116', 'electron'): Path('icrp116') / 'electrons.txt',
    ('icrp116', 'helium'): Path('icrp116') / 'helium_ions.txt',
    ('icrp116', 'mu-'): Path('icrp116') / 'negative_muons.txt',
    ('icrp116', 'pi-'): Path('icrp116') / 'negative_pions.txt',
    ('icrp116', 'neutron'): Path('icrp116') / 'neutrons.txt',
    ('icrp116', 'photon'): Path('icrp116') / 'photons.txt',
    ('icrp116', 'photon kerma'): Path('icrp116') / 'photons_kerma.txt',
    ('icrp116', 'mu+'): Path('icrp116') / 'positive_muons.txt',
    ('icrp116', 'pi+'): Path('icrp116') / 'positive_pions.txt',
    ('icrp116', 'positron'): Path('icrp116') / 'positrons.txt',
    ('icrp116', 'proton'): Path('icrp116') / 'protons.txt',
    ('icrp119', 'neutron'): Path('icrp119') / 'neutrons.txt',
}

_DOSE_TABLES = {key: None for key in _FILES.keys()}


def _load_dose(particle, data_source='icrp116'):
    """Load effective dose tables from text files

    Parameters
    ----------
    particle : {'neutron', 'photon', 'photon kerma', 'electron', 'positron'}
        Incident particle
    data_source : {'icrp116', 'icrp119'}
        The dose conversion data source to use

    """
    print(f'loading {particle} {data_source}')
    path = Path(__file__).parent / _FILES[data_source, particle]
    data = np.loadtxt(path, skiprows=3, encoding='utf-8')
    data[:, 0] *= 1e6   # Change energies to eV
    _DOSE_TABLES[data_source, particle] = data


def dose_coefficients(particle, geometry='AP', data_source='icrp116'):
    """Return effective dose conversion coefficients from ICRP

    This function provides fluence (and air kerma) to effective dose conversion
    coefficients for various types of external exposures based on values in ICRP
    publications. Corrected values found in a corrigendum are used rather than
    the values in the original report. Available libraries include `ICRP
    Publication 116 <https://doi.org/10.1016/j.icrp.2011.10.001>`_ and `ICRP
    Publication 119 <https://journals.sagepub.com/doi/pdf/10.1016/j.icrp.2013.05.003>`_


    Parameters
    ----------
    particle : {'neutron', 'photon', 'photon kerma', 'electron', 'positron'}
        Incident particle
    geometry : {'AP', 'PA', 'LLAT', 'RLAT', 'ROT', 'ISO'}
        Irradiation geometry assumed. Refer to ICRP-116 (Section 3.2) for the
        meaning of the options here.
    data_source : {'icrp116', 'icrp119'}
        The dose conversion data source to use.

    Returns
    -------
    energy : numpy.ndarray
        Energies at which dose conversion coefficients are given
    dose_coeffs : numpy.ndarray
        Effective dose coefficients in [pSv cm^2] at provided energies. For
        'photon kerma', the coefficients are given in [Sv/Gy].

    """

    cv.check_value('geometry', geometry, {'AP', 'PA', 'LLAT', 'RLAT', 'ROT', 'ISO'})
    cv.check_value('data_source', data_source, {'icrp116', 'icrp119'})

    if _DOSE_TABLES[data_source, particle] is None:
        _load_dose(data_source=data_source, particle=particle)

    # Get all data for selected particle
    data = _DOSE_TABLES[data_source, particle]
    if data is None:
        raise ValueError(f"{particle} has no effective dose data in data source {data_source}.")

    # Determine index for selected geometry
    if particle in ('neutron', 'photon', 'proton', 'photon kerma'):
        index = ('AP', 'PA', 'LLAT', 'RLAT', 'ROT', 'ISO').index(geometry)
    else:
        index = ('AP', 'PA', 'ISO').index(geometry)

    # Pull out energy and dose from table
    energy = data[:, 0].copy()
    dose_coeffs = data[:, index + 1].copy()
    # icrp119 neutron does have NaN values in them
    if data_source == 'icrp119' and particle == 'neutron' and geometry in ['ISO', 'RLAT']:
        dose_coeffs = dose_coeffs[~np.isnan(dose_coeffs)]
        energy = energy[:len(dose_coeffs)]
    return energy, dose_coeffs
