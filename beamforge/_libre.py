# -*- coding: utf-8 -*-
# beamforge - MODE LIBRE : import DSTV sans les restrictions de Beamcut Soft.
#
# Ce que le mode libre change (uniquement pendant qu'il est actif, en memoire, aucun fichier
# de Beamcut Soft n'est modifie) :
#   A. refus     : zones de securite (30/60 mm des ailes, 250/381 mm sous une poutre en I, trop
#                  pres des bouts) ignorees sans question ; raccord ame / ailes des coupes
#                  d'extremite (« Cut on faces are not aligned ») : les coupes non raccordees sont
#                  faites separement, telles que dessinees ; collisions du robot AVEC LA PIECE
#                  notees au journal au lieu de refuser la zone. (1.9 : les collisions avec la
#                  machine - supports, serre-pieces - restent gerees par Beamcut, qui deplace la
#                  poutre pour les eviter ; en 1.8 elles etaient ignorees : constate a l'atelier.)
#   B. rognages  : SI / KO / IK gardes exactement comme dessines (plus de rognage dans la zone
#                  permise).
# Garde tel quel (C) : hauteur / largeur maxi, « Cannot go underneath », limites d'axes,
#                  singularites, portee du robot, rapport trou / epaisseur, inclinaison de la
#                  torche pres des ailes, retouche des chanfreins de soudure AK (1.7 : sans elle,
#                  le raccord ame / ailes echoue - « Cut on faces are not aligned » - et aucun
#                  programme n'est genere, constate a l'atelier en 1.6).
#
# Ecrit pour BeamCutSoft 20260930-develop[b02f54a] : chaque fonction remplacee est verifiee par
# empreinte de son bytecode ; si Beamcut a change, le mode libre refuse de s'activer.
# Compatible Python 2.7 (Visual Components) et Python 3 (tests).
import os, sys, zlib

from _bf import ICI, log, log_exc, dire       # ICI de _bf : vrai dossier, meme si BeamCutSoft donne
                                               # __file__ sous la forme 'file:C:/.../My+Commands/...'
MY_COMMANDS = os.path.dirname(ICI)
MODULE = 'LIB.dstvProcess'
MARQUE_LS = 'MODE LIBRE - SANS RESTRICTION'    # 30 caracteres max (commentaire -> remarque .LS)

# (classe, methode) -> CRC32 du bytecode dans la version validee
EMPREINTES = {
    ('mainProcess_Def', 'isFeatureOk'): 2616169431,
    ('mainProcess_Def', 'processSectionsV2'): 97336939,
    ('processSI_BO_IK_KO_Def', 'adjustInXYMaterial'): 648648659,
    ('motionStmtDef', 'checkIfErrorsInRoutine'): 1875956449,
    ('setSections_def', 'checkIfAllAKConnectionDone'): 946646471,
}
# controles de profil appeles par isFeatureOk (constante de profil -> methode)
CONTROLES_PROFIL = [('CHANNEL', 'isFeatureOkCHANNEL'), ('LANGLE', 'isFeatureOkLANGLE'),
                    ('BULBFLAT', 'isFeatureOkLANGLE'), ('TBEAM', 'isFeatureOkTBeam'),
                    ('TUBE', 'isFeatureOkHSS'), ('HBEAM', 'isFeatureOkHBeam')]
REFUS_GARDES = ['Cannot go underneath']        # restrictions physiques (C) conservees

_etat = {'actif': False, 'originaux': {}, 'module': None, 'reload': None, 'piece': None}
_rapport = {'fichier': '', 'items': []}


# ------------------------------------------------------------------ outils
def actif():
    return _etat['actif']


def _crc(fonction):
    code = getattr(fonction, '__code__', None) or getattr(fonction, 'func_code')
    return zlib.crc32(code.co_code) & 0xffffffff


