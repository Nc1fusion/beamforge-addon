# -*- coding: utf-8 -*-
# beamforge - bouton « Mode libre » : active / desactive l'import sans restrictions (voir _libre.py).
# Etat en memoire seulement : toujours desactive au demarrage de BeamCutSoft.
from vcCommand import *
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _bf import log_exc
import _libre

app = getApplication()
cmd = getCommand()


def etat_principal():
    try:
        _libre.basculer()
    except Exception:
        log_exc('Mode libre')
    cmd.setNextState(None)


cmd.addState(etat_principal)
