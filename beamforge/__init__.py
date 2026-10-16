# -*- coding: utf-8 -*-
# beamforge - onglet BEAMFORGE pour BeamCutSoft (Visual Components 4.2).
# Ecrit d'apres l'API de la version installee (Python Editor\Auto Complete\api.xml).
# Ne modifie aucun fichier de Beamcut Soft. Pour l'enlever : supprimer ce dossier et redemarrer.
from vcApplication import *
import os, sys

import urllib


def _dossier_init():
    """BeamCutSoft passe __file__ sous la forme 'file:C:/.../My+Commands/beamforge/__init__.py'
    (constate a l'atelier) : on retire 'file:' et on decode les '+' et '%20'."""
    f = __file__
    for prefixe in ('file:///', 'file://', 'file:'):
        if f.lower().startswith(prefixe):
            f = f[len(prefixe):]
            break
    f = urllib.unquote_plus(f).replace('/', os.sep)
    return os.path.dirname(f)


sys.path.insert(0, _dossier_init())
from _bf import ICI, log, log_exc, vers_uri     # ICI de _bf = vrai dossier (verifie : journal.txt y est ecrit)

try:
    VERSION = open(os.path.join(ICI, 'VERSION.txt')).read().strip()
except Exception:
    VERSION = '?'
log('--- beamforge %s : chargement depuis %s (__file__ = %s)' % (VERSION, ICI, __file__))

ONGLET = 'BEAMFORGE'                 # nom affiche = identifiant (constate en 4.2)
REPLI = 'VcTabTeach/BEAMFORGE'       # groupe dans l'onglet PROGRAMME (forme documentee 'VcTabX/Groupe')
COMMANDES = [   # (nom de commande, fichier, texte du bouton, groupe)
    ('BF_OuvrirBC25', 'BF_OuvrirBC25.py', u'Ouvrir BC25', 'Cellules'),
    ('BF_OuvrirBC50', 'BF_OuvrirBC50.py', u'Ouvrir BC50', 'Cellules'),
    ('BF_Options',    'BF_Options.py',    u'Options',     'Reglages'),
    ('BF_Test',       'BF_Test.py',       u'Diagnostic',  'Aide'),
]


def _charger(nom, fichier):
    """loadCommand(nom, uri) : renvoie la commande, ou None en cas d'echec (doc 4.2)."""
    c = None
    try:
        c = loadCommand(nom, vers_uri(os.path.join(ICI, fichier)))     # verifie a l'atelier (essais 1-9)
    except Exception:
        log_exc('loadCommand %s' % nom)
    if c is None:
        try:
            c = loadCommand(nom, getApplicationPath() + fichier)       # forme de la doc 4.2
        except Exception:
            log_exc('loadCommand (getApplicationPath) %s' % nom)
    log('loadCommand %s : %s' % (nom, 'OK' if c is not None else 'ECHEC'))
    return c


def _creer_onglet():
    # Forme non documentee en 4.2 mais verifiee a l'atelier : cree un onglet nomme d'apres l'identifiant.
    try:
        addMenuItem(UxSite=ONGLET, UxName=u'BEAMFORGE', Index=-1, Id=ONGLET,
                    Parent='gmAction', ControlType='ContextualTabGroup', BaseBackColor='#1985ff')
        log('Onglet %s cree' % ONGLET)
        return True
    except Exception:
        log_exc('Onglet refuse : repli sur %s' % REPLI)
        return False


def OnAppInitialized():
    onglet = _creer_onglet()
    for nom, fichier, texte, groupe in COMMANDES:
        if _charger(nom, fichier) is None:
            continue
        menu = ('%s/%s' % (ONGLET, groupe)) if onglet else REPLI
        try:
            h = addMenuItem(menu, texte, -1, nom)      # (menu, caption, position, command) - doc 4.2
            log('Bouton %s -> %s (handle %r)' % (nom, menu, h))
        except Exception:
            log_exc('addMenuItem %s' % nom)
