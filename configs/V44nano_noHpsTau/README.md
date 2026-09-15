# V44_noHpsTau version - previously V45

Baseline version of CMSSW_15_1_0_pre2, which is the first full release that includes the Phase2-L1Nano Package, with the Spring24 14X 200PU MC samples.

This is a copy of V44 configs, which was based on CMSSW_14_2_0_pre1 + standalone Phase2-L1Nano Package and was the initial validation of the Spring24 samples. The difference is due to a bug in CMSSW_15_1_0_pre2 HPS Tau objects are missing in the nano, so all plots have these removed. The versions therein are named V45nano but the actual object definitions are identical to V44nano outside of the HPS Taus, so the directory was later renamed to an alternative V44.

NOTE: V44 also uses the 200PUALCA samples for MinBias and not 200PU as written in caching. This was renamed on our side in V44, but kept as 200PUALCA here to be consistent with the sample naming.
