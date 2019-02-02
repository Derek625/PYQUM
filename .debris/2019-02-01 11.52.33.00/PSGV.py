# Communicating with Benchtop PSG
from colorama import init, Fore, Back
init(autoreset=True) #to convert termcolor to wins color

from os.path import basename as bs
mdlname = bs(__file__).split('.')[0] # module's name e.g. PSG

import visa
from pyqum.instrument.logger import address, set_status, status_code, debug
from pyqum.instrument.logger import translate_scpi as Attribute

debugger = debug(mdlname)

# INITIALIZATION
def Initiate():
    rs = address(mdlname, reset=debugger) # Instrument's Address
    rm = visa.ResourceManager()
    try:
        bench = rm.open_resource(rs) #establishing connection using GPIB# with the machine
        stat = bench.write('*CLS') #Clear buffer memory; Load preset
        bench.read_termination = '\n' #omit termination tag from output 
        bench.timeout = 150000 #set timeout in ms
        set_status(mdlname, dict(state='connected'))
        print(Fore.GREEN + "%s's connection Initialized: %s" % (mdlname, str(stat[1])[-7:]))
    except: 
        set_status(mdlname, dict(state='DISCONNECTED'))
        print(Fore.RED + "%s's connection NOT FOUND" % mdlname)
        bench = "disconnected"
    return bench

@Attribute
def model(bench, action=['Get', '']):
    SCPIcore = '*IDN'  #inquiring machine identity: "who r u?"
    return mdlname, bench, SCPIcore, action
@Attribute
def commentstate(bench, action): # query with parameters
    """This command lets you to add a descriptive comment to the saved instrument in the state register, 
        <reg_num>,<seq_num>. Comments can be up to 55 characters long.\n
        action=['Set', '<reg 0-99>,<seq 0-9>,comment']
    or  action=['Get', '<reg 0-99>,<seq 0-9>']
    """
    SCPIcore = ':MEMory:STATe:COMMENT'  #save machine state
    return mdlname, bench, SCPIcore, action
@Attribute
def memory(bench, action=['Get', '']):
    '''This command outputs a list of all files in the memory subsystem, 
    but does not include files stored in the Option 601 or 602 baseband generator memory. The return data is in the following form:\n 
    <mem_used>,<mem_free>{,"<file_listing>"} 
    The signal generator returns the two memory usage parameters and as many file listings as there are files in the memory subsystem.\n 
    Each file listing parameter is in the following form: 
    "<file_name,file_type,file_size>" '''
    SCPIcore = ':MEMory:CATalog:ALL'  #inquiring machine memory
    return mdlname, bench, SCPIcore, action
@Attribute
def frequency(bench, action=['Get', '']):
    '''This command sets the signal generator output frequency for the CW frequency mode, or increments or decrements the current RF frequency setting.\n
        action=['Set','2GHz']'''
    SCPIcore = 'SOURce:FREQUENCY:CW'
    return mdlname, bench, SCPIcore, action
@Attribute
def power(bench, action=['Get', '']): 
    '''This command sets the RF output power. 
        action=['Set','-7dbm']'''
    SCPIcore = 'SOURce:POWER:AMPLITUDE'
    return mdlname, bench, SCPIcore, action
@Attribute
def rfoutput(bench, action=['Get', '']):
    '''This command enables or disables the RF output. Although you can configure and engage various modulations, 
    no signal is available at the RF OUTPUT connector until this command is executed.'''
    SCPIcore = ':OUTPut:STATE'
    return mdlname, bench, SCPIcore, action

def close(bench, reset=True):
    if reset:
        bench.write('*RST') # reset to factory setting (including switch-off)
        set_status(mdlname, dict(config='reset'))
    else: set_status(mdlname, dict(config='previous'))
    try:
        bench.close() #None means Success?
        status = "Success"
    except: status = "Error"
    set_status(mdlname, dict(state='disconnected'))
    print(Back.WHITE + Fore.BLACK + "%s's connection Closed" %(mdlname))
    return status
        

# Test Zone
def test(detail=True):
    s = Initiate()
    if s is "disconnected":
        pass
    else:
        if debug(mdlname, detail):
            print(Fore.RED + "Detailed Test:")
            model(s)
            memory(s)
            frequency(s)
            p = float(power(s)[1]['AMPLITUDE'])
            print("Power: %s" %p)
            rfoutput(s, action=['Set', 'ON'])
            rfoutput(s)
            commentstate(s, action=['Set', "1,0,'OMG I am GREAT!'"])
            commentstate(s, action=['Get', '1,0'])
            power(s, action=['Set', '-7.3dbm'])
            power(s)
            frequency(s, action=['Set', '1GHz'])
            frequency(s)
            rfoutput(s, action=['Set', 'ON'])
            rfoutput(s)
        else: print(Fore.RED + "Basic IO Test")
    if not bool(input("Press ENTER (OTHER KEY) to (skip) reset: ")):
        state = True
    else: state = False
    close(s, reset=state)
    return

