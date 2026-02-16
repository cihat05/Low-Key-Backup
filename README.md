# Low-Key-Backup
A simple backup software designed for non-technical users. Backups are performed using rsync. The software does nothing more than back up data from A to B over SSH. The software have a GUI whihch has to be used.
Eine einfache Backup-Software für nicht-technische Benutzer. Es werden lediglich Daten von A nach B per SSH und dem Befehl rsync gesichert. Die Software hat eine GUI, mit der man Backups einrichtet. 

# Important
Prerequisite for using the software: the hosts already know each other and have exchanged SSH keys.
Wichtig für die Benutzung der Software: Die Hosts müssen sich kennen und schon einmal den SSH Key ausgetauscht haben 

## Installation (root)
```bash
unzip lowkey-backup.zip
cd lowkey-backup
sudo ./install.sh
```
## Gui:
Web: http://localhost:8585
## Services:
```bash
systemctl status lowkey-backup
systemctl stop lowkey-backup
systemctl start lowkey-backup
journalctl -u lowkey-backup -f
```

## Data/Logs
- DB: /var/lib/lowkey-backup/lowkey-backup.sqlite3
- Logs: /var/log/lowkey-backup/
- Software: /opt/lowkey-backup/

## Planung
Cron is not in use. Just working with internal scheduler (APScheduler) for backup tasks where jobs loaded from the db with day/time. 
Kein cron. Interner Scheduler (APScheduler) lädt Jobs aus der DB und führt sie zu den gewählten Tagen/Uhrzeiten aus.

## Funktionsweise der Software
Source: What should be backed up? You provide the credentials of the source host, connect to it, and scan the path that needs to be backed up.
Destination: Where should the backup be stored? You provide the credentials of the destination host, connect to it, and scan the target path where the backup will be saved.
You define the days and time when the backup should run, as well as the backup type.
Full: Performs a full backup.
INCR: Is a full backup available? Yes → Perform an incr backup OR No → Create a full backup -> Once a full backup exists → Perform incr backups.

Source: Was soll gesichert werden? Man gibt credentials des Source-Hosts an, verbindet sich damit, durchsucht den zu sichernden Pfad.
Destination: Wohin soll gesichert werden? Man gibt credentials des Destination-Hosts an, verbindet sich damit, durchsucht den abzulegenden Pfad.
Man stellt die Tage und die Uhrzeit ein und welche Art des Backups durchgeführt werden soll. 
Full: Full Backup 
INCR: Ist Full vorhanden? Ja? -> Incr Backup ODER Ist Full vorhanden? Nein? -> Erzeuge Full -> Wurde nun ein Full erzeugt ? Ja? -> Incr Backup
