from numpy import sqrt, array, mean, sum, min, max

from pyqum.instrument.logger import set_status
from pyqum.instrument.toolbox import waveform, gotocdata
from pyqum.instrument.analyzer import curve, IQAParray


# 3. Test Square-wave Pulsing
from pyqum.directive.characterize import SQE_Pulse


# Set RUN mode:
set_status("SQE_Pulse", dict(pause=False))

# Assemble C-Structure:
CStructure = ['Flux-Bias', 'XY-Frequency', 'XY-Power', 'RO-Frequency', 'RO-Power',
                'Pulse-Period', 'RO-ifLevel', 'RO-Pulse-Delay', 'RO-Pulse-Width', 'XY-ifLevel', 'XY-Pulse-Delay', 'XY-Pulse-Width', 
                'LO-Frequency', 'LO-Power', 'ADC-delay', 'Average', 'Sampling-Time']

# Sweep Flux:
F_CORDER = {'C-Structure': CStructure,
            'Flux-Bias':'-0.006 to 0.006 * 100', 'XY-Frequency':'opt,', 'XY-Power':'opt,', 'RO-Frequency':'4.885 4.8979', 'RO-Power':'-30',
            'Pulse-Period':'15994', 'RO-ifLevel':'1', 'RO-Pulse-Delay':'0', 'RO-Pulse-Width':'15994', 'XY-ifLevel':'1', 'XY-Pulse-Delay':'0', 'XY-Pulse-Width':'15994',
            'LO-Frequency':'lockro,', 'LO-Power':'-30', 'ADC-delay':'0', 'Average':'12000', 'Sampling-Time':'2 to 2000 * 999'
            }
F_COMMENT = "Flux dependency of Qubit for different Readout frequency"
F_TAG = 'Flux-bias'

# Sweep RO-frequency:
S_CORDER = {'C-Structure': CStructure,
            'Flux-Bias':'0.002757', 'XY-Frequency':'4.45', 'XY-Power':'-100 0', 'RO-Frequency':'4.89 to 4.9 * 20', 'RO-Power':'-30',
            'Pulse-Period':'15994', 'RO-ifLevel':'1', 'RO-Pulse-Delay':'0', 'RO-Pulse-Width':'15994', 'XY-ifLevel':'1', 'XY-Pulse-Delay':'0', 'XY-Pulse-Width':'15994',
            'LO-Frequency':'lockro,', 'LO-Power':'-30', 'ADC-delay':'0', 'Average':'3000', 'Sampling-Time':'2 to 2000 * 999'
            }
S_COMMENT = "Search for dressed cavity frequency at flux=2.757mA"
S_TAG = 'cavity, spectroscopy'

# Sweep XY-frequency:
X_CORDER = {'C-Structure': CStructure,
            'Flux-Bias':'0.002757', 'XY-Frequency':'4.4 to 4.5 * 50', 'XY-Power':'0', 'RO-Frequency':'4.8979', 'RO-Power':'-30',
            'Pulse-Period':'15994', 'RO-ifLevel':'1', 'RO-Pulse-Delay':'0', 'RO-Pulse-Width':'15994', 'XY-ifLevel':'1', 'XY-Pulse-Delay':'0', 'XY-Pulse-Width':'15994',
            'LO-Frequency':'lockro,', 'LO-Power':'-30', 'ADC-delay':'0', 'Average':'3000', 'Sampling-Time':'2 to 2000 * 999'
            }
X_COMMENT = "Search for qubit frequency at flux=2.757mA using dressed cavity"
X_TAG = 'two-tone, spectroscopy'

# Sweep XY-pulse:
XP_CORDER = {'C-Structure': CStructure,
            'Flux-Bias':'-0.00205', 'XY-Frequency':'5 to 5.3 * 50', 'XY-Power':'0', 'RO-Frequency':'4.893766', 'RO-Power':'-15',
            'Pulse-Period':'63994', 'RO-ifLevel':'1', 'RO-Pulse-Delay':'0', 'RO-Pulse-Width':'1600', 'XY-ifLevel':'1', 'XY-Pulse-Delay':'0', 'XY-Pulse-Width':'63994',
            'LO-Frequency':'lockro,', 'LO-Power':'-25', 'ADC-delay':'0', 'Average':'10000', 'Sampling-Time':'2 to 3200 * 1599'
            }
