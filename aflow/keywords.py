"""Implements classes to represent each keyword with overloaded
operators to make querying with AFLUX intuitive.
"""
from six import string_types
import numpy

_all_keywords = []
"""list: of `str` keyword names for which class instances exist within
this module.
"""

def load(target):
    """Loads all keywords into the specified target dictionary.
    """
    import sys
    self = sys.modules[__name__]    
    _find_all()

    for n in _all_keywords:
        cls = getattr(self, n)
        target[n] = cls

def _find_all():
    """Finds the names of all keywords supported in this module.
    """
    #Get a reference to the module and its global keyword cache.
    global _all_keywords    
    if len(_all_keywords) == 0:
        import sys
        import inspect
        self = sys.modules[__name__]
        for n, o in inspect.getmembers(self):
            if isinstance(o, Keyword):
                _all_keywords.append(n)    

def reset():
    """Resets all the keyword instances internal states so that they
    can be re-used for a new query.
    """
    import sys
    self = sys.modules[__name__]
    _find_all()
    
    for n in _all_keywords:
        cls = getattr(self, n)
        cls.state = []
        cls.cache = []

class Keyword(object):
    """Represents an abstract keyword that can be sub-classed for a
    specific material attribute. This class also represents logical
    operators that define search queries. The combination of two
    keywords with a logical operator produces one more keyword, but
    which has its :attr:`state` altered.

    Args:
        state (str): current query state of this keyword (combination).

    Attributes:
        state (list): of `str` *composite* queries for this keyword (combination).
        ptype (type): python type that values for this keyword will have.
        name (str): keyword name to use in the AFLUX request.
        cache (list): of `str` *simple* operator comparisons.
        classes (set): of `str` keyword names that have been combined into the
          current keyword.
    """
    name = None
    ptype = None
    atype = None
    
    def __init__(self, state=None):
        self.state = state if state is not None else []
        self.cache = []
        self.classes = set([self.name])

    def __str__(self):
        if len(self.state) == 1:
            return self.state[0]
        elif len(self.cache) == 1:
            return self.cache[0]
        else:
            return self.name

    def __lt__(self, other):
        if isinstance(other, string_types):
            self.cache.append("{0}(*'{1}')".format(self.name, other))
        else:
            self.cache.append("{0}(*{1})".format(self.name, other))
        return self
            
    def __gt__(self, other):
        if isinstance(other, string_types):
            self.cache.append("{0}('{1}'*)".format(self.name, other))
        else:
            self.cache.append("{0}({1}*)".format(self.name, other))
        return self

    def __mod__(self, other):
        assert isinstance(other, string_types)
        self.cache.append("{0}(*'{1}'*)".format(self.name, other))
        return self
    
    def __eq__(self, other):
        if isinstance(other, string_types):
            self.cache.append("{0}('{1}')".format(self.name, other))
        else:
            self.cache.append("{0}({1})".format(self.name, other))
        return self

    def _generic_combine(self, other, token):
        if other is self:
            #We need to do some special handling. We shouldn't have
            #more than two entries in state; otherwise something went
            #wrong.
            if len(self.cache) == 2:
                args = self.cache[0], token, self.cache[1]
                self.state.append("{0}{1}{2}".format(*args))
            elif len(self.cache) == 1 and len(self.state) == 1:
                args = self.cache[0], token, self.state[0]
                self.state = ["{0}{1}({2})".format(*args)]
            elif len(self.state) == 2:
                args = self.state[0], token, self.state[1]
                self.state = ["({0}){1}({2})".format(*args)]
            else:
                raise ValueError("Inconsistent operators; check your parenthesis.")
                
            self.cache = []
            return self
        else:
            #Just combine the two together into a new keyword that has
            #the combined state.
            s = None
            if len(self.state) == 1 and len(self.cache) == 0:
                s = self.state[0]
            elif len(self.state) == 0 and len(self.cache) == 1:
                s = self.cache[0]
            if ':' in s or ',' in s:
                s = "({})".format(s)
                
            o = None
            if len(other.state) == 1 and len(other.cache) == 0:
                o = other.state[0]
            elif len(other.state) == 0 and len(other.cache) == 1:
                o = other.cache[0]
            if ':' in o or ',' in o:
                o = "({})".format(o)

            assert s is not None
            assert o is not None            
            result = Keyword(["{0}{1}{2}".format(s, token, o)])
            result.classes = self.classes | other.classes
            return result
    
    def __and__(self, other):
        return self._generic_combine(other, ',')
        
    def __or__(self, other):
        return self._generic_combine(other, ':')

    def __invert__(self):
        assert len(self.state) == 1 or len(self.cache) == 1
        if len(self.state) == 1:
            if '!' in self.state[0]:
                self.state[0] = self.state[0].replace('!', '')
            else:
                self.state[0] = self.state[0].replace('(', "(!")
        elif len(self.cache) == 1:
            if '!' in self.cache[0]:
                self.cache[0] = self.cache[0].replace('!', '')
            else:
                self.cache[0] = self.cache[0].replace('(', "(!")
        return self
    
    
