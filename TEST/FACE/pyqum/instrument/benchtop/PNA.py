# Communicating with Benchtop P-series Vector Network Analyzer 
from colorama import init, Fore, Back
init(autoreset=True) #to convert termcolor to wins color

from os.path import basename as bs
mdlname = bs(__file__).split('.')[0] # model's name e.g. ESG, PSG, MXG, AWG, VSA, ADC
debugger = 'debug' + mdlname

import visa
from functools import wraps
from pyqum.instrument.logger import address, set_status, status_code

import matplotlib.pyplot as plt
from numpy import arange, floor, ceil

def debug(state=False):
    exec('%s %s; %s = %s' %('global', debugger, debugger, 'state'), globals(), locals()) # open global and local both-ways channels!
    if state:
        print(Back.RED + '%s: Debugging Mode' %debugger.replace('debug', ''))
    return

debug() # declare the debugger mode here

# INITIALIZATION
def Initiate():
    rs = address(mdlname, reset=eval(debugger)) # Instrument's Address
    rm = visa.ResourceManager()
    try:
        bench = rm.open_resource(rs) #establishing connection using GPIB# with the machine
        stat = bench.write('*CLS;*RST;') #Clear buffer memory; Load preset
        bench.read_termination = '\n' #omit termination tag from output 
        bench.timeout = 731000 #set timeout in ms
        set_status(mdlname, dict(state='connected'))
        print(Fore.GREEN + "%s's connection Initialized: %s" % (mdlname, str(stat[1])[-7:]))
    except: 
        set_status(mdlname, dict(state='DISCONNECTED'))
        print(Fore.RED + "%s's connection NOT FOUND" % mdlname)
        bench = "disconnected"
    return bench

def Attribute(Name):
    @wraps(Name)
    def wrapper(*a, **b):

        global debug
        bench, SCPIcore, action = Name(*a, **b)
        SCPIcore = SCPIcore.split(";")
        parakeys, paravalues, getspecific, command = [(SCPIcore[0]).split(':')[-1]] + SCPIcore[1:], [], [], []

        if action[0] == 'Get':
            try:
                for i in range(len(parakeys)):
                    if len(str(action[i+1])) > 0: #special type of query (e.g. commentstate)
                        getspecific.append(" " + str(action[i+1]))
                    else: getspecific.append('')
                    command.append(str(SCPIcore[i]) + "?" + getspecific[i])
                command = ";".join(command)

                paravalues = bench.query(command).split(';')
                paravalues = [paravalues[i] + '(' + str(action[i+1]) + ')' for i in range(len(parakeys))]
                paravalues = [x.replace('()', '') for x in paravalues]

                status = "Success"
            except: # get out of the method with just return-value at exception?
                status = "query unsuccessful"
                ans = None

        if action[0] == 'Set':

            for i in range(len(parakeys)):
                paravalues.append(str(action[i+1]))
                command.append(str(SCPIcore[i]) + " " + paravalues[i])

            command = ";".join(command)
            status = str(bench.write(command)[1])[-7:]
            
        # formatting return answer
        if len(SCPIcore) > 1:
            ans = dict(zip(parakeys, paravalues))
        else: ans = paravalues[0]

        # Logging answer
        if action[0] == 'Get': # No logging for "Set"
            set_status(mdlname, {Name.__name__ : str(ans)})

        # debugging
        if eval(debugger):
            print(Fore.BLUE + "SCPI Command: {%s}" %command)
            if action[0] == 'Get':
                print(Fore.YELLOW + "%s %s's %s: %s <%s>" %(action[0], mdlname, Name.__name__, ans, status))
            if action[0] == 'Set':
                print(Back.YELLOW + Fore.MAGENTA + "%s %s's %s: %s <%s>" %(action[0], mdlname, Name.__name__ , ans, status))

        return status, ans
    return wrapper

