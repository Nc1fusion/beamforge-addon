"""Tests du mode libre hors de Visual Components : faux modules qui imitent les fonctions de
BeamCutSoft 2026 visées (mêmes noms, mêmes signatures, mêmes variables locales)."""
import base64, os, sys, tempfile, types

ADDON = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'beamforge')
SORTIE = []

# --- faux modules de l'environnement Visual Components ---------------------------------------
bf = types.ModuleType('_bf')
bf.ICI = ADDON
bf.log = lambda m: None
bf.log_exc = lambda t: (_ for _ in ()).throw(AssertionError('exception : ' + t))
bf.dire = lambda m: SORTIE.append(m)
sys.modules['_bf'] = bf


class vcVectorT(object):
    def __init__(self, x, y):
        self.X, self.Y = x, y


vcVectorT.__name__ = 'vcVector'
vcv = types.ModuleType('vcVector')
vcv.new = lambda v: vcVectorT(v.X, v.Y)
sys.modules['vcVector'] = vcv

COMMENTS = []
lib = types.ModuleType('LIB'); rsl = types.ModuleType('LIB.rslProgram')
rsl.addCommentToRoutine = lambda c, r, index=-1: COMMENTS.append((c, index))
lib.rslProgram = rsl
sys.modules['LIB'] = lib; sys.modules['LIB.rslProgram'] = rsl


def fabriquer_beamcut():
    m = types.ModuleType('LIB.dstvProcess')
    m.CHANNEL, m.HBEAM, m.TUBE, m.LANGLE, m.BULBFLAT, m.TBEAM = 3, 1, 2, 4, 5, 6

    class Beam(object):
        profileCode = 3

    class mainProcess_Def(object):
        def __init__(self, msg='IK Definition too close to inside flange of the CHANNEL'):
            self.beamDef = Beam(); self.filePath = 'C:/x/piece.nc1'; self.msg = msg
            self.doHolesDrillOnly = False; self.trous = 0
            self.motion = types.SimpleNamespace(rslPrg=types.SimpleNamespace(MainRoutine='MAIN'))

        def chkHoleDiamRatioThick(self, folderProcess=False):
            self.trous += 1

        def isFeatureOkCHANNEL(self):
            self.errMsgInSafeZone = self.msg
            return False

        def isFeatureOk(self, folderProcess=False, isTestPiece=False):
            raise AssertionError('question « Do you want the path to be modified ? » posée')

        def processSectionsV2(self):
            return 'fait'

    class processSI_BO_IK_KO_Def(object):
        curFace = 'v'

        def adjustInXYMaterial(self, workList, removeItm=True, applyOffset=True, isSIKO=False):
            return [v for v in workList if 30 <= v.Y <= 270]      # rognage dans la zone permise

    class setSections_def(object):
        def __init__(self):
            self.modifie = False

        def removeUnCompleteWeldPrep3(self):
            self.modifie = True

    class Coll(object):
        def __init__(self, touche):
            self.touche = touche; self.Enabled = False

        def testOneCollision(self, tol):
            return self.touche

        def getHitNodeA(self, i):
            return types.SimpleNamespace(Name='Torche')

        def getHitNodeB(self, i):
            return types.SimpleNamespace(Name='Aile')

    class motionStmtDef(object):
        def __init__(self, axes_ok=True):
            self.lLayoutColl = [Coll(False), Coll(True)]; self.axes_ok = axes_ok

        def checkIfErrorsInRoutine(self, routine):
            if routine == 'PARENT':
                self.checkIfErrorsInRoutine('ENFANT')       # appel récursif comme dans Beamcut
            routineName, stmtName = routine, 'P12'
            for iColl in self.lLayoutColl:
                if iColl.testOneCollision(0.05):
                    self.errMotionTest = '%s; %s; Collision' % (routineName, stmtName)
                    return True
            if not self.axes_ok:
                self.errMotionTest = 'One or more joints exceeding limits'
                return True
            return False

    for c in (mainProcess_Def, processSI_BO_IK_KO_Def, setSections_def, motionStmtDef):
        setattr(m, c.__name__, c)
    m.Coll = Coll
    return m


sys.path.insert(0, ADDON)
import _libre  # noqa: E402

SANS_EMPREINTE = {k: None for k in _libre.EMPREINTES}


def nouveau():
    if _libre.actif():
        _libre.desactiver()
    del SORTIE[:]; del COMMENTS[:]
    m = fabriquer_beamcut()
    assert _libre.activer(m, SANS_EMPREINTE, racine=None)
    return m


