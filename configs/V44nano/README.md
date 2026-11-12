# V44 DT12x version

Based on https://github.com/cms-l1-dpg/Phase2-L1Nano/tree/v38_1400pre3v9

Uses the Annual Review branch 1400pre3v9 and includes rerunning the TrackTrigger.

Note that several variants in the cache_objects directory are named V45nano - this is naming only, and the actual tests at the time effectively used V44nano configs (i.e with the dynamic electron EC ID for pT < 25 GeV, and including hpsTaus). V45 itself now refers to fixing the electron EC to always apply ID.