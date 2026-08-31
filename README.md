# MobPsy

MobPsy dispone de **un único punto de entrada**:

```text
MOBPSY.bat
```

No tienes que ejecutar instaladores, actualizadores ni scripts adicionales.

## Si usas la OVA

1. Descarga `MobPsy-vX.Y.Z.ova`.
2. Impórtala en Oracle VirtualBox.
3. Conserva el nombre de la VM como `MobPsy-Workstation`.
4. Descarga también este pequeño paquete/controlador de MobPsy o clona el repositorio.
5. Ejecuta `MOBPSY.bat`.

El panel detecta automáticamente que existe una **OVA importada** y la controla directamente mediante VirtualBox.

**La OVA NO necesita `.vagrant` ni necesita estar asociada al Vagrantfile.**

## Si prefieres instalar desde código

1. Instala Oracle VirtualBox y Vagrant.
2. Ejecuta `MOBPSY.bat`.
3. Selecciona **Instalar MobPsy desde código**.

En ese modo MobPsy usa el `Vagrantfile` incluido y Vagrant crea localmente `.vagrant`.

## Menú único

Desde `MOBPSY.bat` puedes:

- detectar si estás usando OVA o instalación desde código;
- instalar desde código;
- iniciar y apagar MobPsy;
- ejecutar diagnóstico;
- comprobar actualizaciones;
- actualizar MobPsy desde GitHub Releases;
- realizar mantenimiento granular cuando la instalación es Vagrant.

### Importante sobre `.vagrant`

`.vagrant` es estado **local** de Vagrant: UUID de la VM, metadatos del proveedor y datos del equipo donde se creó.

**Nunca debe subirse a GitHub y nunca debe incluirse junto a la OVA.**

El `Vagrantfile` sí se publica, pero únicamente para usuarios que quieran construir MobPsy desde código.

Repositorio oficial: https://github.com/alvarosr/mobpsy
