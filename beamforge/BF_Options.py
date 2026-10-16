# -*- coding: utf-8 -*-
# beamforge - bouton « Options » : panneau de reglages, enregistres dans config.ini
from vcCommand import *
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _bf import cfg, set_cfg, log, log_exc, vers_uri, depuis_uri

app = getApplication()
cmd = getCommand()

# (nom affiche, type, section, cle, defaut)
REGLAGES = [
    (u'Cellule BC25',        VC_URI,     'cellules', 'BC25', ''),
    (u'Cellule BC50',        VC_URI,     'cellules', 'BC50', ''),
    (u'Vider la scene avant d ouvrir', VC_BOOLEAN, 'options', 'vider_scene', 'True'),
    (u'Programmer sur BC25', VC_BOOLEAN, 'options',  'programmer_BC25', 'True'),
    (u'Programmer sur BC50', VC_BOOLEAN, 'options',  'programmer_BC50', 'True'),
    (u'Dossier des .LS',     VC_STRING,  'sortie',   'dossier', ''),
]


def _sur_changement(prop):          # vcProperty.OnChanged(vcProperty) - doc 4.2
    try:
        for nom, typ, sec, cle, defaut in REGLAGES:
            if prop.Name == nom:
                val = depuis_uri(prop.Value) if typ == VC_URI else prop.Value
                set_cfg(sec, cle, unicode(val))
                log('Option %s = %s' % (cle, val))
    except Exception:
        log_exc('Enregistrement option')


for nom, typ, sec, cle, defaut in REGLAGES:
    p = cmd.getProperty(nom) or cmd.createProperty(typ, nom)
    v = cfg(sec, cle, defaut)
    try:
        if typ == VC_BOOLEAN:
            p.Value = (v == 'True')
        elif typ == VC_URI:
            p.Value = vers_uri(v) if v else ''
        else:
            p.Value = v
    except Exception:
        log_exc('Valeur initiale %s' % nom)
    p.OnChanged = _sur_changement


def etat_principal():
    try:
        executeInActionPanel()      # panneau a droite (verifie a l'atelier)
    except Exception:
        log_exc('executeInActionPanel')


cmd.addState(etat_principal)