def _note(texte):
    """Element ignore par le mode libre, pour la piece en cours."""
    if texte not in _rapport['items']:
        _rapport['items'].append(texte)
        log('MODE LIBRE [%s] %s' % (_rapport['fichier'], texte))


def _debut_piece(nom):
    _rapport['fichier'] = nom
    _rapport['items'] = []


def _resume_piece():
    items = _rapport['items']
    if not items:
        dire(u'MODE LIBRE - %s : aucune restriction rencontree.' % _rapport['fichier'])
        return
    dire(u'MODE LIBRE - %s : %d element(s) NON verifie(s) par Beamcut :' % (_rapport['fichier'], len(items)))
    for t in items:
        dire(u'   - %s' % t)


def _commandes_utilisent_module(racine=MY_COMMANDS):
    """Les commandes d'import passent-elles toujours par LIB.dstvProcess ? (Beamcut prepare un
    nouveau moteur, LIB.mainProcess : s'il est branche, le mode libre n'aurait plus d'effet.)"""
    import base64
    for nom in ('MnuFileDSTV.py', 'MnuFolderDSTV.py'):
        chemin = os.path.join(racine, 'MnuFile', nom)
        try:
            data = open(chemin, 'rb').read().strip()
        except IOError:
            return False, u'%s introuvable' % nom
        if data.startswith(b'BYTECODE('):
            data = base64.b64decode(data[data.index(b')') + 1:])
        if b'dstvProcess' not in data or b'mainProcess_Def' not in data:
            return False, u'%s n\'utilise plus LIB.dstvProcess' % nom
    return True, ''


# ------------------------------------------------------------------ remplacements
def _isFeatureOk(orig):
    def isFeatureOk(self, folderProcess=False, isTestPiece=False):
        if isTestPiece:
            return orig(self, folderProcess, isTestPiece)
        _debut_piece(os.path.basename(getattr(self, 'filePath', '') or ''))
        dire(u'*** MODE LIBRE ACTIF : restrictions Beamcut desactivees pour %s ***' % _rapport['fichier'])
        if not getattr(self, 'doHolesDrillOnly', False):
            self.chkHoleDiamRatioThick(folderProcess)          # (C) gardé : trou trop petit / épaisseur
        self.isFeatureOkMsg = ''
        self.errMsgInSafeZone = ''
        mod = _etat['module']
        code = self.beamDef.profileCode
        for const, meth in CONTROLES_PROFIL:
            if hasattr(mod, const) and code == getattr(mod, const) and hasattr(self, meth):
                if not getattr(self, meth)():                    # même contrôle, sans la question
                    msg = self.errMsgInSafeZone or ''
                    for garde in REFUS_GARDES:
                        if garde in msg:
                            self.isFeatureOkMsg = garde
                            dire(u'MODE LIBRE : refus conserve (limite physique) : %s' % garde)
                            return False
                    for ligne in [l.strip() for l in msg.split('\n') if l.strip()]:
                        _note(u'Zone de securite ignoree : %s' % ligne)
                break
        self.modifiedCutFeature = True     # passage normal ; le rognage lui-même est neutralisé
        return True
    return isFeatureOk


def _adjustInXYMaterial(orig):
    def adjustInXYMaterial(self, workList, removeItm=True, applyOffset=True, isSIKO=False):
        # détection seulement : ce que Beamcut aurait fait
        try:
            avant = len(workList)
            apres = orig(self, list(workList), removeItm, applyOffset, isSIKO)
            if len(apres) != avant:
                face = getattr(self, 'curFace', '?')
                _note(u'Element %s face %s garde tel que dessine (Beamcut l\'aurait rogne)'
                      % ('SI/KO' if isSIKO else 'IK', face))
        except Exception:
            log_exc('MODE LIBRE : detection rognage')
        self.vecInSafe = False
        copie = []
        for itm in workList:                     # même copie que Beamcut, sans rien retirer
            if type(itm).__name__ == 'vcVector':
                import vcVector
                copie.append(vcVector.new(itm))
            else:
                copie.append(itm)
        return copie
    return adjustInXYMaterial


