# rutina-gimnasio

Aplicación personal para registrar pausas, movilidad, sesiones A/B/C, series, sensaciones y diario.

## Ejecutar en tu ordenador

Requiere Python 3.10 o posterior.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Configura una contraseña antes de iniciar la app:

```bash
# macOS/Linux
export APP_PASSWORD='una-clave-larga-y-privada'
streamlit run app.py
```

En Windows PowerShell:

```powershell
$env:APP_PASSWORD = 'una-clave-larga-y-privada'
streamlit run app.py
```

Por defecto, los datos quedan en `routine.db` en el ordenador donde corre la app. La interfaz incluye exportación e importación JSON.

## Acceder desde varios ordenadores

Para que la app se abra desde cualquier navegador, despliega este proyecto en un servicio que ejecute Streamlit. Configura `APP_PASSWORD` como secreto del servicio y conecta una base de datos PostgreSQL compartida mediante `DATABASE_URL`, por ejemplo:

```text
postgresql+psycopg://USUARIO:CONTRASEÑA@HOST:5432/BASE
```

En Streamlit Community Cloud, puedes configurar los secretos del despliegue así:

```toml
APP_PASSWORD = "una-clave-larga-y-privada"
DATABASE_URL = "postgresql+psycopg://USUARIO:CONTRASEÑA@HOST:5432/BASE"
```

No guardes contraseñas ni URL de base de datos en el repositorio. Usa los secretos privados del proveedor. SQLite local no sincroniza datos entre ordenadores; para compartir registros entre dispositivos se necesita una base de datos PostgreSQL persistente.

> El diario puede contener datos personales. Protege el enlace y la contraseña; la autenticación sencilla incluida está pensada para uso personal y no reemplaza un sistema de cuentas multiusuario.

La versión web anterior sigue disponible en `index.html`.
