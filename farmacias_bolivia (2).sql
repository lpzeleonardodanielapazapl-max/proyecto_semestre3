-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 22-05-2026 a las 19:33:45
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `farmacias_bolivia`
--

DELIMITER $$
--
-- Procedimientos
--
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_registrar_venta` (IN `p_sucursal` INT, IN `p_cliente` INT, IN `p_total` DECIMAL(10,2))   BEGIN
    INSERT INTO venta(fecha, id_sucursal, id_cliente, total)
    VALUES (NOW(), p_sucursal, p_cliente, p_total);
    
    SELECT LAST_INSERT_ID() AS id_venta;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_transferir_stock` (IN `p_origen` INT, IN `p_destino` INT, IN `p_medicamento` INT, IN `p_cantidad` INT)   BEGIN
    DECLARE stock_disponible INT;
    
    SELECT stock_actual INTO stock_disponible
    FROM inventario
    WHERE id_sucursal = p_origen AND id_medicamento = p_medicamento;
    
    IF stock_disponible >= p_cantidad THEN
        UPDATE inventario 
        SET stock_actual = stock_actual - p_cantidad
        WHERE id_sucursal = p_origen AND id_medicamento = p_medicamento;
        
        INSERT INTO inventario (id_sucursal, id_medicamento, stock_actual, stock_minimo)
        VALUES (p_destino, p_medicamento, p_cantidad, 5)
        ON DUPLICATE KEY UPDATE stock_actual = stock_actual + p_cantidad;
    END IF;
END$$

DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `carrito`
--