XP_COMMENT = "Searching higher Qubit-frequency with Pulse Readout and Continuus Pumping"
XP_TAG = 'ro-pulse'

# Test XY-Pulses
TP_CORDER = {'C-Structure': CStructure,
            'Flux-Bias':'0', 'XY-Frequency':'4.128', 'XY-Power':'0', 'RO-Frequency':'opt,', 'RO-Power':'opt,',
            'Pulse-Period':'15994', 'RO-ifLevel':'1', 'RO-Pulse-Delay':'0', 'RO-Pulse-Width':'3000', 'XY-ifLevel':'1', 'XY-Pulse-Delay':'0', 'XY-Pulse-Width':'100 to 1000 * 19',
            'LO-Frequency':'4.128', 'LO-Power':'-10', 'ADC-delay':'0', 'Average':'100', 'Sampling-Time':'2 to 2000 * 999'
            }
TP_COMMENT = "Testing AWG consistency of pulse generation"

# Two-tone:
TT_CORDER = {'C-Structure': CStructure,
            'Flux-Bias':'-0.002 to 0 * 48', 'XY-Frequency':'4.1 to 5.3 * 240', 'XY-Power':'10', 'RO-Frequency':'4.93', 'RO-Power':'-30',
            'Pulse-Period':'63994', 'RO-ifLevel':'1', 'RO-Pulse-Delay':'lockxypwd+50,', 'RO-Pulse-Width':'1600', 'XY-ifLevel':'1', 'XY-Pulse-Delay':'0', 'XY-Pulse-Width':'0 35',
            'LO-Frequency':'lockro,', 'LO-Power':'-40', 'ADC-delay':'0', 'Average':'6000', 'Sampling-Time':'2 to 3200 * 1599'
            }
TT_COMMENT = "Two-tone to search for Qubit frequency after flux offset shifting (Ground and Excited state)"
TT_TAG = "Two-tone"

# Rabi
R_CORDER = {'C-Structure': CStructure,
            'Flux-Bias':'0.002757', 'XY-Frequency':'4.45', 'XY-Power':'-100 0 5', 'RO-Frequency':'4.8937 4.8979', 'RO-Power':'-30',
            'Pulse-Period':'63994', 'RO-ifLevel':'1', 'RO-Pulse-Delay':'lockxypwd+0,', 'RO-Pulse-Width':'1600', 'XY-ifLevel':'1', 'XY-Pulse-Delay':'0', 'XY-Pulse-Width':'0 to 600 * 300',
            'LO-Frequency':'lockro,', 'LO-Power':'-30', 'ADC-delay':'0', 'Average':'12000', 'Sampling-Time':'2 to 3200 * 1599'
            }
R_COMMENT = "Checking Lower Qubit-frequency"
R_TAG = "Rabi"

# T1
T1_CORDER = {'C-Structure': CStructure,
            'Flux-Bias':'-0.0031', 'XY-Frequency':'4.19', 'XY-Power':'10', 'RO-Frequency':'4.93', 'RO-Power':'-20',
            'Pulse-Period':'63994', 'RO-ifLevel':'1', 'RO-Pulse-Delay':'85 to 5000 * 200', 'RO-Pulse-Width':'1600', 'XY-ifLevel':'1', 'XY-Pulse-Delay':'0', 'XY-Pulse-Width':'35',
            'LO-Frequency':'lockro,', 'LO-Power':'-20', 'ADC-delay':'lockropdelay,', 'Average':'10000', 'Sampling-Time':'2 to 3200 * 1599'
            }
T1_COMMENT = "Measure T1 with time offset and higher xy-power with cavity detuning"
T1_TAG = "T1"

# New measurement:
SQE_Pulse('abc', corder=R_CORDER, comment=R_COMMENT, tag=R_TAG, dayindex=-1, testeach=False)