def _noms(noeud, profondeur=12):
    """Noms du noeud touche et de ses parents (la piece peut etre touchee par un sous-noeud)."""
    noms = []
    while noeud is not None and profondeur > 0:
        try:
            noms.append(noeud.Name)
            noeud = noeud.Parent
        except Exception:
            break
        profondeur -= 1
    return noms


class _DetecteurEspion(object):
    """Enveloppe un détecteur de collision : la collision est notée, mais ne bloque plus."""

    def __init__(self, reel):
        object.__setattr__(self, '_reel', reel)

    def testOneCollision(self, *args, **kw):
        reel = object.__getattribute__(self, '_reel')
        if not reel.testOneCollision(*args, **kw):
            return False
        try:
            na, nb = reel.getHitNodeA(0), reel.getHitNodeB(0)
            a, b = na.Name, nb.Name
            piece = _etat['piece']
            avec_piece = piece is not None and (piece in _noms(na) or piece in _noms(nb))
        except Exception:
            a = b = '?'
            avec_piece = False
        if not avec_piece:
            return True          # collision avec la machine : Beamcut cherche une autre position
        routine = point = '?'
        try:
            loc = sys._getframe(1).f_locals
            routine, point = loc.get('routineName', '?'), loc.get('stmtName', '?')
        except Exception:
            pass
        _note(u'COLLISION avec la piece %s / %s : %s contre %s' % (routine, point, a, b))
        return False

    def __getattr__(self, nom):
        return getattr(object.__getattribute__(self, '_reel'), nom)

    def __setattr__(self, nom, valeur):
        setattr(object.__getattribute__(self, '_reel'), nom, valeur)


def _checkIfErrorsInRoutine(orig):
    def checkIfErrorsInRoutine(self, routine):
        liste = getattr(self, 'lLayoutColl', None)
        if not liste or isinstance(liste[0], _DetecteurEspion):   # appel récursif : déjà enveloppé
            return orig(self, routine)
        self.lLayoutColl = [_DetecteurEspion(c) for c in liste]
        try:
            return orig(self, routine)           # limites d'axes, singularités, portée : inchangés
        finally:
            self.lLayoutColl = liste
    return checkIfErrorsInRoutine


def _processSectionsV2(orig):
    def processSectionsV2(self):
        try:
            cmp = getattr(self, 'beamBuilded', None) or self.beamDef.cmp
            _etat['piece'] = cmp.Name
        except Exception:
            _etat['piece'] = None
            log_exc('MODE LIBRE : nom de la piece')
        try:
            r = orig(self)
        finally:
            _etat['piece'] = None
        try:
            prg = self.motion.rslPrg
            import LIB.rslProgram
            LIB.rslProgram.addCommentToRoutine(MARQUE_LS, prg.MainRoutine, index=0)
        except Exception:
            log_exc('MODE LIBRE : marque dans le programme')
        _resume_piece()
        return r
    return processSectionsV2


def _checkIfAllAKConnectionDone(orig):
    def checkIfAllAKConnectionDone(self):
        restes = [k for k, v in getattr(self, 'AK_ConnectionMatch', {}).items() if v > 0]
        if restes:
            _note(u'Coupes d\'extremite non raccordees (%s) : ame et ailes coupees separement, '
                  u'telles que dessinees - verifier la jonction' % ', '.join(sorted(str(k) for k in restes)))
        return None
    return checkIfAllAKConnectionDone


REMPLACEMENTS = {
    ('mainProcess_Def', 'isFeatureOk'): _isFeatureOk,
    ('mainProcess_Def', 'processSectionsV2'): _processSectionsV2,
    ('processSI_BO_IK_KO_Def', 'adjustInXYMaterial'): _adjustInXYMaterial,
    ('motionStmtDef', 'checkIfErrorsInRoutine'): _checkIfErrorsInRoutine,
    ('setSections_def', 'checkIfAllAKConnectionDone'): _checkIfAllAKConnectionDone,
}


