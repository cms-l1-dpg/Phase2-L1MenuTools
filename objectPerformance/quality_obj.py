class Quality():
    """
    Class implementing the L1 quality criteria.
    Hardware criteria to be decide with Menu team.
    """
    def __init__(self, ak_arrays, obj: str):
        self.ak_arrays = ak_arrays[obj]
        self.set_selections() 

    def set_selections(self):
        self.sel_lowEta = (abs(self.ak_arrays['eta']) < 0.9) & (self.ak_arrays['region'] != 1)
        self.sel_midEta = (abs(self.ak_arrays['eta']) > 0.9) & (abs(self.ak_arrays['eta']) < 1.2) & (self.ak_arrays['region'] != 2)
        self.sel_highEta = (abs(self.ak_arrays['eta']) > 1.2) & (self.ak_arrays['region'] != 3)

        self.sel_qualities = (self.ak_arrays['quality'] != 11) & (self.ak_arrays['quality'] != 13) & (self.ak_arrays['quality'] != 14) & (self.ak_arrays['quality'] != 15) & (self.ak_arrays['region'] == 3)
        self.sel_qual_12 = (self.ak_arrays['quality'] < 12) & (self.ak_arrays['region'] == 2)
        self.sel_qual_0 = (self.ak_arrays['quality'] == 0) & (self.ak_arrays['region'] == 3)
        self.sel_qual_1 = (self.ak_arrays['quality'] < 2) & (self.ak_arrays['region'] == 1)
        self.sel_qual_3 = (self.ak_arrays['quality'] != 3) & (self.ak_arrays['region'] == 1)
        self.sel_qual_5 = (self.ak_arrays['quality'] != 5) & (self.ak_arrays['region'] == 1)
        self.sel_qualOnly_12 = (self.ak_arrays['quality'] < 12)

        self.sel_midEta_qual = (abs(self.ak_arrays['eta']) > 0.9) & (abs(self.ak_arrays['eta']) < 1.2) & (self.ak_arrays['region'] == 3)

        self.sel_odd = self.ak_arrays['quality'] %2 == 0
        self.sel_odd_type = (self.ak_arrays['quality'] %2 == 0) & (self.ak_arrays['region'] == 1)
        sel_not_4 = self.ak_arrays['region'] == 4
    
    @property
    def QUAL_Overlap12EndcapJaana1345(self):
        return self.sel_qual_12 | self.sel_qualities
    
    @property
    def QUAL_OverlapNotRegion3(self):
        return self.sel_midEta_qual
    
    @property
    def QUAL_Endcap1OverlapNotRegion3(self):
        return self.sel_midEta_qual | self.sel_qual_0
    
    @property
    def QUAL_Overlap12(self):
        return self.sel_qual_12
    
    @property
    def QUAL_BarrelNoneEndcap3(self):
        return self.sel_qual_3
    
    @property        
    def QUAL_CorrectRegion(self):
        return self.sel_lowEta | self.sel_midEta | self.sel_highEta
    
    @property
    def QUAL_Endcap1CorrectRegion(self):
        return self.sel_lowEta | self.sel_midEta | self.sel_highEta | self.sel_qual_0

    @property
    def QUAL_BarrelOddEndcap2(self):
        return self.sel_odd_type | self.sel_qual_1

    @property        
    def QUAL_BarrelNoneEndcap5(self):
        return self.sel_qual_5

    @property
    def QUAL_Overlap12Endcap1(self):
        return self.sel_qual_12 | self.sel_qual_0

    @property
    def QUAL_Endcap1(self):
        return self.sel_qual_0

    @property
    def QUAL_Odd(self):
        return self.sel_odd

    @property        
    def QUAL_Overlap12Endcap1CorrectRegion(self):
        return self.sel_lowEta | self.sel_midEta | self.sel_highEta | self.sel_qual_12 | self.sel_qual_0

    @property        
    def QUAL_12(self):
        return self.sel_qualOnly_12

    @property
    def QUAL_RegionNotFour(self):
        return self.sel_not_4

    @property
    def QUAL_Overlap12Endcap1OverlapNotRegion3(self):
        return self.sel_midEta_qual | self.sel_qual_12 | self.sel_qual_0

    @property
    def QUAL_BarrelNoneEndcap2(self):
        return self.sel_qual_1

    @property
    def QUAL_EndcapJaana1345(self):
        return self.sel_qualities