class _node_CPU_Cores(Keyword):
    """available CPU cores (`optional`). Units: ``.
    
    

    Returns:
        float: Information about the number of cores in the node/cluster where the calculation was performed.
    """
    name = "node_CPU_Cores"
    ptype = float
    atype = "number"

node_CPU_Cores = _node_CPU_Cores()
    
class _bader_net_charges(Keyword):
    """partial charge per atom (`optional`). Units: `electrons`.
    
    

    Returns:
        list: Returns a comma delimited set of partial charges per atom of the primitive cell as calculated by the Bader Atoms in Molecules Analysis.
    """
    name = "bader_net_charges"
    ptype = list
    atype = "numbers"

bader_net_charges = _bader_net_charges()
    
class _enthalpy_formation_atom(Keyword):
    """atomic formation enthalpy (`mandatory`). Units: `eV/atom`.
    
    

    Returns:
        float: Returns the formation enthalpy DeltaHFatomic per atom).
    """
    name = "enthalpy_formation_atom"
    ptype = float
    atype = "number"

enthalpy_formation_atom = _enthalpy_formation_atom()
    
class _agl_thermal_conductivity_300K(Keyword):
    """AGL thermal conductivity (`optional`). Units: `W/m*K`.
    
    

    Returns:
        float: Returns the thermal conductivity as calculated with AGL at 300K.
    """
    name = "agl_thermal_conductivity_300K"
    ptype = float
    atype = "number"

agl_thermal_conductivity_300K = _agl_thermal_conductivity_300K()
    
class _spinD_magmom_orig(Keyword):
    """No schema information available. (`unknown`). Units: ``.
    
    .. warning:: This keyword is still listed as development level. Use it
      knowing that it is subject to change or removal.

    Returns:
        None: No description was returned from AFLUX.
    """
    name = "spinD_magmom_orig"
    ptype = None
    atype = "None"

spinD_magmom_orig = _spinD_magmom_orig()
    
class _nspecies(Keyword):
    """species count (`mandatory`). Units: ``.
    
    

    Returns:
        float: Returns the number of species in the system (e.g., binary = 2, ternary = 3, etc.).
    """
    name = "nspecies"
    ptype = float
    atype = "number"

nspecies = _nspecies()
    
class _data_source(Keyword):
    """data source (`optional`). Units: ``.
    
    

    Returns:
        list: Gives the source of the data in AFLOWLIB.
    """
    name = "data_source"
    ptype = list
    atype = "strings"

data_source = _data_source()
    
class _bader_atomic_volumes(Keyword):
    """atomic volume per atom (`optional`). Units: `&Aring;<sup>3</sup>`.
    
    

    Returns:
        list: Returns the volume of each atom of the primitive cell as calculated by the Bader Atoms in Molecules Analysis. This volume encapsulates the electron density associated with each atom above a threshold of 0.0001 electrons.
    """
    name = "bader_atomic_volumes"
    ptype = list
    atype = "numbers"

bader_atomic_volumes = _bader_atomic_volumes()
    
class _auid(Keyword):
    """AFLOWLIB Unique Identifier (`mandatory`). Units: ``.
    
    

    Returns:
        str: AFLOWLIB Unique Identifier for the entry, AUID, which can be used as a publishable object identifier.
    """
    name = "auid"
    ptype = str
    atype = "string"

auid = _auid()
    
class _ael_bulk_modulus_vrh(Keyword):
    """AEL VRH bulk modulus (`optional`). Units: `GPa`.
    
    

    Returns:
        float: Returns the bulk modulus as calculated using the Voigt-Reuss-Hill average with AEL.
    """
    name = "ael_bulk_modulus_vrh"
    ptype = float
    atype = "number"

ael_bulk_modulus_vrh = _ael_bulk_modulus_vrh()
    
class _aflowlib_date(Keyword):
    """material generation date (`optional`). Units: ``.
    
    

    Returns:
        str: Returns the date of the AFLOW post-processor which generated the entry for the library.
    """
    name = "aflowlib_date"
    ptype = str
    atype = "string"

aflowlib_date = _aflowlib_date()
    
class _calculation_memory(Keyword):
    """used RAM (`optional`). Units: `Megabytes`.
    
    

    Returns:
        float: The maximum memory used for the calculation.
    """
    name = "calculation_memory"
    ptype = float
    atype = "number"

calculation_memory = _calculation_memory()
    
class _author(Keyword):
    """author (`optional`). Units: ``.
    
    .. warning:: This keyword is still listed as development level. Use it
      knowing that it is subject to change or removal.

    Returns:
        list: Returns the name (not necessarily an individual) and affiliation associated with authorship of the data.
    """
    name = "author"
    ptype = list
    atype = "strings"

author = _author()
    