@Attribute
def model(bench, action=['Get'] + 10 * ['']):
    SCPIcore = '*IDN'  #inquiring machine identity: "who r u?"
    return bench, SCPIcore, action
@Attribute
def channel1(bench, action=['Get'] + 10 * ['']):
    '''action=['Get/Set', <coupling>, <range>, <scale>, <offset>, <units>, <Display>]'''
    SCPIcore = ':CHANNEL1:COUPLING;RANGE;SCALE;OFFSET;UNITs;Display'
    return bench, SCPIcore, action
@Attribute
def timebase(bench, action=['Get'] + 10 * ['']):
    '''action=['Get/Set', <mode>, <range[ns]>, <delay[ns]>, <scale[ns]>]'''
    SCPIcore = ':TIMEBASE:MODE;RANGE;DELAY;SCALE'
    return bench, SCPIcore, action
@Attribute
def acquiredata(bench, action=['Get'] + 10 * ['']): # ACQUIRING DATA from DSO
    '''action=['Get/Set', <type{average}>, <complete{0-100}>, <count{N}>]'''
    SCPIcore = ':ACQUIRE:TYPE;COMPLETE;COUNT'
    return bench, SCPIcore, action
@Attribute
def waveform(bench, action=['Get'] + 10 * ['']): # SETTING UP WAVEFORM
    '''action=['Get/Set', <POINTS{MAX}>, <SOURCE{CHANNEL1}>, <FORMAT{ASCII}>, <XINCrement?>, <DATA?>]'''
    SCPIcore = ':WAVEFORM:POINTS;SOURCE;FORMAT;XINCrement;DATA'
    return bench, SCPIcore, action
@Attribute
def measure(bench, action=['Get'] + 10 * ['']): # SETTING UP WAVEFORM
    '''action=['Get', <COUNter>, <RISEtime>, <FALLtime>, <PWIDth>, <NWIDth>, <VPP>, <VAMP>, <VRMS>]'''
    SCPIcore = ':MEASure:COUNter;RISEtime;FALLtime;PWIDth;NWIDth;VPP;VAMP;VRMS'
    return bench, SCPIcore, action

def display2D(dx, y, units):
    # setting png path
    from pathlib import Path
    from inspect import getfile, currentframe
    pyfilename = getfile(currentframe()) # current pyscript filename (usually with path)
    INSTR_PATH = Path(pyfilename).parents[2] / "static" / "img" / "dso" # 2 levels up the path
    png_file =  mdlname + "waveform.png"
    PNG = Path(INSTR_PATH) / png_file
    # Organizing Data
    Y = [float(i) for i in y.split(",")[1:-1]] # to avoid the first and the last string
    X = arange(0, len(Y), 1) * dx
    # Plotting
    fig, ax = plt.subplots()
    ax.plot(X, Y)
    ax.set(xlabel='time(%s)'%units[0], ylabel='voltage (%s)'%units[1], title=mdlname+'-Waveform')
    plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment='right')
    fig.savefig(PNG)
    if eval(debugger):
        plt.show()

def close(bench, reset=True):
    try:
        if reset:
            # bench.write('*RST;channel1:display off;') # reset to factory setting (including switch-off)
            set_status(mdlname, dict(config='reset'))
        else: set_status(mdlname, dict(config='previous'))
        try:
            bench.close() #None means Success?
            status = "Success"
        except: status = "Error"
        set_status(mdlname, dict(state='disconnected'))
        print(Back.WHITE + Fore.BLACK + "%s's connection Closed" %(mdlname))
    except: 
        status = "disconnected per se!!!"
        pass
    return status

# Test Zone
def test(detail=False):
    debug(detail)
    print(Back.WHITE + Fore.MAGENTA + "Debugger mode: %s" %eval(debugger))
    bench = Initiate()
    if bench is "disconnected":
        pass
    else:
        if eval(debugger):
            
        else: print(Fore.RED + "Basic IO Test")
    close(bench)
    return

# test(True)


