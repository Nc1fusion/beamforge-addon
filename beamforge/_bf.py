# -*- coding: utf-8 -*-
# beamforge - outils communs (Python 2.7 de BeamCutSoft / Visual Components 4.2)
import os, datetime, traceback, ConfigParser, urllib


def _dossier(fichier):
    """Dossier d'un fichier, meme si BeamCutSoft le donne sous la forme 'file:C:/.../My+Commands/...'."""
    f = fichier
    for prefixe in ('file:///', 'file://', 'file:'):
        if f.lower().startswith(prefixe):
            f = urllib.unquote_plus(f[len(prefixe):])
            break
    return os.path.dirname(os.path.abspath(f.replace('/', os.sep)))


ICI = _dossier(__file__)
JOURNAL = os.path.join(ICI, 'journal.txt')
CONFIG = os.path.join(ICI, 'config.ini')


def log(msg):
    """Ligne dans journal.txt (diagnostic a distance)."""
    try:
        if isinstance(msg, unicode):
            msg = msg.encode('utf-8')
        f = open(JOURNAL, 'a')
        f.write('%s  %s\n' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg))
        f.close()
    except Exception:
        pass


def log_exc(titre):
    log('%s\n%s' % (titre, traceback.format_exc()))


def dire(msg):
    """Message pour l'utilisateur : panneau Sortie + journal. (Pas de messageBox : BeamCutSoft se bloquait.)"""
    log(msg)
    try:
        print(u'[beamforge] %s' % msg)
    except Exception:
        pass


def _lire():
    c = ConfigParser.ConfigParser()
    c.optionxform = str
    c.read(CONFIG)
    return c


def cfg(section, cle, defaut=''):
    try:
        return _lire().get(section, cle).strip()
    except Exception:
        return defaut


def set_cfg(section, cle, valeur):
    c = _lire()
    if not c.has_section(section):
        c.add_section(section)
    if isinstance(valeur, unicode):
        valeur = valeur.encode('utf-8')
    c.set(section, cle, valeur)
    f = open(CONFIG, 'w')
    c.write(f)
    f.close()


def vers_uri(chemin):
    return 'file:///' + chemin.replace('\\', '/')


def depuis_uri(valeur):
    v = (valeur or '').strip()
    if v.startswith('file:///'):
        v = v[8:]
    return v.replace('/', '\\')