class _spacegroup_relax(Keyword):
    """relaxed space group number (`mandatory`). Units: ``.
    
    

    Returns:
        float: Returns the spacegroup number of the relaxed structure after the calculation.
    """
    name = "spacegroup_relax"
    ptype = float
    atype = "number"

spacegroup_relax = _spacegroup_relax()
    
class _agl_debye(Keyword):
    """AGL Debye temperature (`optional`). Units: `K`.
    
    

    Returns:
        float: Returns the Debye temperature as calculated with AGL.
    """
    name = "agl_debye"
    ptype = float
    atype = "number"

agl_debye = _agl_debye()
    
class _PV_atom(Keyword):
    """atomic pressure*volume (`mandatory`). Units: `eV/atom`.
    
    

    Returns:
        float: Pressure multiplied by volume of the atom.
    """
    name = "PV_atom"
    ptype = float
    atype = "number"

PV_atom = _PV_atom()
    
class _aflow_version(Keyword):
    """aflow version (`optional`). Units: ``.
    
    

    Returns:
        str: Returns the version number of AFLOW used to perform the calculation.
    """
    name = "aflow_version"
    ptype = str
    atype = "string"

aflow_version = _aflow_version()
    
class _agl_heat_capacity_Cp_300K(Keyword):
    """AGL heat capacity Cp (`optional`). Units: `kB/cell`.
    
    

    Returns:
        float: Returns the heat capacity at constant pressure as calculated with AGL at 300K.
    """
    name = "agl_heat_capacity_Cp_300K"
    ptype = float
    atype = "number"

agl_heat_capacity_Cp_300K = _agl_heat_capacity_Cp_300K()
    
class _PV_cell(Keyword):
    """unit cell pressure*volume (`mandatory`). Units: `eV`.
    
    

    Returns:
        float: Pressure multiplied by volume of the unit cell.
    """
    name = "PV_cell"
    ptype = float
    atype = "number"

PV_cell = _PV_cell()
    
class _Egap(Keyword):
    """energy gap (`mandatory`). Units: `eV`.
    
    

    Returns:
        float: Band gap calculated with the approximations and pseudopotentials described by other keywords.
    """
    name = "Egap"
    ptype = float
    atype = "number"

Egap = _Egap()
    
class _ldau_TLUJ(Keyword):
    """on site coulomb interaction (`mandatory`). Units: ``.
    
    .. warning:: This keyword is still listed as development level. Use it
      knowing that it is subject to change or removal.

    Returns:
        list: This vector of numbers contains the parameters of the DFT+U calculations, based on a corrective functional inspired by the Hubbard model.
    """
    name = "ldau_TLUJ"
    ptype = list
    atype = "numbers"

ldau_TLUJ = _ldau_TLUJ()
    
class _loop(Keyword):
    """process category (`optional`). Units: ``.
    
    

    Returns:
        list: Informs the user of the type of post-processing that was performed.
    """
    name = "loop"
    ptype = list
    atype = "strings"

loop = _loop()
    
class _valence_cell_iupac(Keyword):
    """unit cell IUPAC valence (`mandatory`). Units: ``.
    
    

    Returns:
        float: Returns IUPAC valence, the maximum number of univalent atoms that may combine with the atoms.
    """
    name = "valence_cell_iupac"
    ptype = float
    atype = "number"

valence_cell_iupac = _valence_cell_iupac()
    
class _ael_poisson_ratio(Keyword):
    """AEL Poisson ratio (`optional`). Units: ``.
    
    

    Returns:
        float: Returns the istropic Poisson ratio as calculated with AEL.
    """
    name = "ael_poisson_ratio"
    ptype = float
    atype = "number"

ael_poisson_ratio = _ael_poisson_ratio()
    
class _eentropy_cell(Keyword):
    """unit cell electronic entropy (`optional`). Units: `eV/atom`.
    
    

    Returns:
        float: Returns the electronic entropy of the unit cell used to converge the ab initio calculation (smearing).
    """
    name = "eentropy_cell"
    ptype = float
    atype = "number"

eentropy_cell = _eentropy_cell()
    
class _compound(Keyword):
    """chemical formula (`mandatory`). Units: ``.
    
    

    Returns:
        str: Returns the composition description of the compound in the calculated cell.
    """
    name = "compound"
    ptype = str
    atype = "string"

compound = _compound()
    
class _agl_acoustic_debye(Keyword):
    """AGL acoustic Debye temperature (`optional`). Units: `K`.
    
    

    Returns:
        float: Returns the acoustic Debye temperature as calculated with AGL.
    """
    name = "agl_acoustic_debye"
    ptype = float
    atype = "number"

agl_acoustic_debye = _agl_acoustic_debye()
    
class _ael_bulk_modulus_voigt(Keyword):
    """AEL Voigt bulk modulus (`optional`). Units: `GPa`.
    
    

    Returns:
        float: Returns the bulk modulus as calculated using the Voigt method with AEL.
    """
    name = "ael_bulk_modulus_voigt"
    ptype = float
    atype = "number"