def test_zones_de_securite_ignorees_sans_question():
    m = nouveau()
    p = m.mainProcess_Def()
    assert p.isFeatureOk(True) is True and p.trous == 1
    assert any('too close to inside flange' in s for s in _libre._rapport['items'])
    assert any('MODE LIBRE ACTIF' in s for s in SORTIE)


def test_limite_physique_conservee():
    m = nouveau()
    p = m.mainProcess_Def(msg='IK Definition too close\nCannot go underneath')
    assert p.isFeatureOk() is False and p.isFeatureOkMsg == 'Cannot go underneath'


def test_rognage_neutralise():
    m = nouveau()
    pts = [vcVectorT(10, 5), vcVectorT(10, 100), vcVectorT(10, 295)]
    res = m.processSI_BO_IK_KO_Def().adjustInXYMaterial(pts, applyOffset=False)
    assert [(v.X, v.Y) for v in res] == [(10, 5), (10, 100), (10, 295)]
    assert all(a is not b for a, b in zip(res, pts))           # copies, comme Beamcut


def test_chanfreins_non_modifies():
    m = nouveau()
    s = m.setSections_def(); s.removeUnCompleteWeldPrep3()
    assert s.modifie is False


def test_collision_notee_mais_axes_gardes():
    m = nouveau()
    mo = m.motionStmtDef()
    assert mo.checkIfErrorsInRoutine('PARENT') is False
    assert all(type(c).__name__ == 'Coll' for c in mo.lLayoutColl)   # détecteurs rendus
    assert any('COLLISION PARENT / P12 : Torche contre Aile' in t for t in _libre._rapport['items'])
    assert m.motionStmtDef(axes_ok=False).checkIfErrorsInRoutine('Z1') is True


def test_marque_et_resume():
    m = nouveau()
    p = m.mainProcess_Def(); p.isFeatureOk()
    assert p.processSectionsV2() == 'fait'
    assert COMMENTS == [(_libre.MARQUE_LS, 0)] and len(_libre.MARQUE_LS) <= 30
    assert any('NON verifie' in s for s in SORTIE)


def test_desactivation_restaure_beamcut():
    m = nouveau()
    _libre.desactiver()
    try:
        m.mainProcess_Def().isFeatureOk()
        assert False, 'la fonction originale aurait dû être rendue'
    except AssertionError as e:
        assert 'question' in str(e)
    assert m.setSections_def.removeUnCompleteWeldPrep3.__name__ == 'removeUnCompleteWeldPrep3'
    s = m.setSections_def(); s.removeUnCompleteWeldPrep3(); assert s.modifie


def test_empreinte_differente_refusee():
    if _libre.actif():
        _libre.desactiver()
    m = fabriquer_beamcut()
    assert _libre.activer(m, dict(_libre.EMPREINTES), racine=None) is False
    assert not _libre.actif() and any('a change' in s for s in SORTIE)


def test_reapplique_apres_reload():
    import builtins
    m = nouveau()
    _libre.desactiver()
    _libre._etat['reload'] = None
    builtins.reload = lambda mod: fabriquer_beamcut()       # Beamcut : reload(LIB.dstvProcess)
    try:
        assert _libre.activer(m, SANS_EMPREINTE, racine=None)
        _libre.verifier.__defaults__ = (SANS_EMPREINTE, None)
        neuf = builtins.reload(m)
        assert neuf.mainProcess_Def().isFeatureOk() is True    # mode libre toujours actif
    finally:
        _libre.verifier.__defaults__ = (_libre.EMPREINTES, _libre.MY_COMMANDS)
        del builtins.reload
        _libre._etat['reload'] = None
        _libre.desactiver()


def test_commandes_utilisent_dstvProcess():
    d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, 'MnuFile'))
    for nom in ('MnuFileDSTV.py', 'MnuFolderDSTV.py'):
        with open(os.path.join(d, 'MnuFile', nom), 'wb') as f:
            f.write(b'BYTECODE(271)' + base64.b64encode(b'...LIB.dstvProcess...mainProcess_Def...'))
    assert _libre._commandes_utilisent_module(d) == (True, '')
    with open(os.path.join(d, 'MnuFile', 'MnuFolderDSTV.py'), 'wb') as f:
        f.write(b'BYTECODE(271)' + base64.b64encode(b'...LIB.mainProcess...'))
    assert _libre._commandes_utilisent_module(d)[0] is False


if __name__ == '__main__':
    for n, f in list(globals().items()):
        if n.startswith('test_'):
            f(); print('OK', n)
