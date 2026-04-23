-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Apr 23, 2026 at 09:27 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `resume_system`
--

-- --------------------------------------------------------

--
-- Table structure for table `all_submissions`
--

CREATE TABLE `all_submissions` (
  `id` int(11) NOT NULL,
  `full_name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `resume_text` text DEFAULT NULL,
  `tf_idf_score` float DEFAULT NULL,
  `transformer_score` float DEFAULT NULL,
  `final_score` float DEFAULT NULL,
  `upload_time` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `all_submissions`
--

INSERT INTO `all_submissions` (`id`, `full_name`, `email`, `resume_text`, `tf_idf_score`, `transformer_score`, `final_score`, `upload_time`) VALUES
(1, 'alem', 'alem@gmail.com', 'teacher', 0, 0.235936, 0.165155, '2026-04-23 22:22:10'),
(4, 'asresach', '11asresach21@gmail.com', 'full stack developer', 1, 1, 1, '2026-04-23 22:22:10');

-- --------------------------------------------------------

--
-- Table structure for table `invitation_codes`
--

CREATE TABLE `invitation_codes` (
  `email` varchar(255) NOT NULL,
  `code` varchar(10) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `invitation_codes`
--

INSERT INTO `invitation_codes` (`email`, `code`, `created_at`) VALUES
('11asresach21@gmail.com', 'FBZ6OY', '2026-04-23 22:25:28'),
('bekelebelayneh76@gmail.com', 'TX6DRD', '2026-04-23 17:37:08'),
('belayneh76@gmail.com', 'DE27DP', '2026-04-23 17:36:42');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `full_name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('candidate','recruiter') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `full_name`, `email`, `phone`, `password`, `role`) VALUES
(1, 'Belayneh Bekele', 'bekelebelayneh76@gmail.com', '0955072048', '7e922c566c6d1cf6bc96f187260a8e4cf50ba40d1a3977b073e5fa490a49b543', 'recruiter'),
(2, 'abebe kebede', 'abebe@gmail.com', '0955667767', 'ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f', 'candidate'),
(4, 'abebe kebede', 'abebekebede@gmail.com', '0955667767', 'ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f', 'candidate'),
(6, 'alem', 'alem@gmail.com', '0923344556', 'ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f', 'candidate'),
(8, 'alemu mekete', 'alemukass@gmail.com', '0955072042', 'ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f', 'candidate'),
(9, 'asresach', '11asresach21@gmail.com', '0955072041', 'ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f', 'candidate');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `all_submissions`
--
ALTER TABLE `all_submissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `invitation_codes`
--
ALTER TABLE `invitation_codes`
  ADD PRIMARY KEY (`email`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `all_submissions`
--
ALTER TABLE `all_submissions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