ael_bulk_modulus_voigt = _ael_bulk_modulus_voigt()
    
class _kpoints(Keyword):
    """K-point mesh (`optional`). Units: ``.
    
    

    Returns:
        tuple: Set of k-point meshes uniquely identifying the various steps of the calculations, e.g. relaxation, static and electronic band structure (specifying the k-space symmetry points of the structure).
    """
    name = "kpoints"
    ptype = tuple
    atype = "numbers"

kpoints = _kpoints()
    
class _spinF(Keyword):
    """fermi level spin decomposition (`mandatory`). Units: `&mu;<sub>B</sub>`.
    
    

    Returns:
        float: For spin polarized calculations, the magnetization of the cell at the Fermi level.
    """
    name = "spinF"
    ptype = float
    atype = "number"

spinF = _spinF()
    
class _nbondxx(Keyword):
    """Nearest neighbors bond lengths (`optional`). Units: `&Aring;`.
    
    

    Returns:
        list: Nearest neighbors bond lengths of the relaxed structure per ordered set of species Ai,Aj greater than or equal to i.
    """
    name = "nbondxx"
    ptype = list
    atype = "numbers"

nbondxx = _nbondxx()
    
class _composition(Keyword):
    """composition (`optional`). Units: ``.
    
    

    Returns:
        list: Returns a comma delimited composition description of the structure entry in the calculated cell.
    """
    name = "composition"
    ptype = list
    atype = "numbers"

composition = _composition()
    
class _sponsor(Keyword):
    """sponsor (`optional`). Units: ``.
    
    .. warning:: This keyword is still listed as development level. Use it
      knowing that it is subject to change or removal.

    Returns:
        list: Returns information about funding agencies and other sponsors for the data.
    """
    name = "sponsor"
    ptype = list
    atype = "strings"

sponsor = _sponsor()
    
class _pressure(Keyword):
    """external pressure (`mandatory`). Units: `kbar`.
    
    

    Returns:
        float: Returns the target pressure selected for the simulation.
    """
    name = "pressure"
    ptype = float
    atype = "number"

pressure = _pressure()
    
class _data_language(Keyword):
    """data language (`optional`). Units: ``.
    
    

    Returns:
        list: Gives the language of the data in AFLOWLIB.
    """
    name = "data_language"
    ptype = list
    atype = "strings"

data_language = _data_language()
    
class _data_api(Keyword):
    """REST API version (`mandatory`). Units: ``.
    
    

    Returns:
        str: AFLOWLIB version of the entry, API.}
    """
    name = "data_api"
    ptype = str
    atype = "string"

data_api = _data_api()
    
class _energy_atom(Keyword):
    """atomic energy (`mandatory`). Units: `eV/atom`.
    
    

    Returns:
        float: Returns the total ab initio energy per atom- the value of energy_cell/$N$).
    """
    name = "energy_atom"
    ptype = float
    atype = "number"

energy_atom = _energy_atom()
    
class _species_pp(Keyword):
    """species pseudopotential(s) (`mandatory`). Units: ``.
    
    

    Returns:
        list: Pseudopotentials of the atomic species.
    """
    name = "species_pp"
    ptype = list
    atype = "strings"

species_pp = _species_pp()
    
class _entropic_temperature(Keyword):
    """entropic temperature (`mandatory`). Units: `Kelvin`.
    
    

    Returns:
        float: Returns the entropic temperature for the structure.
    """
    name = "entropic_temperature"
    ptype = float
    atype = "number"

entropic_temperature = _entropic_temperature()
    
class _Pearson_symbol_orig(Keyword):
    """original pearson symbol (`mandatory`). Units: ``.
    
    

    Returns:
        str: Returns the Pearson symbol of the original-unrelaxed structure before the calculation.
    """
    name = "Pearson_symbol_orig"
    ptype = str
    atype = "string"

Pearson_symbol_orig = _Pearson_symbol_orig()
    
class _corresponding(Keyword):
    """coresponding (`optional`). Units: ``.
    
    .. warning:: This keyword is still listed as development level. Use it
      knowing that it is subject to change or removal.

    Returns:
        list: Returns the name (not necessarily an individual) and affiliation associated with the data origin concerning correspondence about data.
    """
    name = "corresponding"
    ptype = list
    atype = "strings"

corresponding = _corresponding()
    
class _positions_cartesian(Keyword):
    """relaxed absolute positions (`mandatory`). Units: `&Aring;`.
    
    .. warning:: This keyword is still listed as development level. Use it
      knowing that it is subject to change or removal.

    Returns:
        numpy.ndarray: Final Cartesian positions (xi,xj,xk) in the notation of the code.
    """
    name = "positions_cartesian"
    ptype = numpy.ndarray
    atype = "numbers"

