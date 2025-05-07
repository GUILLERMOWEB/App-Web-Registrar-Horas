
-- *******************************************************
-- INSERTAR NUEVOS USUARIOS
-- *******************************************************

-- Insertar un nuevo superadmin
INSERT INTO usuarios (nombre, email, password, rol) 
VALUES ('Super Admin', 'superadmin@empresa.com', 'contraseña_segura', 'superadmin');

-- Insertar un nuevo administrador
INSERT INTO usuarios (nombre, email, password, rol) 
VALUES ('Administrador Principal', 'admin@empresa.com', 'contraseña_segura', 'admin');

-- *******************************************************
-- INSERTAR CLIENTES
-- *******************************************************

-- Insertar un cliente (ejemplo: Cliente A)
INSERT INTO clientes (nombre, email, telefono, direccion) 
VALUES ('Cliente A', 'clienteA@empresa.com', '123456789', 'Calle Principal 456');

-- Insertar otro cliente (ejemplo: Cliente B)
INSERT INTO clientes (nombre, email, telefono, direccion) 
VALUES ('Cliente B', 'clienteB@empresa.com', '987654321', 'Calle Secundaria 789');

-- *******************************************************
-- ACTUALIZAR REGISTROS EXISTENTES
-- *******************************************************

-- Actualizar un usuario para asignarle el rol de 'admin'
UPDATE usuarios
SET rol = 'admin'
WHERE nombre = 'Juan Pérez';

-- Actualizar la dirección de un cliente
UPDATE clientes
SET direccion = 'Calle Nueva 123'
WHERE nombre = 'Cliente A';

-- *******************************************************
-- CREAR UNA TABLA PARA REGISTROS DE HORAS
-- *******************************************************

-- Crear la tabla de registros de horas (si no existe)
CREATE TABLE IF NOT EXISTS registros_horas (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL,
    cliente_id INT NOT NULL,
    fecha DATE NOT NULL,
    hora_entrada TIME NOT NULL,
    hora_salida TIME NOT NULL,
    horas_trabajadas INT NOT NULL,
    horas_viaje_ida INT DEFAULT 0,
    horas_viaje_vuelta INT DEFAULT 0,
    km_ida INT DEFAULT 0,
    km_vuelta INT DEFAULT 0,
    comentarios TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

-- *******************************************************
-- INSERTAR REGISTROS DE HORAS DE EJEMPLO
-- *******************************************************

-- Insertar un registro de horas para un usuario y cliente específico
INSERT INTO registros_horas (usuario_id, cliente_id, fecha, hora_entrada, hora_salida, horas_trabajadas, horas_viaje_ida, horas_viaje_vuelta, km_ida, km_vuelta, comentarios)
VALUES (1, 1, '2025-05-01', '08:00:00', '17:00:00', 8, 1, 1, 50, 50, 'Trabajo en proyecto A');

-- Insertar otro registro de horas para otro cliente
INSERT INTO registros_horas (usuario_id, cliente_id, fecha, hora_entrada, hora_salida, horas_trabajadas, horas_viaje_ida, horas_viaje_vuelta, km_ida, km_vuelta, comentarios)
VALUES (2, 2, '2025-05-02', '09:00:00', '18:00:00', 8, 1, 1, 60, 60, 'Reunión con Cliente B');

-- *******************************************************
-- AGREGAR NUEVAS COLUMNAS O MODIFICAR LA ESTRUCTURA
-- *******************************************************

-- Si deseas agregar nuevas columnas a la tabla de 'usuarios' (ejemplo: teléfono)
ALTER TABLE usuarios ADD COLUMN telefono VARCHAR(15);

-- Si deseas modificar el tipo de datos de alguna columna
ALTER TABLE usuarios ALTER COLUMN password TYPE VARCHAR(255);

-- *******************************************************
-- ELIMINAR REGISTROS NO NECESARIOS
-- *******************************************************

-- Eliminar un usuario que ya no se necesita
DELETE FROM usuarios
WHERE email = 'usuario@empresa.com';

-- Eliminar un cliente que ya no existe
DELETE FROM clientes
WHERE email = 'clienteC@empresa.com';

-- *******************************************************
-- CONSULTAS DE MANTENIMIENTO
-- *******************************************************

-- Consultar todos los usuarios con rol de 'admin'
SELECT * FROM usuarios WHERE rol = 'admin';

-- Consultar todos los registros de horas de un usuario específico
SELECT * FROM registros_horas WHERE usuario_id = 1;

-- Consultar los clientes con más de 3 registros de horas
SELECT clientes.nombre, COUNT(registros_horas.id) AS cantidad_registros
FROM clientes
JOIN registros_horas ON clientes.id = registros_horas.cliente_id
GROUP BY clientes.nombre
HAVING COUNT(registros_horas.id) > 3;
