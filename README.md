# Low-Key-Backup
A simple backup software designed for non-technical users. Backups are performed using rsync. The software does nothing more than back up data from A to B over SSH. The software have a GUI
# Important
Prerequisite for using the software: the hosts already know each other and have exchanged SSH keys.

## Installation (root)
```bash
unzip lowkey-backup.zip
cd lowkey-backup
sudo ./install.sh
```
## Gui:
Web: http://<host>:8585
## Services:
```bash
systemctl status lowkey-backup
journalctl -u lowkey-backup -f
```

## Daten/Logs
- DB: /var/lib/lowkey-backup/lowkey-backup.sqlite3
- Logs: /var/log/lowkey-backup/
- Software: /opt/lowkey-backup/

## Planung
Kein cron. Interner Scheduler (APScheduler) lädt Jobs aus der DB und führt sie zu den gewählten Tagen/Uhrzeiten aus.
