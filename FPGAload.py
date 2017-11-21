
# Execute with path to rbf-file

import spidev
import RPi.GPIO as GPIO
import time
import sys

GPIO.setmode(GPIO.BCM) # Pin numbering as names on header
nCONFIG = 21 # GPIO21
nSTATUS = 16
CONF_DONE = 20
GPIO.setup(nCONFIG, GPIO.OUT)
GPIO.setup(nSTATUS, GPIO.IN)
GPIO.setup(CONF_DONE, GPIO.IN)

file_data=[[]]  # List of maximum 4096 byte chunks, as integers with lsb first

def read_rbf_file(filename):
    f = open(filename,"rb")

    byte = f.read(1)
    n=0
    i=0
    while byte:
        n = n + 1
        if n == 4096:
            n = 0
            i = i + 1;
            file_data.append([])
        file_data[i].append(int('{:08b}'.format(int.from_bytes(byte,"little"))[::-1], 2))  # Store as integers with lsb first - awkward
        byte = f.read(1)
    f.close()
    return (0)
    
def initiate_fpgaconf():
    # Set nCONFIG high, wait and assert that nSTATUS is high indicating FPGA has gone through POR.
    GPIO.output(nCONFIG, GPIO.HIGH)
    time.sleep(0.01)
    if not GPIO.input(nSTATUS):
        return (-1)
    # Pull nCONFIG low from RBp and wait for nSTATUS and CONF_DONE to be low from FPGA.
    GPIO.setup(nCONFIG, GPIO.OUT)
    GPIO.output(nCONFIG, GPIO.LOW)
    time.sleep(0.01)
    if GPIO.input(nSTATUS) or GPIO.input(CONF_DONE):
        return (-2)
    # Pull nCONFIG high to start configuration, wait for nSTATUS to go high
    GPIO.output(nCONFIG, GPIO.HIGH)
    time.sleep(0.01)
    if not GPIO.input(nSTATUS):
        return (-3)
    return (0)

def load_data_to_fpga():
    chunklist = [] # Maximum 4096 bytes
    spi = spidev.SpiDev()
    spi.open(0,0) # open /dev/spidev-0.1
    spi.max_speed_hz = 2000000
    #spi.lsbfirst = True   #Does not work on RBpi - duh!
    for i in range(0,len(file_data)):
        chunk=file_data[i]
        spi.writebytes(chunk)
    if GPIO.input(CONF_DONE):
        # Data received, clock additional pulses to start FPGA
        spi.writebytes([0x00])
        spi.close()
    else:
        spi.close()
        return (-1)
    return (0)
    
print("Open file and read content...")
err = read_rbf_file(sys.argv[1])
if err:
    print("Fail. Err =", err)
else:
    print("-Ok")

print("Initiate configuration...")
err = initiate_fpgaconf()
if err:
    print("Fail. Err =", err)
else:
    print("-Ok")
    
print("Loading data to FPGA...")
err = load_data_to_fpga()
if err:
    print("Fail. Err =", err)
else:
    print("-Ok, device configured successfully.")

GPIO.cleanup()
