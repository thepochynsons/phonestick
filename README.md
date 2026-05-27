# Ultrasound Phone Joystick

Aplicacion Django + React para visualizar una malla de un transductor de ecografo y moverla con el acelerometro de un celular usado como joystick.

La pantalla principal crea una sala y muestra un QR. El celular entra a `/controller/<sala>`, pide permiso para usar sensores y envia datos por WebSocket al backend Django Channels. La vista 3D recibe esos datos y mueve/rota el transductor en Three.js.

## Estructura

- `backend/`: Django 3.2 + Channels.
- `frontend/`: React + Vite + Three.js.
- `frontend/public/models/transducer.stl`: ubicacion esperada para el STL principal.

## Cargar la malla real

El proyecto incluye una malla procedural para poder probarlo de inmediato. Para usar otro modelo STL, copia el archivo principal como:

```bash
frontend/public/models/transducer.stl
```

Al recargar la app, la escena intentara usar ese archivo automaticamente.

## Ejecutar backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd backend
python manage.py migrate
daphne -b 0.0.0.0 -p 8000 ultrasound_joystick.asgi:application
```

## Ejecutar frontend

```bash
cd frontend
npm install
npm run dev
```

Abrir la app en:

```text
http://localhost:5173
```

## Ejecutar con Docker

Si no quieres instalar Node o pip en el host:

```bash
docker compose up --build
```

## Conectar desde el celular

1. Busca la IP LAN de la computadora donde corre la app.

   En Linux:

   ```bash
   ip route get 1.1.1.1
   ```

   Usa la IP que aparece despues de `src`, por ejemplo `192.168.1.20`.

2. Levanta backend y frontend escuchando en toda la red.

   Con Docker:

   ```bash
   docker compose up --build
   ```

   Sin Docker, el backend ya usa `-b 0.0.0.0` y Vite ya usa `--host 0.0.0.0` por la configuracion del proyecto.

3. Abre la pantalla principal desde la computadora usando la IP LAN, no `localhost`:

   ```text
   http://192.168.1.20:5173
   ```

4. Escanea el QR con el celular o abre manualmente:

   ```text
   http://192.168.1.20:5173/controller/CODIGO_DE_SALA
   ```

5. En el celular toca `Activar sensores`.

Importante: si abres la pantalla principal en la computadora como `http://localhost:5173`, el QR tambien apuntara a `localhost`, y desde el celular eso no llega a tu computadora. Siempre usa la IP LAN para generar el QR.

Si el celular carga la pantalla pero no conecta el WebSocket, verifica que el firewall permita los puertos `5173` y `8000`.

## Calibracion inicial

La pantalla principal no mueve la malla hasta tomar una referencia. La sincronizacion tiene dos pasos separados:

- `Alineacion del modelo`: deja el STL mirando igual que el transductor real en la postura base.
- `Calibracion del celular`: toma la orientacion actual del celular como cero.

La escena tiene tres anclas:

- `FRENTE`: flecha verde. Define hacia donde mira la escena.
- `BOTON IZQ`: flecha azul. Define el lado izquierdo donde debe quedar el boton del transductor.
- `PUNTO FIJO`: aro central. El transductor no se traslada; rota alrededor de ese punto.

1. Conecta el celular y activa sensores.
2. En la computadora, usa los botones de alineacion para dejar el transductor centrado en `PUNTO FIJO`, con su frente hacia `FRENTE` y su boton hacia `BOTON IZQ`.
3. Coloca el celular en la postura base: boca abajo, con la camara o boton de bloqueo apuntando hacia el mismo lado que `BOTON IZQ`.
4. Coloca el transductor real en la misma postura base: boca abajo, con su boton hacia `BOTON IZQ`.
5. En la pantalla de la computadora presiona `Calibrar`.

Desde ese momento, la app resta esa orientacion inicial y mueve la malla de forma relativa al celular. Puedes presionar `Recalibrar` en cualquier momento para tomar una nueva referencia.

La alineacion del modelo queda guardada en el navegador de la computadora. `Alineacion base` vuelve a la orientacion inicial pensada para el celular boca abajo.