positions_cartesian = _positions_cartesian()
    
class _spin_cell(Keyword):
    """unit cell spin polarization (`mandatory`). Units: `&mu;<sub>B</sub>`.
    
    

    Returns:
        float: For spin polarized calculations, the total magnetization of the cell.
    """
    name = "spin_cell"
    ptype = float
    atype = "number"

spin_cell = _spin_cell()
    
class _scintillation_attenuation_length(Keyword):
    """attenuation length (`mandatory`). Units: `cm`.
    
    

    Returns:
        float: Returns the scintillation attenuation length of the compound in cm.
    """
    name = "scintillation_attenuation_length"
    ptype = float
    atype = "number"

scintillation_attenuation_length = _scintillation_attenuation_length()
    
class _enthalpy_cell(Keyword):
    """unit cell enthalpy (`mandatory`). Units: `eV`.
    
    

    Returns:
        float: Returns the enthalpy of the system of the unit cell, H = E + PV.
    """
    name = "enthalpy_cell"
    ptype = float
    atype = "number"

enthalpy_cell = _enthalpy_cell()
    
class _ael_shear_modulus_voigt(Keyword):
    """AEL Voigt shear modulus (`optional`). Units: `GPa`.
    
    

    Returns:
        float: Returns the shear modulus as calculated using the Voigt method with AEL.
    """
    name = "ael_shear_modulus_voigt"
    ptype = float
    atype = "number"

ael_shear_modulus_voigt = _ael_shear_modulus_voigt()
    
class _prototype(Keyword):
    """original prototype (`mandatory`). Units: ``.
    
    

    Returns:
        str: Returns the AFLOW unrelaxed prototype which was used for the calculation.
    """
    name = "prototype"
    ptype = str
    atype = "string"

prototype = _prototype()
    
class _enthalpy_atom(Keyword):
    """atomic enthalpy (`mandatory`). Units: `eV/atom`.
    
    

    Returns:
        float: Returns the enthalpy per atom- the value of enthalpy_cell/N).
    """
    name = "enthalpy_atom"
    ptype = float
    atype = "number"

enthalpy_atom = _enthalpy_atom()
    
class _lattice_system_orig(Keyword):
    """original lattice system (`mandatory`). Units: ``.
    
    

    Returns:
        str: Return the lattice system and lattice variation (Brillouin zone) of the original-unrelaxed structure before the calculation.
    """
    name = "lattice_system_orig"
    ptype = str
    atype = "string"

lattice_system_orig = _lattice_system_orig()
    
class _valence_cell_std(Keyword):
    """unit cell standard valence (`mandatory`). Units: ``.
    
    

    Returns:
        float: Returns standard valence, the maximum number of univalent atoms that may combine with the atoms.
    """
    name = "valence_cell_std"
    ptype = float
    atype = "number"

valence_cell_std = _valence_cell_std()
    
class _Pearson_symbol_relax(Keyword):
    """relaxed pearson symbol (`mandatory`). Units: ``.
    
    

    Returns:
        str: Returns the Pearson symbol of the relaxed structure after the calculation.
    """
    name = "Pearson_symbol_relax"
    ptype = str
    atype = "string"

Pearson_symbol_relax = _Pearson_symbol_relax()
    
class _positions_fractional(Keyword):
    """relaxed relative positions (`mandatory`). Units: ``.
    
    .. warning:: This keyword is still listed as development level. Use it
      knowing that it is subject to change or removal.

    Returns:
        numpy.ndarray: Final fractional positions (xi,xj,xk) with respect to the unit cell as specified in $geometry.
    """
    name = "positions_fractional"
    ptype = numpy.ndarray
    atype = "numbers"

positions_fractional = _positions_fractional()
    
class _calculation_time(Keyword):
    """used time (`optional`). Units: `seconds`.
    
    

    Returns:
        float: Total time taken for the calculation.
    """
    name = "calculation_time"
    ptype = float
    atype = "number"

calculation_time = _calculation_time()
    
class _agl_thermal_expansion_300K(Keyword):
    """AGL thermal expansion (`optional`). Units: `1/K`.
    
    

    Returns:
        float: Returns the thermal expansion as calculated with AGL at 300K.
    """
    name = "agl_thermal_expansion_300K"
    ptype = float
    atype = "number"

agl_thermal_expansion_300K = _agl_thermal_expansion_300K()
    
class _eentropy_atom(Keyword):
    """atomistic electronic entropy (`optional`). Units: `eV/atom`.
    
    

    Returns:
        float: Returns the electronic entropy of the atom used to converge the ab initio calculation (smearing).
    """
    name = "eentropy_atom"
    ptype = float
    atype = "number"

eentropy_atom = _eentropy_atom()
    
class _Bravais_lattice_orig(Keyword):
    """original bravais lattice (`optional`). Units: ``.
    
    

    Returns:
        str: Returns the Bravais lattice of the original unrelaxed structure before the calculation.
    """
    name = "Bravais_lattice_orig"
    ptype = str
    atype = "string"