CREATE TABLE `carrito` (
  `id_carrito` int(11) NOT NULL,
  `id_cliente` int(11) NOT NULL,
  `id_medicamento` int(11) NOT NULL,
  `cantidad` int(11) NOT NULL,
  `fecha_agregado` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cliente`
--

CREATE TABLE `cliente` (
  `id_cliente` int(11) NOT NULL,
  `ci` varchar(15) NOT NULL,
  `nombres` varchar(100) NOT NULL,
  `apellidos` varchar(100) NOT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `direccion` varchar(200) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `contrasena` varchar(255) DEFAULT NULL,
  `fecha_registro` date NOT NULL,
  `nombre` varchar(100) DEFAULT NULL,
  `apellido_paterno` varchar(100) DEFAULT NULL,
  `apellido_materno` varchar(100) DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `cliente`
--

INSERT INTO `cliente` (`id_cliente`, `ci`, `nombres`, `apellidos`, `telefono`, `direccion`, `email`, `contrasena`, `fecha_registro`, `nombre`, `apellido_paterno`, `apellido_materno`, `activo`) VALUES
(1, '1234567', 'Luis', 'Perez', '76543210', 'La Paz', 'luis@test.com', '1234', '2026-01-01', 'Luis', 'Perez', '', 1),
(2, '2345678', 'Ana', 'Lopez', '76543211', 'El Alto', 'ana@test.com', '1234', '2026-01-02', 'Ana', 'Lopez', '', 1),
(3, '3456789', 'Carlos', 'Quispe', '76543212', 'La Paz', 'carlos@test.com', '1234', '2026-01-03', 'Carlos', 'Quispe', '', 1),
(4, '4567890', 'Maria', 'Mamani', '76543213', 'La Paz', 'maria@test.com', '1234', '2026-01-04', 'Maria', 'Mamani', '', 1),
(5, '5678901', 'Pedro', 'Choque', '76543214', 'El Alto', 'pedro@test.com', '1234', '2026-01-05', 'Pedro', 'Choque', '', 1),
(6, '12483475', 'Leonardo', 'Apaza', '78780244', 'EL ALTO', 'leo@test.com', '1234', '2026-04-12', 'Leonardo', 'Apaza', '', 1),
(7, '4823583', 'Denis', 'Apaza', '76760199', 'El Alto', 'denis@test.com', '1234', '2026-04-12', 'Denis', 'Apaza', '', 1),
(8, '10923826', 'Pablo Miguel', 'Hurtado Castillo', '72522600', 'La Paz', 'pablo@test.com', '1234', '2026-04-13', 'Pablo Miguel', 'Hurtado Castillo', '', 1),
(9, '14787474', '', '', '77264625', 'ovejuyo, ', 'algoritmoscotidianos@gmail.com', NULL, '0000-00-00', 'camila', 'Vargas', 'Mamani', 1),
(10, '123456', '', '', '2678587', 'nsebthsert', 'hola@gmail.com', NULL, '0000-00-00', ' gerg e', ' grr ', ' ergerbger', 1),
(11, '7073999', '', '', '78779202', 'casfasa', 'sanchez@gmail.com', NULL, '0000-00-00', 'Alvaro', 'Sanchez', 'Magne', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `compra`
--

CREATE TABLE `compra` (
  `id_compra` int(11) NOT NULL,
  `id_proveedor` int(11) NOT NULL,
  `id_sucursal` int(11) NOT NULL,
  `fecha` date NOT NULL,
  `factura_numero` varchar(50) DEFAULT NULL,
  `total` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `detalle_compra`
--

CREATE TABLE `detalle_compra` (
  `id_detalle_compra` int(11) NOT NULL,
  `id_compra` int(11) NOT NULL,
  `id_medicamento` int(11) NOT NULL,
  `cantidad` int(11) NOT NULL,
  `precio_compra` decimal(10,2) NOT NULL,
  `fecha_vencimiento` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Disparadores `detalle_compra`
--
DELIMITER $$
CREATE TRIGGER `trg_aumentar_stock` AFTER INSERT ON `detalle_compra` FOR EACH ROW BEGIN
    DECLARE v_sucursal INT;
    
    SELECT id_sucursal INTO v_sucursal
    FROM compra WHERE id_compra = NEW.id_compra;
    
    UPDATE inventario
    SET stock_actual = stock_actual + NEW.cantidad
    WHERE id_sucursal = v_sucursal 
    AND id_medicamento = NEW.id_medicamento;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `detalle_pedido`
--

CREATE TABLE `detalle_pedido` (
  `id_detalle_pedido` int(11) NOT NULL,
  `id_pedido` int(11) NOT NULL,
  `id_medicamento` int(11) NOT NULL,
  `cantidad` int(11) NOT NULL,
  `precio_unitario` decimal(10,2) NOT NULL,
  `subtotal` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `detalle_pedido`
--

INSERT INTO `detalle_pedido` (`id_detalle_pedido`, `id_pedido`, `id_medicamento`, `cantidad`, `precio_unitario`, `subtotal`) VALUES
(1, 1, 1, 2, 2.50, 5.00),
(2, 1, 2, 3, 3.00, 9.00),
(3, 1, 3, 1, 8.00, 8.00),
(4, 2, 11, 1, 80.00, 80.00),
(5, 3, 13, 3, 2.00, 6.00),
(6, 3, 4, 2, 1.50, 3.00),
(7, 4, 1, 10, 2.50, 25.00),
(8, 4, 13, 5, 2.00, 10.00),
(9, 5, 13, 2, 38.00, 76.00),
(10, 5, 10, 2, 14.90, 29.80),
(11, 6, 2, 10, 3.00, 30.00),
(12, 6, 3, 3, 8.00, 24.00);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `detalle_venta`
--

CREATE TABLE `detalle_venta` (
  `id_detalle` int(11) NOT NULL,
  `id_venta` int(11) NOT NULL,
  `id_medicamento` int(11) NOT NULL,
  `cantidad` int(11) NOT NULL CHECK (`cantidad` > 0),
  `precio_unitario` decimal(10,2) NOT NULL,
  `subtotal` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `detalle_venta`
--

INSERT INTO `detalle_venta` (`id_detalle`, `id_venta`, `id_medicamento`, `cantidad`, `precio_unitario`, `subtotal`) VALUES
(1, 1, 1, 2, 2.50, 5.00),
(2, 1, 2, 3, 3.00, 9.00),
(3, 2, 3, 1, 8.00, 8.00),
(4, 3, 1, 5, 4.00, 20.00),
(5, 3, 13, 5, 2.00, 10.00),
(6, 3, 4, 5, 1.50, 7.50),
(7, 4, 1, 6, 2.50, 15.00);

--
-- Disparadores `detalle_venta`
--
DELIMITER $$
CREATE TRIGGER `trg_reducir_stock` AFTER INSERT ON `detalle_venta` FOR EACH ROW BEGIN
    DECLARE v_sucursal INT;
    
    SELECT id_sucursal INTO v_sucursal
    FROM venta WHERE id_venta = NEW.id_venta;
    
    UPDATE inventario
    SET stock_actual = stock_actual - NEW.cantidad
    WHERE id_sucursal = v_sucursal 
    AND id_medicamento = NEW.id_medicamento;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `favoritos`
--

CREATE TABLE `favoritos` (
  `id_favorito` int(11) NOT NULL,
  `id_cliente` int(11) NOT NULL,
  `id_medicamento` int(11) NOT NULL,
  `fecha_agregado` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `inventario`
--

CREATE TABLE `inventario` (
  `id_inventario` int(11) NOT NULL,
  `id_sucursal` int(11) NOT NULL,
  `id_medicamento` int(11) NOT NULL,
  `stock_actual` int(11) NOT NULL CHECK (`stock_actual` >= 0),
  `stock_minimo` int(11) NOT NULL DEFAULT 5,
  `fecha_actualizacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `ubicacion_almacen` varchar(200) DEFAULT NULL,
  `cantidad` int(11) GENERATED ALWAYS AS (`stock_actual`) STORED
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `inventario`
--

INSERT INTO `inventario` (`id_inventario`, `id_sucursal`, `id_medicamento`, `stock_actual`, `stock_minimo`, `fecha_actualizacion`, `ubicacion_almacen`) VALUES
(1, 1, 1, 50, 10, '2026-05-18 05:58:47', NULL),
(2, 1, 2, 40, 10, '2026-05-18 05:58:47', NULL),
(3, 1, 3, 30, 5, '2026-05-18 05:58:47', NULL),
(4, 2, 1, 60, 10, '2026-05-18 05:58:47', NULL),
(5, 2, 2, 20, 10, '2026-05-18 05:58:47', NULL),
(6, 2, 3, 10, 5, '2026-05-18 05:58:47', NULL),
(7, 3, 4, 25, 5, '2026-05-18 05:58:47', NULL),
(8, 3, 5, 15, 5, '2026-05-18 05:58:47', NULL),
(9, 3, 6, 10, 5, '2026-05-18 05:58:47', NULL);

--
-- Disparadores `inventario`
--
DELIMITER $$
CREATE TRIGGER `trg_log_movimiento` AFTER UPDATE ON `inventario` FOR EACH ROW BEGIN
    INSERT INTO movimiento_inventario(
        id_sucursal, id_medicamento, tipo, cantidad, motivo, id_usuario
    )
    VALUES (
        NEW.id_sucursal, NEW.id_medicamento, 'AJUSTE',
        NEW.stock_actual - OLD.stock_actual, 'Actualización automática', 1
    );
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `lote`
--

CREATE TABLE `lote` (
  `id_lote` int(11) NOT NULL,
  `id_medicamento` int(11) NOT NULL,
  `numero_lote` varchar(50) NOT NULL,
  `fecha_fabricacion` date NOT NULL,
  `fecha_vencimiento` date NOT NULL,
  `cantidad_inicial` int(11) NOT NULL,
  `cantidad_restante` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `medicamento`
--

CREATE TABLE `medicamento` (
  `id_medicamento` int(11) NOT NULL,
  `codigo_barras` varchar(50) NOT NULL,
  `nombre_comercial` varchar(100) NOT NULL,
  `nombre_generico` varchar(100) DEFAULT NULL,
  `presentacion` varchar(50) DEFAULT NULL,
  `concentracion` varchar(50) DEFAULT NULL,
  `requiere_receta` tinyint(1) NOT NULL DEFAULT 0,
  `precio_actual` decimal(10,2) NOT NULL CHECK (`precio_actual` >= 0),
  `principio_activo` varchar(100) DEFAULT NULL,
  `forma_farmaceutica` varchar(100) DEFAULT NULL,
  `precio_compra` decimal(10,2) NOT NULL DEFAULT 0.00,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  `requiere_refrigeracion` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `medicamento`
--

INSERT INTO `medicamento` (`id_medicamento`, `codigo_barras`, `nombre_comercial`, `nombre_generico`, `presentacion`, `concentracion`, `requiere_receta`, `precio_actual`, `principio_activo`, `forma_farmaceutica`, `precio_compra`, `activo`, `requiere_refrigeracion`) VALUES
(1, '1001', 'Paracetamol', 'Acetaminofen', 'Tableta', '500mg', 0, 2.50, NULL, NULL, 0.00, 1, 0),
(2, '1002', 'Ibuprofeno', 'Ibuprofeno', 'Tableta', '400mg', 0, 3.00, NULL, NULL, 0.00, 1, 0),
(3, '1003', 'Amoxicilina', 'Amoxicilina', 'Capsula', '500mg', 1, 8.00, NULL, NULL, 0.00, 1, 0),
(4, '1004', 'Aspirina', 'Acido acetilsalicilico', 'Tableta', '100mg', 0, 1.50, NULL, NULL, 0.00, 1, 0),
(5, '1005', 'Jarabe Tos', 'Dextrometorfano', 'Jarabe', '120ml', 0, 10.00, NULL, NULL, 0.00, 1, 0),
(6, '1006', 'Omeprazol', 'Omeprazol', 'Capsula', '20mg', 1, 5.50, NULL, NULL, 0.00, 1, 0),
(7, '1007', 'Diclofenaco', 'Diclofenaco', 'Tableta', '50mg', 1, 4.00, NULL, NULL, 0.00, 1, 0),
(8, '1008', 'Salbutamol', 'Salbutamol', 'Inhalador', '100mcg', 1, 25.00, NULL, NULL, 0.00, 1, 0),
(9, '1009', 'Loratadina', 'Loratadina', 'Tableta', '10mg', 0, 3.50, NULL, NULL, 0.00, 1, 0),
(10, '1010', 'Metformina', 'Metformina', 'Tableta', '850mg', 1, 6.00, NULL, NULL, 0.00, 1, 0),
(11, '1011', 'Insulina', 'Insulina', 'Inyectable', '10ml', 1, 80.00, NULL, NULL, 0.00, 1, 0),
(12, '1012', 'Azitromicina', 'Azitromicina', 'Tableta', '500mg', 1, 15.00, NULL, NULL, 0.00, 1, 0),
(13, '1013', 'Vitamina C', 'Acido ascorbico', 'Tableta', '1g', 0, 2.00, NULL, NULL, 0.00, 1, 0),
(14, '1014', 'Calcio', 'Carbonato de calcio', 'Tableta', '600mg', 0, 3.00, NULL, NULL, 0.00, 1, 0),
(15, '1015', 'Enalapril', 'Enalapril', 'Tableta', '10mg', 1, 4.50, NULL, NULL, 0.00, 1, 0);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `movimiento_inventario`
--

CREATE TABLE `movimiento_inventario` (
  `id_movimiento` int(11) NOT NULL,
  `id_sucursal` int(11) NOT NULL,
  `id_medicamento` int(11) NOT NULL,
  `id_lote` int(11) DEFAULT NULL,
  `tipo` enum('ENTRADA','SALIDA','AJUSTE') NOT NULL,
  `cantidad` int(11) NOT NULL,
  `motivo` varchar(200) DEFAULT NULL,
  `fecha` timestamp NOT NULL DEFAULT current_timestamp(),
  `id_usuario` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pedido`
--

CREATE TABLE `pedido` (
  `id_pedido` int(11) NOT NULL,
  `id_cliente` int(11) NOT NULL,
  `numero_pedido` varchar(50) NOT NULL,
  `subtotal` decimal(10,2) NOT NULL,
  `iva` decimal(10,2) NOT NULL,
  `total` decimal(10,2) NOT NULL,
  `metodo_pago` enum('EFECTIVO','TARJETA','TRANSFERENCIA','QR') DEFAULT 'EFECTIVO',
  `direccion_entrega` varchar(200) DEFAULT NULL,
  `telefono_contacto` varchar(20) DEFAULT NULL,
  `estado` enum('PENDIENTE','CONFIRMADO','PREPARANDO','ENVIADO','ENTREGADO','CANCELADO') DEFAULT 'PENDIENTE',
  `fecha` datetime DEFAULT current_timestamp(),
  `receta_medica` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `pedido`
--

INSERT INTO `pedido` (`id_pedido`, `id_cliente`, `numero_pedido`, `subtotal`, `iva`, `total`, `metodo_pago`, `direccion_entrega`, `telefono_contacto`, `estado`, `fecha`, `receta_medica`) VALUES
(1, 6, 'PED-20260503231559', 150.00, 21.53, 171.53, 'QR', 'marruecos', '78780244', 'PENDIENTE', '2026-05-03 23:15:59', NULL),
(2, 6, 'PED-20260503232345', 75.00, 10.88, 85.88, 'QR', 'awefwseaf', '78780244', 'PENDIENTE', '2026-05-03 23:23:45', NULL),
(3, 6, 'PED-20260504160508', 29.50, 4.17, 33.67, 'QR', 'calle bolivar', '78780244', 'ENTREGADO', '2026-05-04 16:05:08', NULL),
(4, 6, 'PED-20260504220000', 50.00, 7.25, 57.25, 'EFECTIVO', 'Av. 6 de Marzo', '78780244', 'CONFIRMADO', '2026-05-04 22:00:00', NULL),
(5, 6, 'PED-20260505135842', 105.80, 13.75, 119.55, 'EFECTIVO', 'marruecos', '78780244', 'PENDIENTE', '2026-05-05 13:58:42', NULL),
(6, 9, 'PED-20260522005559', 54.00, 7.02, 61.02, 'QR', 'ovejuyo, la paz casa cami', '12345678', 'PENDIENTE', '2026-05-22 00:55:59', NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `proveedor`
--

CREATE TABLE `proveedor` (
  `id_proveedor` int(11) NOT NULL,
  `nit` varchar(20) NOT NULL,
  `razon_social` varchar(150) NOT NULL,
  `direccion` varchar(200) DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `contacto` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `proveedor`
--

INSERT INTO `proveedor` (`id_proveedor`, `nit`, `razon_social`, `direccion`, `telefono`, `contacto`) VALUES
(1, '123456', 'Distribuidora Salud', 'La Paz', '70011111', 'Pedro Gomez'),
(2, '789456', 'Farmabol', 'Santa Cruz', '70022222', 'Luis Rojas'),
(3, '456123', 'BioMed', 'Cochabamba', '70033333', 'Ana Perez'),
(4, '321654', 'MedImport', 'La Paz', '70044444', 'Carlos Ruiz'),
(5, '654987', 'PharmaBol', 'El Alto', '70055555', 'Sofia Mamani');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `sucursal`
--

CREATE TABLE `sucursal` (
  `id_sucursal` int(11) NOT NULL,
  `nombre` varchar(50) NOT NULL,
  `direccion` varchar(200) DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `encargado` varchar(100) DEFAULT NULL,
  `ciudad` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `sucursal`
--

INSERT INTO `sucursal` (`id_sucursal`, `nombre`, `direccion`, `telefono`, `encargado`, `ciudad`) VALUES
(1, 'Sopocachi', 'Av. 20 de Octubre', '77711111', 'Juan Perez', 'La Paz'),
(2, 'Miraflores', 'Av. Busch', '77722222', 'Maria Lopez', 'La Paz'),
(3, 'San Pedro', 'Calle Colombia', '77733333', 'Carlos Quispe', 'La Paz'),
(4, 'El Alto', 'Av. 6 de Marzo', '77744444', 'Ana Mamani', 'El Alto'),
(5, 'Villa Fátima', 'Av. Las Américas', '77755555', 'Luis Choque', 'La Paz');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuario`
--

CREATE TABLE `usuario` (
  `id_usuario` int(11) NOT NULL,
  `nombre_usuario` varchar(50) NOT NULL,
  `contrasena` varchar(255) NOT NULL,
  `rol` enum('ADMIN','FARMACEUTICO','CAJERO') NOT NULL,
  `id_sucursal` int(11) DEFAULT NULL,
  `ci` varchar(15) DEFAULT NULL,
  `nombre` varchar(100) DEFAULT NULL,
  `apellido_paterno` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `password_hash` varchar(255) DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `usuario`
--

INSERT INTO `usuario` (`id_usuario`, `nombre_usuario`, `contrasena`, `rol`, `id_sucursal`, `ci`, `nombre`, `apellido_paterno`, `email`, `password_hash`, `activo`) VALUES
(1, 'ADMIN001', 'admin123', 'ADMIN', NULL, 'ADMIN001', 'ADMIN001', '', NULL, 'admin123', 1),
(2, 'FARM001', 'admin123', 'FARMACEUTICO', 1, 'FARM001', 'FARM001', '', NULL, 'admin123', 1),
(3, 'FARM002', 'admin123', 'FARMACEUTICO', 2, 'FARM002', 'FARM002', '', NULL, 'admin123', 1),
(4, 'CAJA001', 'admin123', 'CAJERO', 1, 'CAJA001', 'CAJA001', '', NULL, 'admin123', 1),
(5, 'CAJA002', 'admin123', 'CAJERO', 2, 'CAJA002', 'CAJA002', '', NULL, 'admin123', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `venta`
--

CREATE TABLE `venta` (
  `id_venta` int(11) NOT NULL,
  `fecha` datetime NOT NULL,
  `id_sucursal` int(11) NOT NULL,
  `id_cliente` int(11) DEFAULT NULL,
  `total` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `venta`
--

INSERT INTO `venta` (`id_venta`, `fecha`, `id_sucursal`, `id_cliente`, `total`) VALUES
(1, '2026-04-12 10:21:01', 1, 1, 20.00),
(2, '2026-04-12 10:21:01', 2, 2, 15.00),
(3, '2026-04-12 14:29:18', 1, 6, 37.50),
(4, '2026-04-13 16:13:04', 1, 8, 15.00);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vista_clientes_frecuentes`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `vista_clientes_frecuentes` (
`ci` varchar(15)
,`nombre_completo` varchar(302)
,`total_compras` bigint(21)
,`monto_total_gastado` decimal(32,2)
,`ticket_promedio` decimal(36,6)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vista_pedidos_pendientes`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `vista_pedidos_pendientes` (
`id_pedido` int(11)
,`id_cliente` int(11)
,`numero_pedido` varchar(50)
,`subtotal` decimal(10,2)
,`iva` decimal(10,2)
,`total` decimal(10,2)
,`metodo_pago` enum('EFECTIVO','TARJETA','TRANSFERENCIA','QR')
,`direccion_entrega` varchar(200)
,`telefono_contacto` varchar(20)
,`estado_pedido` enum('PENDIENTE','CONFIRMADO','PREPARANDO','ENVIADO','ENTREGADO','CANCELADO')
,`fecha_pedido` datetime
,`receta_medica` varchar(255)
,`cliente` varchar(302)
,`ci` varchar(15)
,`nombre` varchar(100)
,`apellido_paterno` varchar(100)
,`apellido_materno` varchar(100)
,`email` varchar(100)
,`telefono` varchar(20)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vista_proximos_vencer`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `vista_proximos_vencer` (
`id_lote` int(11)
,`id_medicamento` int(11)
,`nombre_comercial` varchar(100)
,`codigo_lote` varchar(50)
,`fecha_vencimiento` date
,`dias_restantes` int(7)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vista_valorizacion_inventario`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `vista_valorizacion_inventario` (
`sucursal` varchar(50)
,`total_productos` bigint(21)
,`total_unidades` decimal(32,0)
,`valor_costo` decimal(42,2)
,`valor_venta` decimal(42,2)
,`ganancia_potencial` decimal(43,2)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vw_productos_mas_vendidos`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `vw_productos_mas_vendidos` (
`nombre_comercial` varchar(100)
,`nombre_generico` varchar(100)
,`unidades_vendidas` decimal(32,0)
,`numero_ventas` bigint(21)
,`ingreso_total` decimal(32,2)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vw_stock_critico`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `vw_stock_critico` (
`sucursal` varchar(50)
,`nombre_comercial` varchar(100)
,`stock_actual` int(11)
,`stock_minimo` int(11)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vw_ventas_sucursal_mes`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `vw_ventas_sucursal_mes` (
`sucursal` varchar(50)
,`anio` int(4)
,`mes` int(2)
,`total_ventas` decimal(32,2)
);

-- --------------------------------------------------------

--
-- Estructura para la vista `vista_clientes_frecuentes`
--
DROP TABLE IF EXISTS `vista_clientes_frecuentes`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vista_clientes_frecuentes`  AS SELECT `c`.`ci` AS `ci`, concat(`c`.`nombre`,' ',`c`.`apellido_paterno`,' ',coalesce(`c`.`apellido_materno`,'')) AS `nombre_completo`, count(`p`.`id_pedido`) AS `total_compras`, coalesce(sum(`p`.`total`),0) AS `monto_total_gastado`, if(count(`p`.`id_pedido`) = 0,0,coalesce(sum(`p`.`total`),0) / count(`p`.`id_pedido`)) AS `ticket_promedio` FROM (`cliente` `c` join `pedido` `p` on(`p`.`id_cliente` = `c`.`id_cliente`)) GROUP BY `c`.`id_cliente`, `c`.`ci`, `c`.`nombre`, `c`.`apellido_paterno`, `c`.`apellido_materno` ORDER BY count(`p`.`id_pedido`) DESC ;

-- --------------------------------------------------------

--
-- Estructura para la vista `vista_pedidos_pendientes`
--
DROP TABLE IF EXISTS `vista_pedidos_pendientes`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vista_pedidos_pendientes`  AS SELECT `p`.`id_pedido` AS `id_pedido`, `p`.`id_cliente` AS `id_cliente`, `p`.`numero_pedido` AS `numero_pedido`, `p`.`subtotal` AS `subtotal`, `p`.`iva` AS `iva`, `p`.`total` AS `total`, `p`.`metodo_pago` AS `metodo_pago`, `p`.`direccion_entrega` AS `direccion_entrega`, `p`.`telefono_contacto` AS `telefono_contacto`, `p`.`estado` AS `estado_pedido`, `p`.`fecha` AS `fecha_pedido`, `p`.`receta_medica` AS `receta_medica`, concat(`c`.`nombre`,' ',`c`.`apellido_paterno`,' ',coalesce(`c`.`apellido_materno`,'')) AS `cliente`, `c`.`ci` AS `ci`, `c`.`nombre` AS `nombre`, `c`.`apellido_paterno` AS `apellido_paterno`, `c`.`apellido_materno` AS `apellido_materno`, `c`.`email` AS `email`, `c`.`telefono` AS `telefono` FROM (`pedido` `p` join `cliente` `c` on(`p`.`id_cliente` = `c`.`id_cliente`)) WHERE `p`.`estado` = 'PENDIENTE' ;

-- --------------------------------------------------------

--
-- Estructura para la vista `vista_proximos_vencer`
--
DROP TABLE IF EXISTS `vista_proximos_vencer`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vista_proximos_vencer`  AS SELECT `l`.`id_lote` AS `id_lote`, `l`.`id_medicamento` AS `id_medicamento`, `m`.`nombre_comercial` AS `nombre_comercial`, `l`.`numero_lote` AS `codigo_lote`, `l`.`fecha_vencimiento` AS `fecha_vencimiento`, to_days(`l`.`fecha_vencimiento`) - to_days(curdate()) AS `dias_restantes` FROM (`lote` `l` join `medicamento` `m` on(`l`.`id_medicamento` = `m`.`id_medicamento`)) WHERE `l`.`fecha_vencimiento` >= curdate() ORDER BY to_days(`l`.`fecha_vencimiento`) - to_days(curdate()) ASC ;

-- --------------------------------------------------------

--
-- Estructura para la vista `vista_valorizacion_inventario`
--
DROP TABLE IF EXISTS `vista_valorizacion_inventario`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vista_valorizacion_inventario`  AS SELECT `s`.`nombre` AS `sucursal`, count(distinct `i`.`id_medicamento`) AS `total_productos`, coalesce(sum(`i`.`stock_actual`),0) AS `total_unidades`, coalesce(sum(`i`.`stock_actual` * coalesce(`m`.`precio_compra`,0)),0) AS `valor_costo`, coalesce(sum(`i`.`stock_actual` * coalesce(`m`.`precio_actual`,0)),0) AS `valor_venta`, coalesce(sum(`i`.`stock_actual` * coalesce(`m`.`precio_actual`,0)),0) - coalesce(sum(`i`.`stock_actual` * coalesce(`m`.`precio_compra`,0)),0) AS `ganancia_potencial` FROM ((`inventario` `i` join `sucursal` `s` on(`i`.`id_sucursal` = `s`.`id_sucursal`)) join `medicamento` `m` on(`i`.`id_medicamento` = `m`.`id_medicamento`)) GROUP BY `s`.`id_sucursal`, `s`.`nombre` ;

-- --------------------------------------------------------

--
-- Estructura para la vista `vw_productos_mas_vendidos`
--
DROP TABLE IF EXISTS `vw_productos_mas_vendidos`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_productos_mas_vendidos`  AS SELECT `m`.`nombre_comercial` AS `nombre_comercial`, `m`.`nombre_generico` AS `nombre_generico`, sum(`dv`.`cantidad`) AS `unidades_vendidas`, count(distinct `dv`.`id_venta`) AS `numero_ventas`, coalesce(sum(`dv`.`subtotal`),0) AS `ingreso_total` FROM (`detalle_venta` `dv` join `medicamento` `m` on(`dv`.`id_medicamento` = `m`.`id_medicamento`)) GROUP BY `m`.`id_medicamento`, `m`.`nombre_comercial`, `m`.`nombre_generico` ORDER BY sum(`dv`.`cantidad`) DESC LIMIT 0, 10 ;

-- --------------------------------------------------------

--
-- Estructura para la vista `vw_stock_critico`
--
DROP TABLE IF EXISTS `vw_stock_critico`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_stock_critico`  AS SELECT `s`.`nombre` AS `sucursal`, `m`.`nombre_comercial` AS `nombre_comercial`, `i`.`stock_actual` AS `stock_actual`, `i`.`stock_minimo` AS `stock_minimo` FROM ((`inventario` `i` join `sucursal` `s` on(`i`.`id_sucursal` = `s`.`id_sucursal`)) join `medicamento` `m` on(`i`.`id_medicamento` = `m`.`id_medicamento`)) WHERE `i`.`stock_actual` < `i`.`stock_minimo` ;

-- --------------------------------------------------------

--
-- Estructura para la vista `vw_ventas_sucursal_mes`
--
DROP TABLE IF EXISTS `vw_ventas_sucursal_mes`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_ventas_sucursal_mes`  AS SELECT `s`.`nombre` AS `sucursal`, year(`v`.`fecha`) AS `anio`, month(`v`.`fecha`) AS `mes`, sum(`v`.`total`) AS `total_ventas` FROM (`venta` `v` join `sucursal` `s` on(`v`.`id_sucursal` = `s`.`id_sucursal`)) GROUP BY `s`.`nombre`, year(`v`.`fecha`), month(`v`.`fecha`) ;

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `carrito`
--
ALTER TABLE `carrito`
  ADD PRIMARY KEY (`id_carrito`),
  ADD KEY `id_cliente` (`id_cliente`),
  ADD KEY `id_medicamento` (`id_medicamento`);

--
-- Indices de la tabla `cliente`
--
ALTER TABLE `cliente`
  ADD PRIMARY KEY (`id_cliente`),
  ADD UNIQUE KEY `ci` (`ci`);

--
-- Indices de la tabla `compra`
--
ALTER TABLE `compra`
  ADD PRIMARY KEY (`id_compra`),
  ADD KEY `id_proveedor` (`id_proveedor`),
  ADD KEY `id_sucursal` (`id_sucursal`);

--
-- Indices de la tabla `detalle_compra`
--
ALTER TABLE `detalle_compra`
  ADD PRIMARY KEY (`id_detalle_compra`),
  ADD KEY `id_compra` (`id_compra`),
  ADD KEY `id_medicamento` (`id_medicamento`);

--
-- Indices de la tabla `detalle_pedido`
--
ALTER TABLE `detalle_pedido`
  ADD PRIMARY KEY (`id_detalle_pedido`),
  ADD KEY `id_pedido` (`id_pedido`),
  ADD KEY `id_medicamento` (`id_medicamento`);

--
-- Indices de la tabla `detalle_venta`
--
ALTER TABLE `detalle_venta`
  ADD PRIMARY KEY (`id_detalle`),
  ADD KEY `id_venta` (`id_venta`),
  ADD KEY `id_medicamento` (`id_medicamento`);

--
-- Indices de la tabla `favoritos`
--
ALTER TABLE `favoritos`
  ADD PRIMARY KEY (`id_favorito`),
  ADD UNIQUE KEY `uk_cliente_medicamento` (`id_cliente`,`id_medicamento`),
  ADD KEY `id_medicamento` (`id_medicamento`);

--
-- Indices de la tabla `inventario`
--
ALTER TABLE `inventario`
  ADD PRIMARY KEY (`id_inventario`),
  ADD UNIQUE KEY `uk_sucursal_medicamento` (`id_sucursal`,`id_medicamento`),
  ADD KEY `id_medicamento` (`id_medicamento`);

--
-- Indices de la tabla `lote`
--
ALTER TABLE `lote`
  ADD PRIMARY KEY (`id_lote`),
  ADD KEY `id_medicamento` (`id_medicamento`);

--
-- Indices de la tabla `medicamento`
--
ALTER TABLE `medicamento`
  ADD PRIMARY KEY (`id_medicamento`),
  ADD UNIQUE KEY `codigo_barras` (`codigo_barras`);

--
-- Indices de la tabla `movimiento_inventario`
--
ALTER TABLE `movimiento_inventario`
  ADD PRIMARY KEY (`id_movimiento`),
  ADD KEY `id_sucursal` (`id_sucursal`),
  ADD KEY `id_medicamento` (`id_medicamento`),
  ADD KEY `id_lote` (`id_lote`),
  ADD KEY `id_usuario` (`id_usuario`);

--
-- Indices de la tabla `pedido`
--
ALTER TABLE `pedido`
  ADD PRIMARY KEY (`id_pedido`),
  ADD UNIQUE KEY `numero_pedido` (`numero_pedido`),
  ADD KEY `id_cliente` (`id_cliente`);

--
-- Indices de la tabla `proveedor`
--
ALTER TABLE `proveedor`
  ADD PRIMARY KEY (`id_proveedor`),
  ADD UNIQUE KEY `nit` (`nit`);

--
-- Indices de la tabla `sucursal`
--
ALTER TABLE `sucursal`
  ADD PRIMARY KEY (`id_sucursal`);

--
-- Indices de la tabla `usuario`
--
ALTER TABLE `usuario`
  ADD PRIMARY KEY (`id_usuario`),
  ADD UNIQUE KEY `nombre_usuario` (`nombre_usuario`),
  ADD KEY `id_sucursal` (`id_sucursal`);

--
-- Indices de la tabla `venta`
--
ALTER TABLE `venta`
  ADD PRIMARY KEY (`id_venta`),
  ADD KEY `id_sucursal` (`id_sucursal`),
  ADD KEY `id_cliente` (`id_cliente`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `carrito`
--
ALTER TABLE `carrito`
  MODIFY `id_carrito` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `cliente`
--
ALTER TABLE `cliente`
  MODIFY `id_cliente` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT de la tabla `compra`
--
ALTER TABLE `compra`
  MODIFY `id_compra` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `detalle_compra`
--
ALTER TABLE `detalle_compra`
  MODIFY `id_detalle_compra` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `detalle_pedido`
--
ALTER TABLE `detalle_pedido`
  MODIFY `id_detalle_pedido` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT de la tabla `detalle_venta`
--
ALTER TABLE `detalle_venta`
  MODIFY `id_detalle` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT de la tabla `favoritos`
--
ALTER TABLE `favoritos`
  MODIFY `id_favorito` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `inventario`
--
ALTER TABLE `inventario`
  MODIFY `id_inventario` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT de la tabla `lote`
--
ALTER TABLE `lote`
  MODIFY `id_lote` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `medicamento`
--
ALTER TABLE `medicamento`
  MODIFY `id_medicamento` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT de la tabla `movimiento_inventario`
--
ALTER TABLE `movimiento_inventario`
  MODIFY `id_movimiento` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `pedido`
--
ALTER TABLE `pedido`
  MODIFY `id_pedido` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de la tabla `proveedor`
--
ALTER TABLE `proveedor`
  MODIFY `id_proveedor` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `sucursal`
--
ALTER TABLE `sucursal`
  MODIFY `id_sucursal` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `usuario`
--
ALTER TABLE `usuario`
  MODIFY `id_usuario` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `venta`
--
ALTER TABLE `venta`
  MODIFY `id_venta` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `carrito`
--
ALTER TABLE `carrito`
  ADD CONSTRAINT `carrito_ibfk_1` FOREIGN KEY (`id_cliente`) REFERENCES `cliente` (`id_cliente`),
  ADD CONSTRAINT `carrito_ibfk_2` FOREIGN KEY (`id_medicamento`) REFERENCES `medicamento` (`id_medicamento`);

--
-- Filtros para la tabla `compra`
--
ALTER TABLE `compra`
  ADD CONSTRAINT `compra_ibfk_1` FOREIGN KEY (`id_proveedor`) REFERENCES `proveedor` (`id_proveedor`),
  ADD CONSTRAINT `compra_ibfk_2` FOREIGN KEY (`id_sucursal`) REFERENCES `sucursal` (`id_sucursal`);

--
-- Filtros para la tabla `detalle_compra`
--
ALTER TABLE `detalle_compra`
  ADD CONSTRAINT `detalle_compra_ibfk_1` FOREIGN KEY (`id_compra`) REFERENCES `compra` (`id_compra`) ON DELETE CASCADE,
  ADD CONSTRAINT `detalle_compra_ibfk_2` FOREIGN KEY (`id_medicamento`) REFERENCES `medicamento` (`id_medicamento`);

--
-- Filtros para la tabla `detalle_pedido`
--
ALTER TABLE `detalle_pedido`
  ADD CONSTRAINT `detalle_pedido_ibfk_1` FOREIGN KEY (`id_pedido`) REFERENCES `pedido` (`id_pedido`) ON DELETE CASCADE,
  ADD CONSTRAINT `detalle_pedido_ibfk_2` FOREIGN KEY (`id_medicamento`) REFERENCES `medicamento` (`id_medicamento`);

--
-- Filtros para la tabla `detalle_venta`
--
ALTER TABLE `detalle_venta`
  ADD CONSTRAINT `detalle_venta_ibfk_1` FOREIGN KEY (`id_venta`) REFERENCES `venta` (`id_venta`) ON DELETE CASCADE,
  ADD CONSTRAINT `detalle_venta_ibfk_2` FOREIGN KEY (`id_medicamento`) REFERENCES `medicamento` (`id_medicamento`);

--
-- Filtros para la tabla `favoritos`
--
ALTER TABLE `favoritos`
  ADD CONSTRAINT `favoritos_ibfk_1` FOREIGN KEY (`id_cliente`) REFERENCES `cliente` (`id_cliente`),
  ADD CONSTRAINT `favoritos_ibfk_2` FOREIGN KEY (`id_medicamento`) REFERENCES `medicamento` (`id_medicamento`);

--
-- Filtros para la tabla `inventario`
--
ALTER TABLE `inventario`
  ADD CONSTRAINT `inventario_ibfk_1` FOREIGN KEY (`id_sucursal`) REFERENCES `sucursal` (`id_sucursal`),
  ADD CONSTRAINT `inventario_ibfk_2` FOREIGN KEY (`id_medicamento`) REFERENCES `medicamento` (`id_medicamento`);

--
-- Filtros para la tabla `lote`
--
ALTER TABLE `lote`
  ADD CONSTRAINT `lote_ibfk_1` FOREIGN KEY (`id_medicamento`) REFERENCES `medicamento` (`id_medicamento`);

--
-- Filtros para la tabla `movimiento_inventario`
--
ALTER TABLE `movimiento_inventario`
  ADD CONSTRAINT `movimiento_inventario_ibfk_1` FOREIGN KEY (`id_sucursal`) REFERENCES `sucursal` (`id_sucursal`),
  ADD CONSTRAINT `movimiento_inventario_ibfk_2` FOREIGN KEY (`id_medicamento`) REFERENCES `medicamento` (`id_medicamento`),
  ADD CONSTRAINT `movimiento_inventario_ibfk_3` FOREIGN KEY (`id_lote`) REFERENCES `lote` (`id_lote`),
  ADD CONSTRAINT `movimiento_inventario_ibfk_4` FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id_usuario`);

--
-- Filtros para la tabla `pedido`
--
ALTER TABLE `pedido`
  ADD CONSTRAINT `pedido_ibfk_1` FOREIGN KEY (`id_cliente`) REFERENCES `cliente` (`id_cliente`);

--
-- Filtros para la tabla `usuario`
--
ALTER TABLE `usuario`
  ADD CONSTRAINT `usuario_ibfk_1` FOREIGN KEY (`id_sucursal`) REFERENCES `sucursal` (`id_sucursal`);

--
-- Filtros para la tabla `venta`
--
ALTER TABLE `venta`
  ADD CONSTRAINT `venta_ibfk_1` FOREIGN KEY (`id_sucursal`) REFERENCES `sucursal` (`id_sucursal`),
  ADD CONSTRAINT `venta_ibfk_2` FOREIGN KEY (`id_cliente`) REFERENCES `cliente` (`id_cliente`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
