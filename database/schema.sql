-- MySQL dump 10.13  Distrib 9.2.0, for Win64 (x86_64)
--
-- Host: localhost    Database: bbdd_produccion
-- ------------------------------------------------------
-- Server version	9.2.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `calidad_inspeccion_detalle`
--

DROP TABLE IF EXISTS `calidad_inspeccion_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `calidad_inspeccion_detalle` (
  `ID_Detalle` int NOT NULL AUTO_INCREMENT,
  `ID_Inspeccion` int NOT NULL,
  `ID_Variable_Calidad` int NOT NULL,
  `Valor_Medido` varchar(255) NOT NULL,
  `Resultado_Variable` enum('DENTRO_CONTROL','FUERA_CONTROL_SUP','FUERA_CONTROL_INF','FUERA_ESPECIFICACION_SUP','FUERA_ESPECIFICACION_INF','CONFORME','NO_CONFORME') DEFAULT NULL,
  PRIMARY KEY (`ID_Detalle`),
  UNIQUE KEY `uq_inspeccion_variable` (`ID_Inspeccion`,`ID_Variable_Calidad`),
  KEY `fk_cal_det_var` (`ID_Variable_Calidad`),
  CONSTRAINT `fk_cal_det_head` FOREIGN KEY (`ID_Inspeccion`) REFERENCES `calidad_inspeccion_header` (`ID_Inspeccion`) ON DELETE CASCADE,
  CONSTRAINT `fk_cal_det_var` FOREIGN KEY (`ID_Variable_Calidad`) REFERENCES `calidad_maestro_variables` (`ID_Variable`)
) ENGINE=InnoDB AUTO_INCREMENT=102 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `calidad_inspeccion_header`
--

DROP TABLE IF EXISTS `calidad_inspeccion_header`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `calidad_inspeccion_header` (
  `ID_Inspeccion` int NOT NULL AUTO_INCREMENT,
  `ID_Registro_KPI` int NOT NULL,
  `Lote` varchar(50) NOT NULL,
  `ID_Usuario` varchar(50) NOT NULL,
  `Fecha_Hora_Inspeccion` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Resultado_General` enum('APROBADO','APROBADO_CON_DESVIACION','RECHAZADO','PENDIENTE') NOT NULL DEFAULT 'PENDIENTE',
  PRIMARY KEY (`ID_Inspeccion`),
  KEY `fk_cal_head_kpi` (`ID_Registro_KPI`),
  KEY `fk_cal_head_usr` (`ID_Usuario`),
  CONSTRAINT `fk_cal_head_kpi` FOREIGN KEY (`ID_Registro_KPI`) REFERENCES `registro_kpi` (`ID_Registro`),
  CONSTRAINT `fk_cal_head_usr` FOREIGN KEY (`ID_Usuario`) REFERENCES `usuario` (`ID_Usuario`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `calidad_maestro_variables`
--

DROP TABLE IF EXISTS `calidad_maestro_variables`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `calidad_maestro_variables` (
  `ID_Variable` int NOT NULL AUTO_INCREMENT,
  `ID_Proceso` varchar(10) NOT NULL,
  `Referencia` varchar(50) DEFAULT NULL,
  `Nombre_Variable` varchar(100) NOT NULL,
  `Tipo_Dato` enum('NUMERICO','TEXTO','BOOLEANO','LISTA') NOT NULL,
  `Unidad_Medida` varchar(20) DEFAULT NULL,
  `Valor_Esperado` decimal(10,4) DEFAULT NULL,
  `Limite_Control_Inferior` decimal(10,4) DEFAULT NULL,
  `Limite_Control_Superior` decimal(10,4) DEFAULT NULL,
  `Limite_Especificacion_Inferior` decimal(10,4) DEFAULT NULL,
  `Limite_Especificacion_Superior` decimal(10,4) DEFAULT NULL,
  `Opciones_Lista` json DEFAULT NULL,
  `Activo` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`ID_Variable`),
  UNIQUE KEY `uq_proceso_ref_nombre` (`ID_Proceso`,`Referencia`,`Nombre_Variable`),
  KEY `fk_cal_var_referencia` (`Referencia`),
  CONSTRAINT `fk_cal_var_proceso` FOREIGN KEY (`ID_Proceso`) REFERENCES `proceso` (`ID_Proceso`),
  CONSTRAINT `fk_cal_var_referencia` FOREIGN KEY (`Referencia`) REFERENCES `producto` (`Referencia`)
) ENGINE=InnoDB AUTO_INCREMENT=248 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `descripcion_paro`
--

