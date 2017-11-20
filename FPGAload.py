import spidev
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM) # Pin numbering as names on header
nCONFIG = 21 # GPIO21
nSTATUS = 16
CONF_DONE = 20
GPIO.setup(nCONFIG, GPIO.OUT)
GPIO.setup(nSTATUS, GPIO.IN)
GPIO.setup(CONF_DONE, GPIO.IN)
spi = spidev.SpiDev()
spi.open(0,0) # open /dev/spidev-0.1
spi.max_speed_hz = 2000000
#spi.lsbfirst = True   #Does not work on RBpi - duh!

print("Open file and read content...")
f = open("/home/pi/develtest/test1.rbf","rb")
bytelists=[[]]  # List of maximum 4096 byte chunks
byte = f.read(1)
n=0
i=0
while byte:
    n = n + 1
    if n == 4096:
        n = 0
        i = i + 1;
        bytelists.append([])
    bytelists[i].append(int('{:08b}'.format(int.from_bytes(byte,"little"))[::-1], 2))  # Store as integers with lsb first - awkward
    byte = f.read(1)
f.close()
print("-Ok")

print("Initiate configuration...")
#print("Set nCONFIG high, wait and assert that nSTATUS is high indicating FPGA has gone through POR")
GPIO.output(nCONFIG, GPIO.HIGH)
time.sleep(0.1)
if not GPIO.input(nSTATUS):
    print("-Fail, FPGA not ready")
#print("Pull nCONFIG low from RBp and wait for nSTATUS and CONF_DONE to be low from FPGA")
GPIO.setup(nCONFIG, GPIO.OUT)
GPIO.output(nCONFIG, GPIO.LOW)
while (GPIO.input(nSTATUS) or GPIO.input(CONF_DONE)):
    time.sleep(0.01)
#print("-Ok")
#print("Pull nCONFIG high to start configuration, wait for nSTATUS to go high")
GPIO.output(nCONFIG, GPIO.HIGH)
while (not GPIO.input(nSTATUS)):
    time.sleep(0.001)
print("-Ok")
print("Program FPGA...")

chunklist = [] # Maximum 4096 bytes
for i in range(0,len(bytelists)):
    chunk=bytelists[i]
    spi.writebytes(chunk)

#print("-Ok")
#print("Assert that CONF_DONE is high")
if GPIO.input(CONF_DONE):
    #print("-Ok")
    #print("Clock additional pulses to start FPGA")
    spi.writebytes([0x00])
    print("-Ok, done!")
else:
    print("-Fail, FPGA not configured")
spi.close()
GPIO.cleanup()
