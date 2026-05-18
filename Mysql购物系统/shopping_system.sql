/*
 Navicat Premium Dump SQL

 Source Server         : shopping_system
 Source Server Type    : MySQL
 Source Server Version : 80015 (8.0.15)
 Source Host           : localhost:3306
 Source Schema         : shopping_system

 Target Server Type    : MySQL
 Target Server Version : 80015 (8.0.15)
 File Encoding         : 65001

 Date: 18/05/2026 13:06:25
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for categories
-- ----------------------------
DROP TABLE IF EXISTS `categories`;
CREATE TABLE `categories`  (
  `category_id` int(11) NOT NULL AUTO_INCREMENT,
  `category_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `parent_id` int(11) NULL DEFAULT 0 COMMENT '0-顶级分类',
  `sort_order` int(11) NULL DEFAULT 0,
  PRIMARY KEY (`category_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of categories
-- ----------------------------
INSERT INTO `categories` VALUES (1, '电子产品', 0, 1);
INSERT INTO `categories` VALUES (2, '手机', 1, 1);
INSERT INTO `categories` VALUES (3, '电脑', 1, 2);
INSERT INTO `categories` VALUES (4, '家居用品', 0, 2);
INSERT INTO `categories` VALUES (5, '服装', 0, 3);
INSERT INTO `categories` VALUES (6, '男装', 5, 1);
INSERT INTO `categories` VALUES (7, '女装', 5, 2);
INSERT INTO `categories` VALUES (8, '食品', 0, 4);
INSERT INTO `categories` VALUES (9, '零食', 8, 1);
INSERT INTO `categories` VALUES (10, '饮料', 8, 2);

-- ----------------------------
-- Table structure for order_items
-- ----------------------------
DROP TABLE IF EXISTS `order_items`;
CREATE TABLE `order_items`  (
  `item_id` int(11) NOT NULL AUTO_INCREMENT,
  `order_id` int(11) NOT NULL,
  `product_id` int(11) NOT NULL,
  `quantity` int(11) NOT NULL,
  `unit_price` decimal(10, 2) NOT NULL,
  PRIMARY KEY (`item_id`) USING BTREE,
  INDEX `order_id`(`order_id` ASC) USING BTREE,
  INDEX `product_id`(`product_id` ASC) USING BTREE,
  CONSTRAINT `order_items_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `order_items_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of order_items
-- ----------------------------
INSERT INTO `order_items` VALUES (1, 1, 1, 1, 7999.00);
INSERT INTO `order_items` VALUES (2, 2, 6, 1, 3999.00);
INSERT INTO `order_items` VALUES (3, 3, 7, 1, 899.00);
INSERT INTO `order_items` VALUES (4, 4, 9, 1, 9.90);
INSERT INTO `order_items` VALUES (5, 5, 5, 1, 4599.00);
INSERT INTO `order_items` VALUES (6, 6, 2, 1, 6999.00);
INSERT INTO `order_items` VALUES (7, 7, 8, 1, 299.00);
INSERT INTO `order_items` VALUES (8, 8, 10, 1, 3.50);
INSERT INTO `order_items` VALUES (9, 9, 4, 1, 5999.00);
INSERT INTO `order_items` VALUES (10, 10, 3, 1, 4999.00);

-- ----------------------------
-- Table structure for orders
-- ----------------------------
DROP TABLE IF EXISTS `orders`;
CREATE TABLE `orders`  (
  `order_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `total_amount` decimal(10, 2) NOT NULL,
  `order_status` tinyint(4) NOT NULL COMMENT '1-待付款,2-已付款,3-已发货,4-已完成,5-已取消',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `pay_time` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`order_id`) USING BTREE,
  INDEX `user_id`(`user_id` ASC) USING BTREE,
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of orders
-- ----------------------------
INSERT INTO `orders` VALUES (1, 1, 7999.00, 4, '2023-10-01 10:00:00', '2023-10-01 10:30:00');
INSERT INTO `orders` VALUES (2, 1, 3999.00, 4, '2023-10-02 14:00:00', '2023-10-02 14:10:00');
INSERT INTO `orders` VALUES (3, 2, 899.00, 4, '2023-10-03 09:30:00', '2023-10-03 09:35:00');
INSERT INTO `orders` VALUES (4, 3, 9.90, 4, '2023-10-04 11:20:00', '2023-10-04 11:25:00');
INSERT INTO `orders` VALUES (5, 4, 4599.00, 3, '2023-10-05 16:40:00', '2023-10-05 16:45:00');
INSERT INTO `orders` VALUES (6, 5, 6999.00, 2, '2023-10-06 15:10:00', '2023-10-06 15:15:00');
INSERT INTO `orders` VALUES (7, 6, 299.00, 4, '2023-10-07 10:00:00', '2023-10-07 10:05:00');
INSERT INTO `orders` VALUES (8, 7, 3.50, 4, '2023-10-08 13:20:00', '2023-10-08 13:22:00');
INSERT INTO `orders` VALUES (9, 8, 5999.00, 1, '2023-10-09 08:50:00', NULL);
INSERT INTO `orders` VALUES (10, 9, 4999.00, 2, '2023-10-10 17:30:00', '2023-10-10 17:35:00');

-- ----------------------------
-- Table structure for products
-- ----------------------------
DROP TABLE IF EXISTS `products`;
CREATE TABLE `products`  (
  `product_id` int(11) NOT NULL AUTO_INCREMENT,
  `product_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `category_id` int(11) NULL DEFAULT NULL,
  `price` decimal(10, 2) NOT NULL,
  `stock` int(11) NOT NULL DEFAULT 0,
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `status` tinyint(4) NULL DEFAULT 1 COMMENT '1-在售,0-下架',
  PRIMARY KEY (`product_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of products
-- ----------------------------
INSERT INTO `products` VALUES (1, 'iPhone 15', 2, 7999.00, 80, 'Apple手机', '2025-12-27 18:39:54', 1);
INSERT INTO `products` VALUES (2, '华为Mate 60', 2, 6999.00, 80, '华为旗舰手机', '2025-12-27 18:39:54', 1);
INSERT INTO `products` VALUES (3, '小米14', 2, 4999.00, 120, '小米旗舰手机', '2025-12-27 18:39:54', 1);
INSERT INTO `products` VALUES (4, '联想笔记本', 3, 5999.00, 50, '轻薄本', '2025-12-27 18:39:54', 1);
INSERT INTO `products` VALUES (5, '戴尔台式机', 3, 4599.00, 30, '家用台式机', '2025-12-27 18:39:54', 1);
INSERT INTO `products` VALUES (6, '小米电视', 1, 3999.00, 40, '55寸智能电视', '2025-12-27 18:39:54', 1);
INSERT INTO `products` VALUES (7, '耐克运动鞋', 6, 899.00, 200, '男士运动鞋', '2025-12-27 18:39:54', 1);
INSERT INTO `products` VALUES (8, '阿迪达斯T恤', 6, 299.00, 300, '男士T恤', '2025-12-27 18:39:54', 1);
INSERT INTO `products` VALUES (9, '乐事薯片', 9, 9.90, 500, '原味薯片', '2025-12-27 18:39:54', 1);
INSERT INTO `products` VALUES (10, '可口可乐', 10, 3.50, 1000, '500ml瓶装', '2025-12-27 18:39:54', 1);

-- ----------------------------
-- Table structure for shopping_cart
-- ----------------------------
DROP TABLE IF EXISTS `shopping_cart`;
CREATE TABLE `shopping_cart`  (
  `cart_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `product_id` int(11) NOT NULL,
  `quantity` int(11) NOT NULL DEFAULT 1,
  `add_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`cart_id`) USING BTREE,
  UNIQUE INDEX `uk_user_product`(`user_id` ASC, `product_id` ASC) USING BTREE,
  INDEX `product_id`(`product_id` ASC) USING BTREE,
  CONSTRAINT `shopping_cart_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `shopping_cart_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of shopping_cart
-- ----------------------------
INSERT INTO `shopping_cart` VALUES (1, 1, 2, 1, '2023-10-11 08:00:00');
INSERT INTO `shopping_cart` VALUES (2, 1, 3, 1, '2023-10-11 08:05:00');
INSERT INTO `shopping_cart` VALUES (3, 2, 1, 1, '2023-10-11 09:00:00');
INSERT INTO `shopping_cart` VALUES (4, 3, 7, 2, '2023-10-11 10:00:00');
INSERT INTO `shopping_cart` VALUES (5, 4, 9, 5, '2023-10-11 11:00:00');
INSERT INTO `shopping_cart` VALUES (6, 5, 10, 10, '2023-10-11 12:00:00');
INSERT INTO `shopping_cart` VALUES (7, 6, 4, 1, '2023-10-11 13:00:00');
INSERT INTO `shopping_cart` VALUES (8, 7, 5, 1, '2023-10-11 14:00:00');
INSERT INTO `shopping_cart` VALUES (9, 8, 6, 1, '2023-10-11 15:00:00');
INSERT INTO `shopping_cart` VALUES (10, 9, 8, 3, '2023-10-11 16:00:00');

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `password` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `register_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `status` tinyint(4) NULL DEFAULT 1 COMMENT '1-正常,0-禁用',
  PRIMARY KEY (`user_id`) USING BTREE,
  UNIQUE INDEX `email`(`email` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of users
-- ----------------------------
INSERT INTO `users` VALUES (1, 'user1', '123', 'user1@test.com', '13800138001', '北京', '2025-12-27 18:39:54', 1);
INSERT INTO `users` VALUES (2, 'user2', '123', 'user2@test.com', '13800138002', '上海', '2025-12-27 18:39:54', 1);
INSERT INTO `users` VALUES (3, 'user3', '123', 'user3@test.com', '13800138003', '广州', '2025-12-27 18:39:54', 1);
INSERT INTO `users` VALUES (4, 'user4', '123', 'user4@test.com', '13800138004', '深圳', '2025-12-27 18:39:54', 1);
INSERT INTO `users` VALUES (5, 'user5', '123', 'user5@test.com', '13800138005', '杭州', '2025-12-27 18:39:54', 1);
INSERT INTO `users` VALUES (6, 'user6', '123', 'user6@test.com', '13800138006', '成都', '2025-12-27 18:39:54', 1);
INSERT INTO `users` VALUES (7, 'user7', '123', 'user7@test.com', '13800138007', '武汉', '2025-12-27 18:39:54', 1);
INSERT INTO `users` VALUES (8, 'user8', '123', 'user8@test.com', '13800138008', '南京', '2025-12-27 18:39:54', 1);
INSERT INTO `users` VALUES (9, 'user9', '123', 'user9@test.com', '13800138009', '西安', '2025-12-27 18:39:54', 1);
INSERT INTO `users` VALUES (10, 'user10', '123', 'user10@test.com', '13800138010', '重庆', '2025-12-27 18:39:54', 1);

SET FOREIGN_KEY_CHECKS = 1;
