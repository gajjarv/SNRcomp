#!/bin/python 
import os,sys

# ----- Config ----- #
Np=2
Ttime = 5*60 # In seconds
Wfrac = 5 # Assuming 5% pulse width
# ------------------ # 

filfile = sys.argv[1]
fname = filfile.split('/')[-1].strip('.fil')

cmd="echo %s | sed 's/Psr/PSR/' | sed 's/psr/PSR/' | awk -F_PSR_ '{print $2}' | awk -F_ '{print $1}' | sed 's/j/J/' | sed 's/b/B/'" % (filfile)
PSRNAME=os.popen(cmd).readline().strip()

print PSRNAME

cmd="psrcat -e %s > tmp.par" % (PSRNAME)
os.system(cmd)

cmd="dspsr -E tmp.par %s -O %s" % (filfile,fname)
os.system(cmd)

#cmd="paz -r -L -b -d -m %s.ar" % (fname)
#os.system(cmd)

cmd="psrstat -jDF -c 'snr=modular:{on=minimum:{find_min=0,smooth:width=0.05}}' -c snr %s.ar " % (fname)
SNR=float(os.popen(cmd).readline().strip().split("=")[1])

#Center frequency
#FREQ = pfdfl.lofreq - 0.5*pfdfl.chan_wid + pfdfl.chan_wid*(pfdfl.numchan/2)
cmd="psredit -c freq %s.ar" % (fname)
FREQ=float(os.popen(cmd).readline().strip().split("=")[1])

cmd="psredit -c bw %s.ar" % (fname)
BW=float(os.popen(cmd).readline().strip().split("=")[1])
BW=abs(BW*pow(10,6)) # In Hz

#Only for 80% of the band, we have sufficient sensitivity. 
BW = 0.8*BW

#Get MJD
cmd = "header %s -tstart" % (filfile)
MJD = float(os.popen(cmd).readline().strip())

#SEFD
if FREQ<2000: SEFD = 10 # For GBT-L band
if FREQ>2000 and FREQ<3000: SEFD = 12 # GBT-S band
if FREQ>3000 and FREQ<8000: SEFD = 10 # GBT-C band
if FREQ>8000 and FREQ<11000: SEFD = 15 # GBT-X band

# Get spectral index
cmd="psrcat -c 'SPINDX' -o short -nohead -nonumber " + str(PSRNAME) + " 2>&1 "
SPINDEX=os.popen(cmd).readline().strip()

# If not in the catalogue, then assume -1.4 (Bates et al. 2013)
if SPINDEX=="*": SPINDEX=-1.4
else: SPINDEX=float(SPINDEX)

# Flux at 1400 MHz
cmd="psrcat -c 'S1400' -o short -nohead -nonumber " + str(PSRNAME) + " 2>&1 "
print cmd
S1400=float(os.popen(cmd).readline().strip())

#Flux at the observing frequency
FLUX=S1400*pow((FREQ/1400.0),SPINDEX)

#Expected average profile SNR
expSNR = FLUX * pow(10,-3) * pow(Np*Ttime*BW,0.5) / (1.16*SEFD)

print "Flux at 1400 MHz : " + str(S1400) + " mJy"
print "Flux at " + str(FREQ)  + " MHz : " + str(FLUX) + " mJy"
print "MJD : " + str(MJD)
print "Expected SNR : " + str(expSNR)
print "Observed SNR : " + str(SNR)

cmd = "psrplot -N 1x2 -p flux -p freq  " + \
      " -j :0:dedisperse -j :0:fscrunch -j ':1:dedisperse' " + \
      " -c ':0:set=pub,below:r=Obs SNR: %.2f'" % (float(SNR)) +  \
      " -c ':0:below:l=Expected SNR: %.2f'" % (float(expSNR)) + \
      " -c ':1:set=pub,above:c= ,ch=3,y:reverse=1' " + \
      " -c ':0:above:c=%s'  " % (PSRNAME) + \
      " -D  %s_DSPSR.png/png " % (fname) + \
      " -c ':1:y:view=(0.1,1.13)' %s.ar " % (fname) 

print cmd	
os.system(cmd)
