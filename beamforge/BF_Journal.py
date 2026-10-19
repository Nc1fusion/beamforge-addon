# -*- coding: utf-8 -*-
# beamforge - bouton « Envoyer journal »
# Prepare journal_beamforge.txt (fin du journal + versions) sur le Bureau, le copie dans le
# presse-papiers Windows et ouvre l'Explorateur avec le fichier selectionne :
# il ne reste qu'a faire Ctrl+V (ou glisser le fichier) dans la conversation Claude.
from vcCommand import *
import os, sys, subprocess, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _bf import ICI, JOURNAL, log, log_exc, dire

app = getApplication()
cmd = getCommand()

DERNIERES_LIGNES = 3000          # assez pour plusieurs imports, sans envoyer tout l'historique
SANS_FENETRE = 0x08000000        # CREATE_NO_WINDOW : pas de console noire


def _bureau():
    """Dossier Bureau reel (gere la redirection OneDrive), sinon le dossier de l'add-on."""
    try:
        import _winreg
        k = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                            r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders')
        v = os.path.expandvars(_winreg.QueryValueEx(k, 'Desktop')[0])
        if os.path.isdir(v):
            return v
    except Exception:
        pass
    v = os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
    return v if os.path.isdir(v) else ICI


def _entete():
    lignes = ['beamforge - journal envoye le %s' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
    for nom, chemin in (('beamforge', os.path.join(ICI, 'VERSION.txt')),
                        ('BeamCutSoft', os.path.join(os.path.dirname(ICI), 'versioninfo.txt'))):
        try:
            lignes.append('%s : %s' % (nom, open(chemin).read().strip()))
        except Exception:
            lignes.append('%s : ?' % nom)
    lignes.append('python : %s' % sys.version.replace('\n', ' '))
    lignes.append('-' * 70)
    return '\n'.join(lignes) + '\n'


def etat_principal():
    try:
        try:
            contenu = open(JOURNAL).readlines()
        except IOError:
            contenu = ['(journal vide)\n']
        cible = os.path.join(_bureau(), 'journal_beamforge.txt')
        f = open(cible, 'w')
        f.write(_entete())
        f.writelines(contenu[-DERNIERES_LIGNES:])
        f.close()
        log('Journal prepare : %s' % cible)
        try:      # fichier dans le presse-papiers (Ctrl+V dans Claude)
            subprocess.Popen(['powershell', '-NoProfile', '-Command',
                              "Set-Clipboard -Path '%s'" % cible.replace("'", "''")],
                             creationflags=SANS_FENETRE)
        except Exception:
            log_exc('Presse-papiers')
        try:      # Explorateur, fichier selectionne (pour glisser-deposer)
            subprocess.Popen('explorer /select,"%s"' % cible)
        except Exception:
            log_exc('Explorateur')
        nom = cible.decode('mbcs', 'replace') if not isinstance(cible, type(u'')) else cible
        dire(u'Journal pret : %s - copie dans le presse-papiers. Dans Claude : Ctrl+V '
             u'(ou glissez le fichier depuis la fenetre ouverte).' % nom)
    except Exception:
        log_exc('Envoyer journal')
        dire(u'Envoyer journal : echec (voir journal.txt dans %s)' % ICI)
    cmd.setNextState(None)


cmd.addState(etat_principal)
