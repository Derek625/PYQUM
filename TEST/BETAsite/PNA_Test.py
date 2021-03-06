from colorama import init, Fore, Back
init(autoreset=True) #to convert termcolor to wins color

from os.path import basename as bs
mdlname = bs(__file__).split('.')[0] #py filename

import visa
from statistics import median
from numpy import arange, sqrt, arctan2, frombuffer, array, linspace, pi, log10, reshape
import matplotlib.pyplot as plt
from time import sleep, time, ctime
from pyqum.instrument.logger import get_data, set_data

# pna
rm = visa.ResourceManager()
pna = rm.open_resource("TCPIP0::192.168.0.6::hpib7,16::INSTR") #PNA

pna.read_termination = '\n' #omit termination tag from output 
pna.timeout = 80000000 #set timeout (ms)

#Checking Connections & Identities

# print('All connected GPIB Instruments:', rm.list_resources())
print(pna.query('*IDN?'))  #inquiring machine identity: "who r u?"

#Clear ALL
pna.write('*RST;*CLS;SYST:FPReset') # SYST:FPReset
pna.write("CALCulate:PARameter:DELete:ALL")

# 'setrace' in PNA [done]
Mname = []
Mparam = ['S11', 'S21']
for S in Mparam:
    iTrace = Mparam.index(S) + 1
    Mname.append("CH1_%s"%S)
    pna.write("CALC%d:PAR:EXT '%s','%s'" % (1, Mname[iTrace - 1], S)) #setting measurement name
    pna.write(":DISP:WIND%s:STATe ON" %1)
    pna.write("DISP:WIND%d:TRAC%d:FEED '%s'" % (1, iTrace, Mname[iTrace - 1])) #displaying trace (no set-trace for old-type handling of traces)
    pna.write(":DISP:WIND%d:TRAC%d:Y:AUTO"%(1, iTrace)) #pre-auto-scale

# attribute of 'catalog' in PNA [done]
Catalog = pna.query("CALC1:PAR:CAT:EXT?")
print("catalog: %s" %Catalog)

# attribute of 'sweep' in PNA [done]
pna.write("SENS:SWE:TYPE LIN")
status = pna.query("SENS:SWE:TYPE?")
print("Sweeping Type: %s" %status)
N = 18000
pna.write("SENSe:SWEep:POINts %s" %N)
datapts = pna.query("SENSe:SWEep:POINts?")
print("Sweeping Points#: %s" %datapts)

# attribute of 'linfreq' in PNA [done]
f_start, f_stop = 4.4e9, 4.9e9
pna.write("SENS:FREQuency:STARt %s" %f_start)
pna.write("SENS:FREQuency:STOP %s" %f_stop)
fstart = pna.query("SENSe:FREQuency:STARt?")
print("Start Frequency(Hz): %s" %fstart)
fstop = pna.query("SENSe:FREQuency:STOP?")
print("Stop Frequency(Hz): %s" %fstop)

# port extension calibration [auto-reset: done]
pna.write("SENS:CORR:EXT:AUTO:RESet")
# pna.write("SENS:CORR:EXT ON")
# pna.write("SENS:CORR:EXT:AUTO:PORT ON")
# pna.write("SENS:CORR:EXT:AUTO:STAR %s" %f_start)
# pna.write("SENS:CORR:EXT:AUTO:STOP %s" %f_stop)
# pna.write("SENS:CORR:EXT:AUTO:CONF USPN")
# pna.write("SENS:CORR:EXT:AUTO:LOSS 1")
# pna.write("SENS:CORR:EXT:AUTO:DCOF 1")
# pna.write("SENS:CORR:EXT:AUTO:MEAS SHORT")
# pna.write("SENS:CORR:EXT:PORT 55NS")

# PortDistance = pna.query("SENSe:CORRection:EXTension:PORT2:DISTance?")
# print("Port Extension(m): %s" %PortDistance)

# Building X-axis
fstart, fstop, datapts = float(fstart), float(fstop), int(datapts)
X = list(linspace(fstart, fstop, datapts))
fcenter = median(X)

noisefilfac = 100
IFB = abs(float(fstart) - float(fstop))/N/noisefilfac

# attribute of 'ifbw' in PNA [done]
print("Setting IFB: %s" %IFB)
pna.write("SENSe:BANDwidth %s" %IFB)#unit is in Hz
status = pna.query("SENSe:BANDwidth?") #IF Freq
print("IF-Bandwidth (Hz): %s" %status)

# attribute of 'power' in PNA [done]
pna.write("SOURce:POWer -10")
status = pna.query("SOURce:POWer?")
print("Power (dBm): %s" %status)

# attribute of 'averag' in PNA [done]
status = pna.write("SENSe:AVER:CLE")
print("Clear Average: %s" %[x for x in status])
Ave_num = 1
status = pna.write("SENSe:AVER:COUN %s" %Ave_num) #Averaged by VNA itself
print("Set Average Number=%s: %s" %(Ave_num, [x for x in status]))
status = pna.write("SENSe:AVER ON") #OFF by default
print("Set Average ON: %s" %[x for x in status])

# attribute of 'sweep' in PNA [done]
sweeptime = pna.query("SENS:SWE:TIME?")
print("Sweeping Time: %s" %sweeptime*Ave_num)

