# Sistema de Agua

## Backups de base de datos

Crear un backup de PostgreSQL:

```bash
bash scripts/backup_db.sh
```

Los archivos se guardan en `backups/` y no se suben a git.

Restaurar un backup:

```bash
bash scripts/restore_db.sh backups/nombre_del_backup.dump
```

La restauración pide escribir `RESTAURAR` antes de reemplazar la base de datos.
