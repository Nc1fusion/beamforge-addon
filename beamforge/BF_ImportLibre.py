# -*- coding: utf-8 -*-
# beamforge - bouton « Importer DSTV libre »
# Meme panneau et meme moteur que « Importer DSTV (*.nc1) » de Beamcut Soft (MnuFile\MnuFileDSTV.py,
# version 20260930), mais le mode libre (voir _libre.py) est applique a la copie du module que
# l'add-on utilise, et seulement pendant cet import. L'import normal de Beamcut reste inchange.
# (1.5 : le mode libre modifiait le module, mais « Importer DSTV » de Beamcut ne passait pas par
#  cette copie - constate a l'atelier : aucune trace du mode libre pendant l'import.)
from vcCommand import *
from vcHelpers.Application import *
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _bf import log_exc, dire
import _libre
import LIB.gui, LIB.propName, LIB.dstvProcess
import LIB.libPlasma

myCmd = getCommand()
app = getApplication()
sim = app.getSimulation()
dstvBuildSeq = None
plasmaDef = None
lPlasmaProp = []


def buttonPushed(arg):
    global lPlasmaProp
    print('Starting Process (beamforge : import libre)')
    myCmd = getCommand()
    plasmaDef.checkKeyParameter(myCmd)
    lPlasmaProp = []
    dstvBuildSeq.plasmaDef = plasmaDef
    dstvBuildSeq.setInfoUser(myCmd)
    if dstvBuildSeq.checkBuildCondition():
        if dstvBuildSeq.__class__ is not LIB.dstvProcess.mainProcess_Def:
            # Beamcut a recharge son module depuis l'ouverture du panneau : on repart proprement
            dire(u'Module Beamcut recharge entre-temps : relancez Importer DSTV libre.')
            return
        if not _libre.activer(LIB.dstvProcess, racine=None, surveiller_reload=False, bavard=False):
            dire(u'Import libre annule : le mode libre n\'a pas pu etre active (voir ci-dessus).')
            return
        try:
            dstvBuildSeq.workOnDstvFiles()
        finally:
            _libre.desactiver(bavard=False)
            dire(u'Import libre termine. Restrictions Beamcut retablies.')
    else:
        LIB.gui.guiMessage('AzSimRobot', 'The provided information is not valid for generating the sequence').showError()
        OnStart()
    return


def plasmaDataChange(arg):
    myCmd = getCommand()
    plasmaDef.updateUserProperties(myCmd.getProperty(plasmaDef.USERCURRENT), myCmd.getProperty(plasmaDef.USERCONSUMABLEANG),
                                   myCmd.getProperty(plasmaDef.USERMATERIALTYPE), myCmd.getProperty(plasmaDef.USERPLASMAGAZ),
                                   myCmd.getProperty(plasmaDef.USERSCRIBEGAZ), myCmd.getProperty(plasmaDef.USERSCRIBECURRENT))
    return


def addOkButton():
    global okButton
    okButton = createProperty(VC_BUTTON, 'Ok')
    okButton.OnChanged = buttonPushed
    return


def deleteMyCmdProps():
    for iProp in myCmd.Properties:
        myCmd.deleteProperty(iProp)
    return


def OnStart():
    global dstvBuildSeq, lPlasmaProp, plasmaDef
    try:
        pb = _libre.verifier(LIB.dstvProcess, racine=None)
        if pb:
            dire(u'IMPORT LIBRE IMPOSSIBLE : %s' % u'; '.join(pb))
            return
        dire(u'*** IMPORT LIBRE : la piece sera importee SANS les restrictions de Beamcut ***')
        selManage = app.SelectionManager
        selManage.clear()
        sim.halt()
        sim.reset()
        dstvBuildSeq = LIB.dstvProcess.mainProcess_Def(True, is3dImport=False)
        plasmaDef = LIB.libPlasma.CutParam(useXPRData=dstvBuildSeq.systemID.plasmaTypeIsXPR,
                                           useMaxPro=dstvBuildSeq.systemID.plasmaTypeIsMaxPro)
        deleteMyCmdProps()
        if plasmaDef.errorImportData != '':
            LIB.gui.guiMessage('BeamcutSoft', plasmaDef.errorImportData).showWarning()
        else:
            plasmaDef.maximumCurrent = dstvBuildSeq.systemID.maxPlasmaAmp
            lPlasmaProp = []
            plasmaDef.userSetPlasmaPrm(myCmd, lPlasmaProp, plasmaDataChange)
            dstvBuildSeq.infoFromUser(myCmd)
            addOkButton()
            executeInActionPanel()
    except Exception:
        log_exc('Importer DSTV libre')
        dire(u'Erreur dans Importer DSTV libre (voir journal.txt).')
    return


addState(None)
