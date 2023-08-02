import numpy as np

def dr(leg1,leg2):
    return leg1.deltaR(leg2)

def deltar(eta1,eta2,phi1,phi2):
    return np.sqrt(np.power(abs(eta1-eta2),2) + np.power(abs(phi1-phi2) if abs(phi1-phi2)<=np.pi else 2*np.pi-abs(phi1-phi2),2))
    #return np.sqrt(np.power(abs(eta1-eta2),2) + np.power(abs(phi1-phi2) * abs(phi1-phi2)<=np.pi else 2*np.pi-abs(phi1-phi2),2))

def notmatched(eta1,eta2,phi1,phi2):
    return deltar(eta1,eta2,phi1,phi2) > 0.1

def pairinvmass(pt1,pt2,eta1,eta2,phi1,phi2):
    return np.sqrt(2.0*pt1*pt2*(np.cosh(eta1-eta2)-np.cos(phi1-phi2)))

def phoid(EleID, PhoID, Eta):
    return EleID * (abs(Eta)<1.5) + PhoID * (abs(Eta)>=1.5)

def egid(EleID, SaID, Eta): 
    return EleID * abs(Eta)<1.5 + SaID * (abs(Eta)>=1.5)

def TkEleQualHIGH(Et,Eta,PassesEleID): return PassesEleID
def TkEleQualLOW(Et,Eta,PassesEleID): return PassesEleID * (abs(Eta)<1.479) + (abs(Eta)>1.479)
def TkEleIsoQualHIGH(Et,Eta,PassesEleID): return PassesEleID  * (abs(Eta)>1.479) +  (abs(Eta)<1.479)
def TkEleIsoQualLOW(Et,Eta,PassesEleID): return (PassesEleID>=0) # this should be always true: we can remove this condition from the menu

def tkelequalhigh(et,eta,passeseleid): return passeseleid
def tkelequallow(et,eta,passeseleid): return passeseleid * (abs(eta)<1.479) + (abs(eta)>1.479)
def tkeleisoqualhigh(et,eta,passeseleid): return passeseleid  * (abs(eta)>1.479) +  (abs(eta)<1.479)
def tkeleisoquallow(et,eta,passeseleid): return (passeseleid>=0) # this should be always true: we can remove this condition from the menu

def rangecutless(x,eta,etaRange,cutInRange,cutOutRange):
    return (x<cutInRange) * (abs(eta)<etaRange) + (x<cutOutRange) * (abs(eta)>=etaRange)
