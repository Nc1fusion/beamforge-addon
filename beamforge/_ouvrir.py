# -*- coding: utf-8 -*-
# Ouverture d'une cellule .vcmx avec la commande integree « loadLayout(String uri) » (api.xml 4.2).
# NE PAS utiliser app.load() : il charge un COMPOSANT (gel de BeamCutSoft avec une cellule entiere).
import os
from _bf import cfg, log, log_exc, vers_uri, depuis_uri, dire


def chemin_cellule(app, machine):
    chemin = cfg('cellules', machine)
    if not chemin:      # repli : valeur affichee dans le panneau Options
        try:
            c = app.findCommand('BF_Options')
            p = c.getProperty(u'Cellule %s' % machine) if c is not None else None
            chemin = depuis_uri(p.Value) if p is not None else ''
        except Exception:
            log_exc('Lecture du panneau Options')
    return chemin


def ouvrir(app, machine):
    chemin = chemin_cellule(app, machine)
    if not chemin or not chemin.lower().endswith('.vcmx') or not os.path.exists(chemin):
        dire(u"Cellule %s : choisissez le fichier .vcmx dans Options (actuel : %s)." % (machine, chemin))
        return
    cmd = app.findCommand('loadLayout')
    if cmd is None:
        dire(u"Commande loadLayout introuvable : ouverture impossible.")
        return
    if cfg('options', 'vider_scene', 'True') == 'True':
        # Commande integree de la 4.2 (api.xml) : equivalent de « Nouveau » (devrait proposer d'enregistrer).
        vider = app.findCommand('interactiveClearWorld')
        if vider is None:
            dire(u"Commande interactiveClearWorld introuvable : la cellule sera ajoutee a la scene.")
        else:
            try:
                vider.execute()
                log('interactiveClearWorld execute')
            except Exception:
                log_exc('interactiveClearWorld')
                dire(u"Impossible de vider la scene : ouverture annulee (voir journal.txt).")
                return
    dire(u"Ouverture de la cellule %s : %s" % (machine, chemin))
    try:
        cmd.execute(vers_uri(chemin))
        log('loadLayout termine : %s' % chemin)
    except Exception:
        log_exc('loadLayout %s' % chemin)
        dire(u"Echec de l'ouverture de la cellule %s (voir journal.txt)." % machine)
