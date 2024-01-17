class L1IsoCut:
    def __init__(self, ak_arrays, obj: str, IsoBB=-1, IsoEE=-1, l1_iso="iso"):
        ak_arrays = ak_arrays[obj]  # TODO: remove obj arg
        self.IsoBB = IsoBB
        self.IsoEE = IsoEE
        self.l1_iso = l1_iso

        self.sel_iso_BB = ak_arrays["eta"] > -100
        self.sel_iso_EE = ak_arrays["eta"] > -100

        if self.IsoBB >= 0:
            self.sel_iso_BB = (abs(ak_arrays["eta"]) < 1.479) & (
                ak_arrays[self.l1_iso] > self.IsoBB
            )
        if self.IsoEE >= 0:
            self.sel_iso_EE = (abs(ak_arrays["eta"]) > 1.479) & (
                ak_arrays[self.l1_iso] > self.IsoEE
            )

    @property
    def ISO_EEBB(self):
        return self.sel_iso_EE | self.sel_iso_BB


class Quality:
    """
    Class implementing the L1 quality criteria.
    Hardware criteria to be decide with Menu team.
    """

    def __init__(self, ak_arrays, obj: str):
        ak_arrays = ak_arrays[obj]  # TODO: remove obj arg
        # print("Computing quality for ", obj)

        self.sel_lowEta = (abs(ak_arrays["eta"]) < 0.9) & (ak_arrays["region"] != 1)
        self.sel_midEta = (
            (abs(ak_arrays["eta"]) > 0.9)
            & (abs(ak_arrays["eta"]) < 1.2)
            & (ak_arrays["region"] != 2)
        )
        self.sel_highEta = (abs(ak_arrays["eta"]) > 1.2) & (ak_arrays["region"] != 3)

        self.sel_qualities = (
            (ak_arrays["quality"] != 11)
            & (ak_arrays["quality"] != 13)
            & (ak_arrays["quality"] != 14)
            & (ak_arrays["quality"] != 15)
            & (ak_arrays["region"] == 3)
        )
        self.sel_qual_12 = (ak_arrays["quality"] < 12) & (ak_arrays["region"] == 2)
        self.sel_qual_0 = (ak_arrays["quality"] == 0) & (ak_arrays["region"] == 3)
        self.sel_qual_1 = (ak_arrays["quality"] < 2) & (ak_arrays["region"] == 1)
        self.sel_qual_3 = (ak_arrays["quality"] != 3) & (ak_arrays["region"] == 1)
        self.sel_qual_5 = (ak_arrays["quality"] != 5) & (ak_arrays["region"] == 1)
        self.sel_qualOnly_12 = ak_arrays["quality"] < 12

        self.sel_midEta_qual = (
            (abs(ak_arrays["eta"]) > 0.9)
            & (abs(ak_arrays["eta"]) < 1.2)
            & (ak_arrays["region"] == 3)
        )

        self.sel_odd = ak_arrays["quality"] % 2 == 0
        self.sel_odd_type = (ak_arrays["quality"] % 2 == 0) & (ak_arrays["region"] == 1)
        self.sel_not_4 = ak_arrays["region"] == 4

        ### EG IDs from 123x
        self.sel_tkIsoPho_123 = (
            (ak_arrays["quality"] > 0) & (abs(ak_arrays["eta"]) < 1.479)
        ) | ((ak_arrays["quality"] == 3) & (abs(ak_arrays["eta"]) >= 1.479))

        ## EG IDs from 125x
        # for EG: region == HGC
        if "passeseleid" in ak_arrays.fields:
            self.sel_EG_barrelID = (ak_arrays["region"] == 0) & (
                ak_arrays["passeseleid"] == 1
            )
        else:
            self.sel_EG_barrelID = (ak_arrays["region"] == 0) & (
                ((ak_arrays["quality"] >> 1) & 1) > 0
            )

        if "passessaid" in ak_arrays.fields:
            self.sel_EG_endcapID = (ak_arrays["region"] == 1) & (
                ak_arrays["passessaid"] == 1
            )
        else:
            self.sel_EG_endcapID = (ak_arrays["region"] == 1) & (
                ((ak_arrays["quality"] >> 0) & 1) > 0
            )

        # for EG: quality = HwQual, alt approach: use HW qual bits directly instead of the menu ntuple variables: bit0: SA, 1: Ele, 2: Pho
        # self.sel_EG_barrelID = (ak_arrays['region'] == 0) & (((ak_arrays['quality'] >> 1)&1) > 0)
        # self.sel_EG_endcapID = (ak_arrays['region'] == 1) & (((ak_arrays['quality'] >> 0)&1) > 0)

        ## tkPhoton from 125x
        # self.sel_tkPho_barrelID = (ak_arrays['region'] == 0) & (ak_arrays['passeseleid'] == 1)
        # self.sel_tkPho_endcapID = (ak_arrays['region'] == 1) & (ak_arrays['passesphoid'] == 1)
        if "passesphoid" in ak_arrays.fields:
            self.sel_tkPho_endcapID = (ak_arrays["region"] == 1) & (
                ak_arrays["passesphoid"] == 1
            )
        else:
            self.sel_tkPho_endcapID = (ak_arrays["region"] == 1) & (
                ((ak_arrays["quality"] >> 2) & 1) > 0
            )

        # self.sel_tkPho_barrelID = (ak_arrays['region'] == 0) & (((ak_arrays['quality'] >> 1)&1) > 0)
        # self.sel_tkPho_endcapID = (ak_arrays['region'] == 1) & (((ak_arrays['quality'] >> 2)&1) > 0)

    @property
    def QUAL_125x_EGID(self):
        return ~(self.sel_EG_barrelID | self.sel_EG_endcapID)

    @property
    def QUAL_125x_tkPhoID(self):
        # return ~(self.sel_tkPho_barrelID | self.sel_tkPho_endcapID)
        return ~(self.sel_EG_barrelID | self.sel_tkPho_endcapID)

    @property
    def QUAL_123x_tkPhoID(self):
        return ~(self.sel_tkIsoPho_123)

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
        return (
            self.sel_lowEta
            | self.sel_midEta
            | self.sel_highEta
            | self.sel_qual_12
            | self.sel_qual_0
        )

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