## Realismo del movimiento

El transductor queda fijo en el espacio. No se rastrea ni se simula traslacion espacial.

La app rastrea pitch/roll del dispositivo sobre sus propios ejes. Internamente usa cuaterniones para comparar la orientacion actual contra la orientacion calibrada, en vez de restar `alpha`, `beta` y `gamma` por separado. Esto evita mezclar ejes cuando el celular esta boca abajo o girado.

Por estabilidad, el giro tipo brujula/twist (`alpha`) esta desactivado. En Android puede saltar de 0 a 360 cuando el celular se inclina lateralmente, haciendo que el transductor parezca girar sobre su propio eje. La app no convierte inclinacion ni aceleracion en desplazamientos laterales.

La traslacion real del celular en el espacio no se puede reconstruir con precision usando solo sensores del navegador. Para una traslacion fisica real haria falta tracking adicional, por ejemplo camara/AR, marcadores visuales, WebXR, o un tracker externo.

## Nota sobre sensores del celular

En Android Chrome, si el controlador muestra `Permiso: no events`, mira estos campos en la pantalla del celular:

- `Contexto`: si dice `http local`, Chrome puede bloquear sensores por no ser un origen seguro.
- `Orientation API` y `Motion API`: deben decir `si`.
- `Accelerometer` y `Gyroscope`: si dicen `denied`, Chrome esta bloqueando permisos.
- `Fuente`: debe cambiar a `orientation` o `motion` cuando llegan eventos reales.

Revisa tambien:

- Chrome > Configuracion > Configuracion de sitios > Sensores de movimiento: activado.
- No usar modo incognito.
- Probar con la pantalla desbloqueada y el ahorro de bateria desactivado.
- Si sigue sin datos en una URL `http://192.168...`, usar HTTPS local o un tunel seguro. Algunas versiones de Chrome bloquean sensores en origenes no seguros aunque la pagina cargue bien.

El controlador tambien incluye un modo tactil: arrastra el dedo sobre el recuadro del telefono para enviar movimiento aunque los sensores esten bloqueados. Si eso mueve el transductor, la conexion WebSocket esta bien y el problema queda acotado al acceso del navegador a sensores.

### Probar sensores con USB y localhost

Chrome considera `localhost` como un origen seguro. Si tienes `adb` instalado, esta es la forma mas directa de probar sensores sin configurar HTTPS:

1. Activa opciones de desarrollador y depuracion USB en Android.
2. Conecta el celular por USB.
3. Levanta la app:

   ```bash
   docker compose up --build
   ```

4. En otra terminal:

   ```bash
   adb devices
   adb reverse tcp:5173 tcp:5173
   ```

5. En el celular abre:

   ```text
   http://localhost:5173
   ```

6. Entra al controlador y toca `Activar sensores`.

Si funciona, deberias ver `Contexto: seguro`, `Orientation API: si` o `Motion API: si`, y `Eventos` subiendo.

### Probar sensores con un tunel HTTPS

Tambien puedes usar un tunel HTTPS hacia el frontend. Como Vite proxyea `/ws` y `/api` al backend, solo necesitas exponer el puerto `5173`.

Opcion recomendada con Docker y Cloudflare Tunnel:

```bash
docker compose --profile tunnel up --build
```

Busca en los logs del servicio `tunnel` una URL parecida a:

```text
https://algo.trycloudflare.com
```

Abre esa URL HTTPS en la computadora, escanea el QR con el celular y toca `Activar sensores`.

Si prefieres ngrok, debe ejecutarse en otra terminal fuera de Docker Compose:

```bash
docker compose up --build
ngrok http 5173
```

El error `no such service: ngrok` aparece cuando se escribe `ngrok` como parte del comando de Docker Compose.

En iPhone/iOS, `DeviceOrientationEvent` normalmente requiere permiso explicito y casi siempre HTTPS. Si el boton "Activar sensores" no entrega datos, levanta Vite y Daphne detras de HTTPS local o usa un tunel seguro.