Bravais_lattice_orig = _Bravais_lattice_orig()
    
class _sg2(Keyword):
    """refined compound space group (`mandatory`). Units: ``.
    
    

    Returns:
        list: Evolution of the space group of the compound.  The first, second and third string represent space group name/number before the first, after the first, and after the last relaxation of the calculation.
    """
    name = "sg2"
    ptype = list
    atype = "strings"

sg2 = _sg2()
    
class _node_RAM_GB(Keyword):
    """available RAM (`optional`). Units: `Gigabytes`.
    
    

    Returns:
        float: Information about the RAM in the node/cluster where the calculation was performed.
    """
    name = "node_RAM_GB"
    ptype = float
    atype = "number"

node_RAM_GB = _node_RAM_GB()
    
class _ael_shear_modulus_vrh(Keyword):
    """AEL VRH shear modulus (`optional`). Units: `GPa`.
    
    

    Returns:
        float: Returns the shear modulus as calculated using the Voigt-Reuss-Hill average with AEL.
    """
    name = "ael_shear_modulus_vrh"
    ptype = float
    atype = "number"

ael_shear_modulus_vrh = _ael_shear_modulus_vrh()
    
class _species_pp_version(Keyword):
    """pseudopotential species/version (`mandatory`). Units: ``.
    
    

    Returns:
        list: Species of the atoms, pseudopotentials species, and pseudopotential versions.
    """
    name = "species_pp_version"
    ptype = list
    atype = "strings"

species_pp_version = _species_pp_version()
    
class _code(Keyword):
    """ab initio code (`optional`). Units: ``.
    
    

    Returns:
        str: Returns the software name and version used to perform the simulation.
    """
    name = "code"
    ptype = str
    atype = "string"

code = _code()
    
class _aflowlib_entries_number(Keyword):
    """aflowlib entry count (`conditional`). Units: ``.
    
    

    Returns:
        float: For projects and set-layer entries, aflowlib_entrieslists the available sub-entries which are associated with the $aurl of the subdirectories.  By parsing $aurl/?aflowlib_entries (containing $aurl/aflowlib_entries_number entries) the user finds further locations to interrogate.
    """
    name = "aflowlib_entries_number"
    ptype = float
    atype = "number"

aflowlib_entries_number = _aflowlib_entries_number()
    
class _ael_elastic_anistropy(Keyword):
    """AEL elastic anistropy (`optional`). Units: ``.
    
    

    Returns:
        float: Returns the elastic anistropy as calculated with AEL.
    """
    name = "ael_elastic_anistropy"
    ptype = float
    atype = "number"

ael_elastic_anistropy = _ael_elastic_anistropy()
    
class _keywords(Keyword):
    """Title (`mandatory`). Units: ``.
    
    

    Returns:
        list: This includes the list of keywords available in the entry, separated by commas.
    """
    name = "keywords"
    ptype = list
    atype = "strings"

keywords = _keywords()
    
class _spacegroup_orig(Keyword):
    """original space group number (`mandatory`). Units: ``.
    
    

    Returns:
        float: Returns the spacegroup number of the original-unrelaxed structure before the calculation.
    """
    name = "spacegroup_orig"
    ptype = float
    atype = "number"

spacegroup_orig = _spacegroup_orig()
    
class _node_CPU_Model(Keyword):
    """CPU model (`optional`). Units: ``.
    
    

    Returns:
        str: Information about the CPU model in the node/cluster where the calculation was performed.
    """
    name = "node_CPU_Model"
    ptype = str
    atype = "string"

node_CPU_Model = _node_CPU_Model()
    
class _calculation_cores(Keyword):
    """used CPU cores (`optional`). Units: ``.
    
    

    Returns:
        float: Number of processors/cores used for the calculation.
    """
    name = "calculation_cores"
    ptype = float
    atype = "number"

calculation_cores = _calculation_cores()
    
class _forces(Keyword):
    """Quantum Forces (`optional`). Units: `eV/&Aring;`.
    
    .. warning:: This keyword is still listed as development level. Use it
      knowing that it is subject to change or removal.

    Returns:
        numpy.ndarray: Final quantum mechanical forces (Fi,Fj,Fk) in the notation of the code.
    """
    name = "forces"
    ptype = numpy.ndarray
    atype = "numbers"

forces = _forces()
    
class _agl_gruneisen(Keyword):
    """AGL Gruneisen parameter (`optional`). Units: ``.
    
    

    Returns:
        float: Returns the Gruneisen parameter as calculated with AGL.
    """
    name = "agl_gruneisen"
    ptype = float
    atype = "number"

agl_gruneisen = _agl_gruneisen()
    
class _volume_cell(Keyword):
    """unit cell volume (`mandatory`). Units: `&Aring;<sup>3</sup>`.
    
    

    Returns:
        float: Returns the volume of the unit cell.
    """
    name = "volume_cell"
    ptype = float
    atype = "number"

