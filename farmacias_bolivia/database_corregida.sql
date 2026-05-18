-- database_corregida.sql
-- Script de corrección de esquema para la aplicación Farmacias Bolivia.
-- Ejecutar en la base de datos: farmacias_bolivia

USE farmacias_bolivia;

-- =====================================================
-- TABLA cliente: agregar campos que el código actual espera
-- =====================================================
ALTER TABLE cliente
  ADD COLUMN nombre varchar(100) DEFAULT NULL,
  ADD COLUMN apellido_paterno varchar(100) DEFAULT NULL,
  ADD COLUMN apellido_materno varchar(100) DEFAULT NULL,
  ADD COLUMN activo tinyint(1) NOT NULL DEFAULT 1;

UPDATE cliente
SET nombre = nombres,
    apellido_paterno = apellidos,
    apellido_materno = ''
WHERE nombre IS NULL OR apellido_paterno IS NULL OR apellido_materno IS NULL;

-- =====================================================
-- TABLA usuario: agregar campos que el código de auth espera
-- =====================================================
ALTER TABLE usuario
  ADD COLUMN ci varchar(15) DEFAULT NULL,
  ADD COLUMN nombre varchar(100) DEFAULT NULL,
  ADD COLUMN apellido_paterno varchar(100) DEFAULT NULL,
  ADD COLUMN email varchar(100) DEFAULT NULL,
  ADD COLUMN password_hash varchar(255) DEFAULT NULL,
  ADD COLUMN activo tinyint(1) NOT NULL DEFAULT 1;

UPDATE usuario
SET ci = nombre_usuario,
    nombre = nombre_usuario,
    apellido_paterno = '',
    password_hash = contrasena
WHERE ci IS NULL OR nombre IS NULL OR apellido_paterno IS NULL OR password_hash IS NULL;

-- =====================================================
-- TABLA medicamento: agregar campos usados por templates/admin
-- =====================================================
ALTER TABLE medicamento
  ADD COLUMN principio_activo varchar(100) DEFAULT NULL,
  ADD COLUMN forma_farmaceutica varchar(100) DEFAULT NULL,
  ADD COLUMN precio_compra decimal(10,2) NOT NULL DEFAULT 0.00,
  ADD COLUMN activo tinyint(1) NOT NULL DEFAULT 1,
  ADD COLUMN requiere_refrigeracion tinyint(1) NOT NULL DEFAULT 0;

-- =====================================================
-- TABLA inventario: agregar columnas necesarias para templates
-- =====================================================
ALTER TABLE inventario
  ADD COLUMN ubicacion_almacen varchar(200) DEFAULT NULL,
  ADD COLUMN cantidad int(11) AS (stock_actual) STORED;

-- =====================================================
-- VISTA vista_pedidos_pendientes
-- =====================================================
DROP VIEW IF EXISTS vista_pedidos_pendientes;
CREATE VIEW vista_pedidos_pendientes AS
SELECT p.id_pedido,
       p.id_cliente,
       p.numero_pedido,
       p.subtotal,
       p.iva,
       p.total,
       p.metodo_pago,
       p.direccion_entrega,
       p.telefono_contacto,
       p.estado AS estado_pedido,
       p.fecha AS fecha_pedido,
       p.receta_medica,
       CONCAT(c.nombre, ' ', c.apellido_paterno, ' ', COALESCE(c.apellido_materno, '')) AS cliente,
       c.ci,
       c.nombre,
       c.apellido_paterno,
       c.apellido_materno,
       c.email,
       c.telefono
FROM pedido p
JOIN cliente c ON p.id_cliente = c.id_cliente
WHERE p.estado = 'PENDIENTE';

-- =====================================================
-- VISTA vista_proximos_vencer
-- =====================================================
DROP VIEW IF EXISTS vista_proximos_vencer;
CREATE VIEW vista_proximos_vencer AS
SELECT l.id_lote,
       l.id_medicamento,
       m.nombre_comercial,
       l.numero_lote AS codigo_lote,
       l.fecha_vencimiento,
       DATEDIFF(l.fecha_vencimiento, CURDATE()) AS dias_restantes
FROM lote l
JOIN medicamento m ON l.id_medicamento = m.id_medicamento
WHERE l.fecha_vencimiento >= CURDATE()
ORDER BY dias_restantes ASC;

-- =====================================================
-- VISTA vista_clientes_frecuentes
-- =====================================================
DROP VIEW IF EXISTS vista_clientes_frecuentes;
CREATE VIEW vista_clientes_frecuentes AS
SELECT c.ci,
       CONCAT(c.nombre, ' ', c.apellido_paterno, ' ', COALESCE(c.apellido_materno, '')) AS nombre_completo,
       COUNT(p.id_pedido) AS total_compras,
       COALESCE(SUM(p.total), 0) AS monto_total_gastado,
       IF(COUNT(p.id_pedido) = 0, 0, COALESCE(SUM(p.total), 0) / COUNT(p.id_pedido)) AS ticket_promedio
FROM cliente c
JOIN pedido p ON p.id_cliente = c.id_cliente
GROUP BY c.id_cliente, c.ci, c.nombre, c.apellido_paterno, c.apellido_materno
ORDER BY total_compras DESC;

-- =====================================================
-- VISTA vista_valorizacion_inventario
-- =====================================================
DROP VIEW IF EXISTS vista_valorizacion_inventario;
CREATE VIEW vista_valorizacion_inventario AS
SELECT s.nombre AS sucursal,
       COUNT(DISTINCT i.id_medicamento) AS total_productos,
       COALESCE(SUM(i.stock_actual), 0) AS total_unidades,
       COALESCE(SUM(i.stock_actual * COALESCE(m.precio_compra, 0)), 0) AS valor_costo,
       COALESCE(SUM(i.stock_actual * COALESCE(m.precio_actual, 0)), 0) AS valor_venta,
       COALESCE(SUM(i.stock_actual * COALESCE(m.precio_actual, 0)), 0)
         - COALESCE(SUM(i.stock_actual * COALESCE(m.precio_compra, 0)), 0) AS ganancia_potencial
FROM inventario i
JOIN sucursal s ON i.id_sucursal = s.id_sucursal
JOIN medicamento m ON i.id_medicamento = m.id_medicamento
GROUP BY s.id_sucursal, s.nombre;

-- =====================================================
-- VISTA vw_productos_mas_vendidos (corregida)
-- =====================================================
DROP VIEW IF EXISTS vw_productos_mas_vendidos;
CREATE VIEW vw_productos_mas_vendidos AS
SELECT m.nombre_comercial,
       m.nombre_generico,
       SUM(dv.cantidad) AS unidades_vendidas,
       COUNT(DISTINCT dv.id_venta) AS numero_ventas,
       COALESCE(SUM(dv.subtotal), 0) AS ingreso_total
FROM detalle_venta dv
JOIN medicamento m ON dv.id_medicamento = m.id_medicamento
GROUP BY m.id_medicamento, m.nombre_comercial, m.nombre_generico
ORDER BY unidades_vendidas DESC
LIMIT 10;