# ------------------------------------------------------------------ activation
def _module():
    mod = sys.modules.get(MODULE)
    if mod is None:
        __import__(MODULE)
        mod = sys.modules[MODULE]
    return mod


def verifier(mod, empreintes=EMPREINTES, racine=MY_COMMANDS):
    """Liste des problèmes empêchant l'activation (vide = OK)."""
    pb = []
    for (cls, meth), attendu in sorted(empreintes.items()):
        c = getattr(mod, cls, None)
        f = c.__dict__.get(meth) if c is not None else None
        if f is None:
            pb.append(u'%s.%s introuvable' % (cls, meth))
        elif attendu is not None and _crc(f) != attendu:
            pb.append(u'%s.%s a change (mise a jour de Beamcut Soft ?)' % (cls, meth))
    if racine is not None:
        ok, msg = _commandes_utilisent_module(racine)
        if not ok:
            pb.append(msg)
    return pb


def _appliquer(mod):
    for (cls, meth), fabrique in REMPLACEMENTS.items():
        c = getattr(mod, cls)
        orig = c.__dict__[meth]
        _etat['originaux'][(id(mod), cls, meth)] = (c, orig)
        setattr(c, meth, fabrique(orig))
    _etat['module'] = mod


def _retirer():
    for (mid, cls, meth), (c, orig) in list(_etat['originaux'].items()):
        setattr(c, meth, orig)
    _etat['originaux'].clear()


def _installer_reload():
    """Les commandes Beamcut font reload(LIB.dstvProcess) : on réapplique après chaque rechargement."""
    try:
        import __builtin__ as bi
    except ImportError:
        import builtins as bi
    if _etat['reload'] is not None or not hasattr(bi, 'reload'):
        return
    orig = bi.reload

    def reload(m):
        r = orig(m)
        try:
            if _etat['actif'] and getattr(r, '__name__', '') == MODULE:
                _etat['originaux'].clear()
                pb = verifier(r, racine=None)
                if pb:
                    desactiver()
                    dire(u'MODE LIBRE DESACTIVE : module Beamcut recharge et different (%s)' % '; '.join(pb))
                else:
                    _appliquer(r)
                    log('MODE LIBRE reapplique apres reload')
        except Exception:
            log_exc('MODE LIBRE : reload')
        return r
    bi.reload = reload
    _etat['reload'] = orig


def activer(mod=None, empreintes=EMPREINTES, racine=MY_COMMANDS, surveiller_reload=True, bavard=True):
    if _etat['actif']:
        return True
    try:
        mod = mod or _module()
        log('MODE LIBRE : module %s id=%s fichier=%s' % (MODULE, id(mod), getattr(mod, '__file__', '?')))
        pb = verifier(mod, empreintes, racine)
        if pb:
            dire(u'MODE LIBRE REFUSE : %s' % u'; '.join(pb))
            return False
        _appliquer(mod)
        if surveiller_reload:
            _installer_reload()
        _etat['actif'] = True
    except Exception:
        log_exc('MODE LIBRE : activation')
        _retirer()
        dire(u'MODE LIBRE : echec de l\'activation (voir journal.txt)')
        return False
    if not bavard:
        log('MODE LIBRE active')
        return True
    dire(u'*** MODE LIBRE ACTIVE *** zones de securite, rognages, raccords et collisions avec la piece ne sont plus '
         u'verifies. Limites physiques conservees. Desactive au prochain demarrage.')
    return True


def desactiver(bavard=True):
    _retirer()
    _etat['actif'] = False
    _etat['module'] = None
    (dire if bavard else log)(u'Mode libre desactive : Beamcut Soft fonctionne normalement.')


def basculer():
    """Bouton « Mode libre » : active ou désactive. Retourne le nouvel état."""
    if _etat['actif']:
        desactiver()
        return False
    return activer()
