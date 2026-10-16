# -*- coding: utf-8 -*-
# beamforge - bouton « Diagnostic »
from vcCommand import *
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _bf import ICI, JOURNAL, log, dire

app = getApplication()
cmd = getCommand()


def etat_principal():
    log('Diagnostic : python %s' % sys.version.replace('\n', ' '))
    try:
        v = open(os.path.join(ICI, 'VERSION.txt')).read().strip()
    except Exception:
        v = '?'
    dire(u"beamforge %s fonctionne. Journal : %s" % (v, JOURNAL))
    try:
        import _libre
        pb = _libre.verifier(_libre._module(), racine=None)
        dire(u"Importer DSTV libre : compatible avec cette version de Beamcut : %s"
             % (u'oui' if not pb else u'NON (' + u'; '.join(pb) + u')'))
    except Exception:
        log('Diagnostic mode libre impossible')
    cmd.setNextState(None)


cmd.addState(etat_principal)