volume_cell = _volume_cell()
    
class _Bravais_lattice_relax(Keyword):
    """relaxed bravais lattice (`optional`). Units: ``.
    
    

    Returns:
        str: Returns the Bravais lattice of the original relaxed structure after the calculation.
    """
    name = "Bravais_lattice_relax"
    ptype = str
    atype = "string"

Bravais_lattice_relax = _Bravais_lattice_relax()
    
class _lattice_variation_orig(Keyword):
    """original lattice variation (`mandatory`). Units: ``.
    
    

    Returns:
        str: Return the lattice system and lattice variation (Brillouin zone) of the original-unrelaxed structure before the calculation.
    """
    name = "lattice_variation_orig"
    ptype = str
    atype = "string"

lattice_variation_orig = _lattice_variation_orig()
    
class _aurl(Keyword):
    """AFLOWLIB Uniform Resource Locator (`mandatory`). Units: ``.
    
    

    Returns:
        str: AFLOWLIB Uniform Resource Locator returns the AURL of the entry.
    """
    name = "aurl"
    ptype = str
    atype = "string"

aurl = _aurl()
    
class _density(Keyword):
    """mass density (`optional`). Units: `grams/cm<sup>3</sup>`.
    
    

    Returns:
        float: Returns the mass density in grams/cm3.
    """
    name = "density"
    ptype = float
    atype = "number"

density = _density()
    
class _natoms(Keyword):
    """unit cell atom count (`mandatory`). Units: ``.
    
    

    Returns:
        float: Returns the number of atoms in the unit cell of the structure entry. The number can be non integer if partial occupation is considered within appropriate approximations.
    """
    name = "natoms"
    ptype = float
    atype = "number"

natoms = _natoms()
    
class _stoichiometry(Keyword):
    """unit cell stoichiometry (`mandatory`). Units: ``.
    
    

    Returns:
        list: Similar to composition, returns a comma delimited stoichiometry description of the structure entry in the calculated cell.
    """
    name = "stoichiometry"
    ptype = list
    atype = "numbers"

stoichiometry = _stoichiometry()
    
class _energy_cell(Keyword):
    """unit cell energy (`mandatory`). Units: `eV`.
    
    

    Returns:
        float: Returns the total ab initio energy of the unit cell, E. At T=0K and p=0, this is the internal energy of the system (per unit cell).
    """
    name = "energy_cell"
    ptype = float
    atype = "number"

energy_cell = _energy_cell()
    
class _spin_atom(Keyword):
    """atomic spin polarization (`mandatory`). Units: `&mu;<sub>B</sub>/atom`.
    
    

    Returns:
        float: For spin polarized calculations, the magnetization per atom.
    """
    name = "spin_atom"
    ptype = float
    atype = "number"

spin_atom = _spin_atom()
    
class _agl_heat_capacity_Cv_300K(Keyword):
    """AGL heat capacity Cv (`optional`). Units: `kB/cell`.
    
    

    Returns:
        float: Returns the heat capacity at constant volume as calculated with AGL at 300K.
    """
    name = "agl_heat_capacity_Cv_300K"
    ptype = float
    atype = "number"

agl_heat_capacity_Cv_300K = _agl_heat_capacity_Cv_300K()
    
class _volume_atom(Keyword):
    """atomic volume (`mandatory`). Units: `&Aring;<sup>3</sup>/atom`.
    
    

    Returns:
        float: Returns the volume per atom in the unit cell.
    """
    name = "volume_atom"
    ptype = float
    atype = "number"

volume_atom = _volume_atom()
    
class _agl_bulk_modulus_isothermal_300K(Keyword):
    """AGL isothermal bulk modulus 300K (`optional`). Units: `GPa`.
    
    

    Returns:
        float: Returns the isothermal bulk modulus at 300K as calculated with AGL.
    """
    name = "agl_bulk_modulus_isothermal_300K"
    ptype = float
    atype = "number"

agl_bulk_modulus_isothermal_300K = _agl_bulk_modulus_isothermal_300K()
    
class _ael_bulk_modulus_reuss(Keyword):
    """AEL Reuss bulk modulus (`optional`). Units: `GPa`.
    
    

    Returns:
        float: Returns the bulk modulus as calculated using the Reuss method with AEL.
    """
    name = "ael_bulk_modulus_reuss"
    ptype = float
    atype = "number"

ael_bulk_modulus_reuss = _ael_bulk_modulus_reuss()
    
class _sg(Keyword):
    """compound space group (`mandatory`). Units: ``.
    
    

    Returns:
        list: Evolution of the space group of the compound.  The first, second and third string represent space group name/number before the first, after the first, and after the last relaxation of the calculation.
    """
    name = "sg"
    ptype = list
    atype = "strings"

sg = _sg()
    
