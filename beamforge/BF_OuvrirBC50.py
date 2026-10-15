# -*- coding: utf-8 -*-
# beamforge - bouton « Ouvrir BC50 »
from vcCommand import *
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _bf import log_exc
from _ouvrir import ouvrir

app = getApplication()
cmd = getCommand()


def etat_principal():
    try:
        ouvrir(app, 'BC50')
    except Exception:
        log_exc('Ouvrir BC50')
    cmd.setNextState(None)      # fin de la commande apres cette fonction (doc 4.2)


cmd.addState(etat_principal)    # premiere fonction d'etat = appelee a l'execution (doc 4.2)