# 'measure' in PNA [done]
status = pna.write("SENSe:SWE:GRO:COUN %s" %Ave_num) #Averaged by VNA itself
print("Set Trigger group count=%s: %s" %(Ave_num, [x for x in status]))
status = pna.write("TRIG:SOUR IMM")
print("Set immediate: %s" %[x for x in status])
# when opc return, the sweep is done
status = pna.query("SENS:SWE:MODE GRO;*OPC?") # method from labber was inefficient at best, misleading us on purpose perhaps!
print("OPC: %s" %[i for i in status])

# 'autoscal' in PNA [done]
for i in range(len(Mparam)):
    pna.write(":DISP:WIND%d:TRAC%d:Y:AUTO"%(1, i+1))

# switch off pna ['rfports': done]
if pna.query("OUTP?"):
    pna.write('OUTP OFF')
print("PNA state is %s" % pna.query("OUTP?"))

def displaydata(Mname):
    pna.write("FORMat:DATA REAL,32")
    start = time() #in seconds
    databin = pna.query_binary_values("CALC:DATA? SDATA", datatype='f', is_big_endian=True)
    stop = time()
    DataAcqTimeb = stop - start
    print("It take %ss to retrieve data from machine using binary" %DataAcqTimeb)

    pna.write("FORMat:DATA ASCII,0")
    start = time() #in seconds
    datascii = pna.query_ascii_values("CALC:DATA? SDATA")
    stop = time()
    DataAcqTimes = stop - start
    print("It take %ss to retrieve data from machine using ascii" %DataAcqTimes)

    if DataAcqTimeb > DataAcqTimes:
        print("ASCII is transferred faster than Binary by %sms" %((DataAcqTimeb - DataAcqTimes)/1e-3))
    elif DataAcqTimes > DataAcqTimeb:
        print("Binary is transferred faster than ASCII by %sms" %((DataAcqTimes - DataAcqTimeb)/1e-3))
    else: print("ascii and binary has the exact same speed")

    databoth = array(databin + datascii)
    if len(databin) == len(datascii):
        DATA = databoth.reshape(2, len(databin))
    else: print("inconsistency between binary and ascii data handling!")

    for i in range(len(DATA[:])):
        if i == 0: datype = "BINARY"
        else: datype = "ASCII"
        datas = DATA[i]
        IQdata = datas.reshape(datapts, 2)
        Idata, Qdata = IQdata[:,0], IQdata[:,1]
        print("transfer#%s: Data/Idata: %s/%s" %(i, len(datas), len(Idata)))

        yI = [float(i) for i in Idata]
        yQ = [float(i) for i in Qdata]

        Amp, Pha = [], []
        for i in zip(yI, yQ):
            Amp.append(20*log10(sqrt(i[0]**2 + i[1]**2)))
            Pha.append(arctan2(i[1], i[0]))

        # Plotting
        fig, ax = plt.subplots(2, 2, sharex=True, sharey=False)
        fig.suptitle("%s-measurement: I, Q, Amplitude & Phase"%Mname, fontsize=16) # global title
        ax[0, 0].plot(X, yI)
        ax[0, 0].set(ylabel=r'I-Data (V)') #title=""
        ax[0, 1].plot(X, yQ)
        ax[0, 1].set(ylabel=r'Q-Data (V)')
        ax[1, 0].scatter(X, Amp, s=12, c='k')
        ax[1, 0].set(ylabel=r'Amplitude (dB)')
        ax[1, 1].plot(X, Pha)
        ax[1, 1].set(ylabel=r'Phase (rad)')

        # universal settings:
        for row in ax:
            for eachaxes in row:
                eachaxes.grid(color='b', linestyle=':', linewidth=0.7)
        for eachaxes in ax[1, :]:
            eachaxes.set(xlabel=r'$frequency, {\omega}_r\ (f_{center}:\ {%.1e})$'%(fcenter))

        # # Fine-tune figure; hide x ticks for top plots and y ticks for right plots
        plt.setp([a.get_xticklabels() for a in ax[0, :]], visible=False)

        # Tight layout often produces nice results
        # but requires the title to be spaced accordingly
        fig.tight_layout()
        fig.subplots_adjust(top=0.88)

        # saving image
        from pathlib import Path
        from inspect import getfile, currentframe
        pyfilename = getfile(currentframe()) # current pyscript filename (usually with path)
        INSTR_PATH = Path(pyfilename).parents[0] / "Output" # forming the folder-path
        image_file = "%sMEASUREMENT(%s).png" %(mdlname, str(ctime()).replace(":",""))
        IMG = Path(INSTR_PATH) / image_file
        fig.savefig(IMG, format="png")
        
        # saving data
        pna_data = dict(Sdata=Mname, datype=datype, X=X, yI=yI, yQ=yQ, Amp=Amp, Pha=Pha) #packing measurement data
        set_data("LTH", "NCHUQ", "Finding Resonance", "PNA", pna_data)

        plt.show()

    return

for i in range(len(Mparam)):
    # select measurement name
    pna.write('CALC%d:PAR:SEL %s'%(1, Mname[i]))
    print("%s on channel #%s is selected!" %(Mname[i], 1))
    selectedS = pna.query("CALC:PAR:SEL?")
    print("We are now retrieving %s..." %selectedS)
    displaydata(Mname[i])

pna.close()

