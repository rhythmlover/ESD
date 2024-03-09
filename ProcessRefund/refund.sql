-- phpMyAdmin SQL Dump
-- version 4.7.4
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Jun 12, 2020 at 02:17 AM
-- Server version: 5.7.19
-- PHP Version: 7.1.9

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `refund`
--
CREATE DATABASE IF NOT EXISTS `refund` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `refund`;

-- --------------------------------------------------------

--
-- Table structure for table `refund`
--

DROP TABLE IF EXISTS `refund`;
CREATE TABLE IF NOT EXISTS `refund` (
  `refund_id` int(11) NOT NULL AUTO_INCREMENT,
  `customer_id` varchar(32) NOT NULL,
  `status` varchar(10) NOT NULL DEFAULT 'NEW',
  `created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `modified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`refund_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `refund`
--

INSERT INTO `refund` (`refund_id`, `customer_id`, `status`, `created`, `modified`) VALUES
(1, 'Apple TAN', 'NEW', '2020-06-12 02:14:55', '2020-06-12 02:14:55');

-- --------------------------------------------------------

--
-- Table structure for table `refund_item`
--

DROP TABLE IF EXISTS `refund_item`;
CREATE TABLE IF NOT EXISTS `refund_item` (
  `item_id` int(11) NOT NULL AUTO_INCREMENT,
  `refund_id` int(11) NOT NULL,
  `book_id` char(13) NOT NULL,
  `quantity` int(11) NOT NULL,
  PRIMARY KEY (`item_id`),
  KEY `FK_refund_id` (`refund_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `refund_item`
--

INSERT INTO `refund_item` (`item_id`, `refund_id`, `book_id`, `quantity`) VALUES
(1, 1, '9781434474234', 1),
(2, 1, '9781449474212', 1);

--
-- Constraints for dumped tables
--

--
-- Constraints for table `refund_item`
--
ALTER TABLE `refund_item`
  ADD CONSTRAINT `FK_refund_id` FOREIGN KEY (`refund_id`) REFERENCES `refund` (`refund_id`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
