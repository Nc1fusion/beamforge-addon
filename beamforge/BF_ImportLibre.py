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
from _bf import log, log_exc, dire
import _libre
import LIB.gui, LIB.propName, LIB.dstvProcess
import LIB.libPlasma

# Maximums des champs « Cut Flush » dans ce panneau (Beamcut : 35 / 35 / 750 mm, limite du panneau
# seulement - le calcul utilise la valeur telle quelle). 1000 mm couvre toute hauteur de poutre des
# cellules ; au-dela de la moitie de la hauteur d'ame, les bandes du bas et du haut se chevauchent.
MAX_CUT_FLUSH = [('USERMINFLUSHLIMIT', 1000.0), ('USERMAXFLUSHLIMIT', 1000.0), ('USERDISTOFFSETFLANGECUT', 3000)]

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
            _bilan(dstvBuildSeq)
    else:
        LIB.gui.guiMessage('AzSimRobot', 'The provided information is not valid for generating the sequence').showError()
        OnStart()
    return


def _compte(prg):
    """(nb de routines, nb d'instructions de la routine principale) d'un programme robot."""
    try:
        return len(prg.Routines), len(prg.MainRoutine.Statements)
    except Exception:
        return '?', '?'


def _bilan(seq):
    """Diagnostic apres import : ou est le programme genere, et quelles erreurs Beamcut a notees."""
    try:
        for att in ('errProcessCode', 'errDstvNoSolutionFound', 'errDstvNotSupported', 'errDstvNotComplete',
                    'errDstvFeatureNotSupported', 'errPartOutSideSystemSize', 'setSectionErrorProcess', 'errPlasma'):
            v = getattr(seq, att, '')
            if v and str(v).strip(' \\'):
                dire(u'Bilan import libre - %s : %s' % (att, v))
        mot = getattr(seq, 'motion', None)
        prg = getattr(mot, 'rslPrg', None)
        if prg is not None:
            r, n = _compte(prg)
            try:
                nom = prg.Component.Name
            except Exception:
                nom = '?'
            dire(u'Bilan import libre - programme ecrit par Beamcut : robot %s, %s routine(s), %s instruction(s) dans Main'
                 % (nom, r, n))
        for cmp in app.Components:
            for b in cmp.findBehavioursByType(VC_ROBOTEXECUTOR):
                r, n = _compte(b.Program)
                dire(u'Bilan import libre - robot de la cellule %s : %s routine(s), %s instruction(s) dans Main'
                     % (cmp.Name, r, n))
    except Exception:
        log_exc('Bilan import libre')


def _agrandir_cut_flush():
    """Releve le maximum des champs Cut Flush (presents seulement si la machine a l'option)."""
    for attr, maxi in MAX_CUT_FLUSH:
        try:
            nom = getattr(dstvBuildSeq, attr, None)
            p = myCmd.getProperty(nom) if nom else None
            if p is not None:
                p.MaxValue = maxi
                log('Import libre : %s -> maximum %s' % (nom, maxi))
        except Exception:
            log_exc('Maximum Cut Flush %s' % attr)


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
            _agrandir_cut_flush()
            addOkButton()
            executeInActionPanel()
    except Exception:
        log_exc('Importer DSTV libre')
        dire(u'Erreur dans Importer DSTV libre (voir journal.txt).')
    return


addState(None)
