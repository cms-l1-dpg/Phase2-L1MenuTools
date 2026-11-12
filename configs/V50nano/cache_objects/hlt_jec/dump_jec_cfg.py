import FWCore.ParameterSet.Config as cms
process = cms.Process("JECDUMP")
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, 'auto:phase2_realistic_T35', '')
process.source = cms.Source("EmptySource", firstRun=cms.untracked.uint32(1))
process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(1))
process.reader = cms.EDAnalyzer("JetCorrectorDBReader",
    payloadName=cms.untracked.string("AK4PFPuppiHLT"),
    globalTag=cms.untracked.string("phase2_realistic_T35"),
    printScreen=cms.untracked.bool(False),
    createTextFile=cms.untracked.bool(True))
process.p = cms.Path(process.reader)
