# Guía de ejecución del proyecto
Pasos necesarios para ejecutar correctamente el proyecto utilizando **Docker**, **WSL2**, **ROS 2** y la simulación de **TurtleBot3**.

---

## Requisitos previos

1. Sistema base

Windows con WSL2 habilitado.

Docker Desktop instalado y configurado para usar WSL2.

Python 3 instalado en Windows.

2. ROS2

ROS 2 correctamente configurado dentro del contenedor Docker.

3. Dependencias de Python

En Windows: instalar dependencias usando requirements_win.txt.

Se recomienda crear un entorno virtual para evitar conflictos.

En el contenedor Docker: instalar dependencias usando requirements.txt.

4. Código y contenedor Docker

Clonar el repositorio con la imagen de Docker:

git clone https://github.com/fjrodl/ROS2andGazebo.git


Construir la imagen Docker:

cd ROSConES/Docker
docker build -t ros2roscon .


Levantar el contenedor:

docker compose up  

---

## Pasos de ejecución

### 1. Iniciar Docker Desktop

1. Abre **Docker Desktop**.
2. Espera a que la aplicación esté disponible y correctamente conectada con **WSL2**.

---

### 2. Preparar el entorno en WSL2

1. Abre una terminal de **WSL2**.
2. Accede al directorio del proyecto.

---

### 3. Configurar el servidor en Windows

1. Copia el archivo ejecutable:

   ```
   scripts/windows_server.py
   ```

   a cualquier ubicación de tu sistema de archivos de **Windows**.

2. En Windows, abre un **terminal como administrador**.

3. Navega hasta la ubicación donde copiaste el archivo y ejecútalo:

   ```bash
   python3 ./windows_server.py
   ```

4. Espera a que el servidor se haya iniciado y tenga todos sus servicios disponibles.

---

### 4. Lanzar el contenedor Docker

1. Lanza el contenedor del proyecto.
2. Una vez que el contenedor esté en ejecución, abre **dos terminales** dentro del contenedor.
3. En ambas terminales, accede al workspace de ROS 2:

   ```bash
   cd ros2_ws
   ```

---

## 5. Terminal 1 – Compilación y simulación

### 5.1 Compilar los paquetes

```bash
colcon build
```

### 5.2 Cargar el entorno de trabajo

```bash
source install/setup.bash
```

### 5.3 Exportar el modelo del robot

```bash
export TURTLEBOT3_MODEL="waAle"
```

### 5.4 Lanzar la simulación de TurtleBot3

```bash
ros2 launch turtlebot3 simulation.launch.py
```

### 5.5 Esperar a la simulación

Espera a que se carguen correctamente:

* Gazebo
* RViz
* Todos los nodos y elementos de la simulación

---

## 6. Terminal 2 – Control y navegación

### 6.1 Cargar el entorno de trabajo

```bash
source install/setup.bash
```

### 6.2 Lanzar el commander

Ejecuta el launcher del paquete `commander_bringup` para iniciar todos los nodos de control y navegación:

```bash
ros2 launch commander_bringup commander.launch.xml
```

---

## 7. Uso de la simulación

La simulación ya está en funcionamiento. Puedes interactuar con el robot y darle **comandos de voz** para:

* Navegar por el entorno
* Cambiar el planificador
* Cambiar el controlador
* Volver a posiciones anteriores

---

✅ **La simulación está lista para su uso.**
