"""Container bootstrap only: retain runtime data across releases."""
import os
import shutil
from pathlib import Path

if __name__ == '__main__':
    destination = Path('/app/backend/data')
    destination.mkdir(parents=True, exist_ok=True)
    for source in Path('/app/seed-data').iterdir():
        # Packaged reference data only; private databases/uploads are never in the image.
        if source.is_file() and not (destination / source.name).exists():
            shutil.copy2(source, destination / source.name)
    os.execvp('uvicorn', ['uvicorn', 'backend.main:app', '--host', '0.0.0.0',
                        '--port', os.environ.get('PORT', '8000'), '--workers', '1',
                        '--proxy-headers', '--forwarded-allow-ips',
                        os.environ.get('FORWARDED_ALLOW_IPS', '127.0.0.1')])