class _Egap_type(Keyword):
    """band gap type (`mandatory`). Units: ``.
    
    

    Returns:
        str: Given a band gap, this keyword describes if the system is a metal, a semi-metal, an insulator with direct or indirect band gap.
    """
    name = "Egap_type"
    ptype = str
    atype = "string"

Egap_type = _Egap_type()
    
class _files(Keyword):
    """I/O files (`conditional`). Units: ``.
    
    

    Returns:
        list: Provides access to the input and output files used in the simulation (provenance data).
    """
    name = "files"
    ptype = list
    atype = "strings"

files = _files()
    
class _dft_type(Keyword):
    """DFT type (`optional`). Units: ``.
    
    

    Returns:
        list: Returns information about the pseudopotential type, the exchange correlation functional used (normal or hybrid) and use of GW.
    """
    name = "dft_type"
    ptype = list
    atype = "strings"

dft_type = _dft_type()
    
class _ael_shear_modulus_reuss(Keyword):
    """AEL Reuss shear modulus (`optional`). Units: `GPa`.
    
    

    Returns:
        float: Returns the shear modulus as calculated using the Reuss method with AEL.
    """
    name = "ael_shear_modulus_reuss"
    ptype = float
    atype = "number"

ael_shear_modulus_reuss = _ael_shear_modulus_reuss()
    
class _lattice_system_relax(Keyword):
    """relaxed lattice system (`mandatory`). Units: ``.
    
    

    Returns:
        str: Return the lattice system and lattice variation (Brillouin zone) of the relaxed structure after the calculation.
    """
    name = "lattice_system_relax"
    ptype = str
    atype = "string"

lattice_system_relax = _lattice_system_relax()
    
class _spinD(Keyword):
    """atomic spin decomposition (`mandatory`). Units: `&mu;<sub>B</sub>`.
    
    

    Returns:
        list: For spin polarized calculations, the spin decomposition over the atoms of the cell.
    """
    name = "spinD"
    ptype = list
    atype = "numbers"

spinD = _spinD()
    
class _aflowlib_entries(Keyword):
    """aflowlib entries (`conditional`). Units: ``.
    
    

    Returns:
        list: For projects and set-layer entries, aflowlib_entries lists the available sub-entries which are associated with the $aurl of the subdirectories.  By parsing $aurl/?aflowlib_entries (containing $aurl/aflowlib_entries_number entries) the user finds further locations to interrogate.
    """
    name = "aflowlib_entries"
    ptype = list
    atype = "strings"

aflowlib_entries = _aflowlib_entries()
    
class _energy_cutoff(Keyword):
    """energy cutoff (`optional`). Units: `eV`.
    
    

    Returns:
        list: Set of energy cut-offs used during the various steps of the calculations.
    """
    name = "energy_cutoff"
    ptype = list
    atype = "numbers"

energy_cutoff = _energy_cutoff()
    
class _lattice_variation_relax(Keyword):
    """relaxed lattice variation (`mandatory`). Units: ``.
    
    

    Returns:
        str: Return the lattice system and lattice variation (Brillouin zone) of the relaxed structure after the calculation.
    """
    name = "lattice_variation_relax"
    ptype = str
    atype = "string"

lattice_variation_relax = _lattice_variation_relax()
    
class _agl_bulk_modulus_static_300K(Keyword):
    """AGL static bulk modulus 300K (`optional`). Units: `GPa`.
    
    

    Returns:
        float: Returns the static bulk modulus at 300K as calculated with AGL.
    """
    name = "agl_bulk_modulus_static_300K"
    ptype = float
    atype = "number"

agl_bulk_modulus_static_300K = _agl_bulk_modulus_static_300K()
    
class _node_CPU_MHz(Keyword):
    """CPU rate (`optional`). Units: `Megahertz`.
    
    

    Returns:
        float: Information about the CPU speed in the node/cluster where the calculation was performed.
    """
    name = "node_CPU_MHz"
    ptype = float
    atype = "number"

node_CPU_MHz = _node_CPU_MHz()
    
class _enthalpy_formation_cell(Keyword):
    """unit cell formation enthalpy (`mandatory`). Units: `eV`.
    
    

    Returns:
        float: Returns the formation enthalpy DeltaHF per unit cell.
    """
    name = "enthalpy_formation_cell"
    ptype = float
    atype = "number"

enthalpy_formation_cell = _enthalpy_formation_cell()
    
class _species(Keyword):
    """atomic species (`mandatory`). Units: ``.
    
    

    Returns:
        list: Species of the atoms in this material.
    """
    name = "species"
    ptype = list
    atype = "strings"

species = _species()
    
class _geometry(Keyword):
    """unit cell basis (`mandatory`). Units: `&Aring;`.
    
    

    Returns:
        list: Returns geometrical data describing the unit cell in the usual a,b,c,alpha,beta,gamma notation.
    """
    name = "geometry"
    ptype = list
    atype = "numbers"

geometry = _geometry()