DROP TABLE IF EXISTS `descripcion_paro`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `descripcion_paro` (
  `ID_Paro` varchar(10) NOT NULL,
  `ID_Proceso` varchar(10) NOT NULL,
  `Descripcion_Paro` varchar(50) NOT NULL,
  `ID_TP` varchar(10) NOT NULL,
  PRIMARY KEY (`ID_Paro`),
  UNIQUE KEY `ID_Paro` (`ID_Paro`),
  KEY `ID_Proceso` (`ID_Proceso`),
  KEY `ID_TP` (`ID_TP`),
  CONSTRAINT `descripcion_paro_ibfk_1` FOREIGN KEY (`ID_Proceso`) REFERENCES `proceso` (`ID_Proceso`),
  CONSTRAINT `descripcion_paro_ibfk_2` FOREIGN KEY (`ID_TP`) REFERENCES `tipo_paro` (`ID_TP`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `maquina`
--

DROP TABLE IF EXISTS `maquina`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `maquina` (
  `ID_Proceso` varchar(10) NOT NULL,
  `ID_Maquina` varchar(10) NOT NULL,
  `Maquina` varchar(50) NOT NULL,
  PRIMARY KEY (`ID_Maquina`),
  KEY `ID_Proceso` (`ID_Proceso`),
  CONSTRAINT `maquina_ibfk_1` FOREIGN KEY (`ID_Proceso`) REFERENCES `proceso` (`ID_Proceso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `paros_maquina`
--

DROP TABLE IF EXISTS `paros_maquina`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `paros_maquina` (
  `Fecha` date NOT NULL,
  `Referencia` varchar(50) NOT NULL,
  `ID_Usuario` varchar(10) NOT NULL,
  `ID_Maquina` varchar(10) NOT NULL,
  `ID_Proceso` varchar(10) NOT NULL,
  `Turno` varchar(10) NOT NULL,
  `ID_TP` varchar(10) NOT NULL,
  `ID_Registro_KPI` int NOT NULL,
  `ID_Paro` varchar(10) NOT NULL,
  `Tiempo_Paro` decimal(10,1) NOT NULL,
  KEY `ID_Usuario` (`ID_Usuario`),
  KEY `ID_Maquina` (`ID_Maquina`),
  KEY `ID_Proceso` (`ID_Proceso`),
  KEY `ID_TP` (`ID_TP`),
  KEY `ID_Paro` (`ID_Paro`),
  KEY `fk_paros_registro_kpi` (`ID_Registro_KPI`),
  CONSTRAINT `fk_paros_registro_kpi` FOREIGN KEY (`ID_Registro_KPI`) REFERENCES `registro_kpi` (`ID_Registro`),
  CONSTRAINT `paros_maquina_ibfk_1` FOREIGN KEY (`ID_Usuario`) REFERENCES `usuario` (`ID_Usuario`),
  CONSTRAINT `paros_maquina_ibfk_2` FOREIGN KEY (`ID_Maquina`) REFERENCES `maquina` (`ID_Maquina`),
  CONSTRAINT `paros_maquina_ibfk_3` FOREIGN KEY (`ID_Proceso`) REFERENCES `proceso` (`ID_Proceso`),
  CONSTRAINT `paros_maquina_ibfk_4` FOREIGN KEY (`ID_TP`) REFERENCES `tipo_paro` (`ID_TP`),
  CONSTRAINT `paros_maquina_ibfk_5` FOREIGN KEY (`ID_Paro`) REFERENCES `descripcion_paro` (`ID_Paro`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `proceso`
--

DROP TABLE IF EXISTS `proceso`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `proceso` (
  `ID_Proceso` varchar(10) NOT NULL,
  `Proceso` varchar(50) NOT NULL,
  PRIMARY KEY (`ID_Proceso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `producto`
--

DROP TABLE IF EXISTS `producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `producto` (
  `Referencia` varchar(50) NOT NULL,
  `Largo` decimal(10,2) NOT NULL,
  `Ancho` decimal(5,2) NOT NULL,
  `Calibre` decimal(4,2) NOT NULL,
  `Diseño_Perforado` varchar(50) NOT NULL,
  `Linea_Producto` varchar(50) NOT NULL,
  `Peso_Paquete` decimal(6,3) NOT NULL,
  `Tratamiento` varchar(100) NOT NULL,
  `Tipo_Sellado` varchar(50) NOT NULL,
  `Tipo_Producto` varchar(50) NOT NULL,
  PRIMARY KEY (`Referencia`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `registro_kpi`
--

DROP TABLE IF EXISTS `registro_kpi`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `registro_kpi` (
  `ID_Registro` int NOT NULL AUTO_INCREMENT,
  `Fecha` date NOT NULL,
  `Referencia` varchar(50) NOT NULL,
  `ID_Usuario` varchar(10) NOT NULL,
  `ID_Maquina` varchar(10) NOT NULL,
  `ID_Proceso` varchar(10) NOT NULL,
  `Turno` varchar(10) NOT NULL,
  `Hora_Inicio` time NOT NULL,
  `Hora_Finalización` time DEFAULT NULL,
  `Cantidad_Conforme` decimal(10,1) NOT NULL,
  `Cantidad_Unidades` int NOT NULL DEFAULT '0',
  `Numero_Capas` int NOT NULL,
  `Retal_Proceso` decimal(10,1) NOT NULL,
  `Retal_Merma` decimal(10,1) NOT NULL,
  `Paros_Alistamiento` decimal(10,1) DEFAULT NULL,
  `Paros_Programados` decimal(10,1) DEFAULT NULL,
  `Paros_Calidad` decimal(10,1) DEFAULT NULL,
  `Paros_Averias` decimal(10,1) DEFAULT NULL,
  `Paros_Organizacion` decimal(10,1) DEFAULT NULL,
  `Tiempo_Bruto_Turno_Registrado_Min` decimal(10,2) DEFAULT NULL,
  `Tiempo_Disponible_Para_Producir_Min` decimal(10,2) DEFAULT NULL,
  `Tiempo_Paros_NoPlaneados_Min` decimal(10,2) DEFAULT NULL,
  `Tiempo_Operativo_Real_Min` decimal(10,2) DEFAULT NULL,
  `Disponibilidad_OEE` decimal(10,4) DEFAULT NULL,
  `Calidad_OEE` decimal(10,4) DEFAULT NULL,
  `Rendimiento_OEE` decimal(10,4) DEFAULT NULL,
  `OEE_General` decimal(10,4) DEFAULT NULL,
  PRIMARY KEY (`ID_Registro`),
  KEY `ID_Usuario` (`ID_Usuario`),
  KEY `ID_Maquina` (`ID_Maquina`),
  KEY `ID_Proceso` (`ID_Proceso`),
  CONSTRAINT `registro_kpi_ibfk_1` FOREIGN KEY (`ID_Usuario`) REFERENCES `usuario` (`ID_Usuario`),
  CONSTRAINT `registro_kpi_ibfk_2` FOREIGN KEY (`ID_Maquina`) REFERENCES `maquina` (`ID_Maquina`),
  CONSTRAINT `registro_kpi_ibfk_3` FOREIGN KEY (`ID_Proceso`) REFERENCES `proceso` (`ID_Proceso`)
) ENGINE=InnoDB AUTO_INCREMENT=113 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tipo_paro`
--

DROP TABLE IF EXISTS `tipo_paro`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tipo_paro` (
  `ID_TP` varchar(10) NOT NULL,
  `Tipo_De_Paro` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`ID_TP`),
  UNIQUE KEY `ID_TP` (`ID_TP`),
  UNIQUE KEY `Tipo_De_Paro` (`Tipo_De_Paro`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `turno`
--

DROP TABLE IF EXISTS `turno`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `turno` (
  `ID_Turno` varchar(10) NOT NULL,
  `Nombre_Turno` varchar(50) NOT NULL,
  `Hora_Inicio` time NOT NULL,
  `Hora_Fin` time NOT NULL,
  PRIMARY KEY (`ID_Turno`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `usuario`
--

DROP TABLE IF EXISTS `usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuario` (
  `ID_Usuario` varchar(50) NOT NULL,
  `Nombre` varchar(50) NOT NULL,
  `Cedula` int NOT NULL,
  `Telefono` varchar(20) NOT NULL,
  `Correo` varchar(50) DEFAULT NULL,
  `Contraseña` int NOT NULL,
  `Rol` varchar(50) NOT NULL,
  `Estado` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`ID_Usuario`),
  UNIQUE KEY `ID_Usuario` (`ID_Usuario`),
  UNIQUE KEY `Cedula` (`Cedula`),
  UNIQUE KEY `Telefono` (`Telefono`),
  UNIQUE KEY `Contraseña` (`Contraseña`),
  UNIQUE KEY `Correo` (`Correo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping routines for database 'bbdd_produccion'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-12-05 19:02:21
