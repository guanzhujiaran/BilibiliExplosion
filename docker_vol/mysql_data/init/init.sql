-- --------------------------------------------------------
-- 主机:                           127.0.0.1
-- 服务器版本:                        8.0.43 - MySQL Community Server - GPL
-- 服务器操作系统:                      Win64
-- HeidiSQL 版本:                  12.11.0.7085
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- 导出 bili_reserve 的数据库结构
CREATE DATABASE IF NOT EXISTS `bili_reserve` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `bili_reserve`;

-- 导出  表 bili_reserve.t_reserve_round_info 结构
CREATE TABLE IF NOT EXISTS `t_reserve_round_info` (
  `id` int NOT NULL AUTO_INCREMENT,
  `round_id` int NOT NULL,
  `is_finished` tinyint(1) NOT NULL,
  `round_start_ts` int NOT NULL,
  `round_add_num` int NOT NULL,
  `round_lot_num` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `round_id` (`round_id`)
) ENGINE=InnoDB AUTO_INCREMENT=425 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 bili_reserve.t_up_reserve_relation_info 结构
CREATE TABLE IF NOT EXISTS `t_up_reserve_relation_info` (
  `code` int DEFAULT NULL,
  `message` text,
  `ttl` int DEFAULT NULL,
  `sid` int DEFAULT NULL,
  `name` text,
  `total` bigint DEFAULT NULL,
  `stime` int DEFAULT NULL,
  `etime` int DEFAULT NULL,
  `isFollow` int DEFAULT NULL,
  `state` int DEFAULT NULL,
  `oid` text,
  `type` int DEFAULT NULL,
  `upmid` bigint DEFAULT NULL,
  `reserveRecordCtime` int DEFAULT NULL,
  `livePlanStartTime` int DEFAULT NULL,
  `upActVisible` int DEFAULT NULL,
  `lotteryType` int DEFAULT NULL,
  `text` text,
  `jumpUrl` text,
  `dynamicId` text,
  `reserveTotalShowLimit` bigint DEFAULT NULL,
  `desc` text,
  `start_show_time` int DEFAULT NULL,
  `BaseJumpUrl` text,
  `OidView` bigint DEFAULT NULL,
  `ids` int NOT NULL,
  `hide` text,
  `ext` text,
  `subType` text,
  `productIdPrice` json DEFAULT NULL,
  `reserve_products` json DEFAULT NULL,
  `raw_JSON` json DEFAULT NULL,
  `reserve_round_id` int DEFAULT NULL,
  `new_field` json DEFAULT NULL COMMENT '是否有新的字段',
  PRIMARY KEY (`ids`),
  KEY `reserve_round_id` (`reserve_round_id`),
  KEY `available_reserve_lottery` (`lotteryType`,`state`,`etime`),
  KEY `global_index` (`code`,`sid`,`name`(100),`total`,`stime`,`etime`,`state`,`oid`(100),`type`,`upmid`,`lotteryType`,`text`(100),`jumpUrl`(100),`dynamicId`(100),`desc`(100),`ids`),
  CONSTRAINT `t_up_reserve_relation_info_ibfk_1` FOREIGN KEY (`reserve_round_id`) REFERENCES `t_reserve_round_info` (`round_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。


-- 导出 bilidb 的数据库结构
CREATE DATABASE IF NOT EXISTS `bilidb` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `bilidb`;

-- 导出  表 bilidb.t_activity_lottery 结构
CREATE TABLE IF NOT EXISTS `t_activity_lottery` (
  `pk` int NOT NULL AUTO_INCREMENT,
  `traffic_card_id` int DEFAULT NULL,
  `lotteryId` varchar(50) DEFAULT NULL,
  `continueTimes` json DEFAULT NULL,
  `list` json DEFAULT NULL,
  PRIMARY KEY (`pk`),
  KEY `FK_activity_lottery_t_traffic_card` (`traffic_card_id`),
  CONSTRAINT `FK_activity_lottery_t_traffic_card` FOREIGN KEY (`traffic_card_id`) REFERENCES `t_traffic_card` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 bilidb.t_activity_match_lottery 结构
CREATE TABLE IF NOT EXISTS `t_activity_match_lottery` (
  `pk` int NOT NULL AUTO_INCREMENT,
  `traffic_card_id` int DEFAULT NULL,
  `lottery_id` varchar(50) DEFAULT NULL,
  `activity_id` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`pk`),
  KEY `FK_activity_match_lottery_t_traffic_card` (`traffic_card_id`),
  CONSTRAINT `FK_activity_match_lottery_t_traffic_card` FOREIGN KEY (`traffic_card_id`) REFERENCES `t_traffic_card` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 bilidb.t_activity_match_task 结构
CREATE TABLE IF NOT EXISTS `t_activity_match_task` (
  `pk` int NOT NULL AUTO_INCREMENT,
  `traffic_card_id` int NOT NULL,
  `task_desc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `interact_type` json DEFAULT NULL,
  `task_group_id` json DEFAULT NULL,
  `task_name` varchar(50) DEFAULT NULL,
  `url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  PRIMARY KEY (`pk`),
  KEY `FK_t_activity_match_task_t_traffic_card` (`traffic_card_id`),
  CONSTRAINT `FK_t_activity_match_task_t_traffic_card` FOREIGN KEY (`traffic_card_id`) REFERENCES `t_traffic_card` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=39 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 bilidb.t_capsule 结构
CREATE TABLE IF NOT EXISTS `t_capsule` (
  `pk` int NOT NULL AUTO_INCREMENT,
  `functional_card_id` int NOT NULL,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `jump_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `icon_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  PRIMARY KEY (`pk`),
  KEY `FK_t_capsule_t_functional_card` (`functional_card_id`),
  CONSTRAINT `FK_t_capsule_t_functional_card` FOREIGN KEY (`functional_card_id`) REFERENCES `t_functional_card` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 bilidb.t_click_area_card 结构
CREATE TABLE IF NOT EXISTS `t_click_area_card` (
  `id` int NOT NULL AUTO_INCREMENT,
  `json_data` json DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=327 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 bilidb.t_era_jika 结构
CREATE TABLE IF NOT EXISTS `t_era_jika` (
  `pk` int NOT NULL AUTO_INCREMENT,
  `traffic_card_id` int NOT NULL,
  `activityUrl` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT '',
  `jikaId` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT '',
  `topId` int DEFAULT NULL,
  `topName` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT '',
  PRIMARY KEY (`pk`),
  KEY `idx_traffic_card_id` (`traffic_card_id`),
  CONSTRAINT `FK_era_jika_t_traffic_card` FOREIGN KEY (`traffic_card_id`) REFERENCES `t_traffic_card` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 bilidb.t_era_lottery 结构
CREATE TABLE IF NOT EXISTS `t_era_lottery` (
  `pk` int NOT NULL AUTO_INCREMENT,
  `traffic_card_id` int NOT NULL,
  `activity_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `gifts` json DEFAULT NULL,
  `icon` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `lottery_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `lottery_type` int DEFAULT NULL,
  `per_time` int DEFAULT NULL,
  `point_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  PRIMARY KEY (`pk`),
  KEY `FK_era_lottery_t_traffic_card` (`traffic_card_id`),
  CONSTRAINT `FK_era_lottery_t_traffic_card` FOREIGN KEY (`traffic_card_id`) REFERENCES `t_traffic_card` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=222 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 bilidb.t_era_task 结构
CREATE TABLE IF NOT EXISTS `t_era_task` (
  `pk` int NOT NULL AUTO_INCREMENT,
  `traffic_card_id` int NOT NULL,
  `awardName` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `taskDes` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `taskId` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `taskName` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `taskType` int DEFAULT NULL,
  `topicID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `topicName` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  PRIMARY KEY (`pk`),
  KEY `FK__t_traffic_card` (`traffic_card_id`),
  CONSTRAINT `FK__t_traffic_card` FOREIGN KEY (`traffic_card_id`) REFERENCES `t_traffic_card` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=984 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 bilidb.t_era_video 结构
CREATE TABLE IF NOT EXISTS `t_era_video` (
  `pk` int NOT NULL AUTO_INCREMENT,
  `traffic_card_id` int DEFAULT NULL,
  `poolList` json DEFAULT NULL,
  `topic_id` int DEFAULT NULL,
  `topic_name` varchar(50) DEFAULT NULL,
  `videoSource_id` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`pk`),
  KEY `FK_era_video_t_traffic_card` (`traffic_card_id`),
  CONSTRAINT `FK_era_video_t_traffic_card` FOREIGN KEY (`traffic_card_id`) REFERENCES `t_traffic_card` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=756 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 bilidb.t_functional_card 结构
CREATE TABLE IF NOT EXISTS `t_functional_card` (
  `id` int NOT NULL AUTO_INCREMENT,
  `traffic_card_id` int DEFAULT NULL,
  `json_data` json DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `t_functional_card_ibfk_1` (`traffic_card_id`),
  CONSTRAINT `t_functional_card_ibfk_1` FOREIGN KEY (`traffic_card_id`) REFERENCES `t_traffic_card` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=4123 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 bilidb.t_spaceseries 结构
CREATE TABLE IF NOT EXISTS `t_spaceseries` (
  `series_id` int NOT NULL DEFAULT (0),
  `mid` bigint DEFAULT NULL,
  `data` json DEFAULT NULL,
  `name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_zh_0900_as_cs COMMENT '播放列表的名称',
  PRIMARY KEY (`series_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='B站播放列表';

-- 数据导出被取消选择。

-- 导出  表 bilidb.t_topic 结构
CREATE TABLE IF NOT EXISTS `t_topic` (
  `topic_id` int NOT NULL,
  `raw_JSON` json DEFAULT NULL,
  `click_area_card_id` int DEFAULT NULL,
  `functional_card_id` int DEFAULT NULL,
  `topic_detail_id` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT (now()),
  `update_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`topic_id`),
  UNIQUE KEY `topic_id` (`topic_id`),
  KEY `click_area_card_id` (`click_area_card_id`),
  KEY `functional_card_id` (`functional_card_id`),
  KEY `topic_detail_id` (`topic_detail_id`),
  CONSTRAINT `t_topic_ibfk_1` FOREIGN KEY (`click_area_card_id`) REFERENCES `t_click_area_card` (`id`),
  CONSTRAINT `t_topic_ibfk_2` FOREIGN KEY (`functional_card_id`) REFERENCES `t_functional_card` (`id`),
  CONSTRAINT `t_topic_ibfk_3` FOREIGN KEY (`topic_detail_id`) REFERENCES `t_top_details` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 bilidb.t_topic_creator 结构
CREATE TABLE IF NOT EXISTS `t_topic_creator` (
  `face` text,
  `name` text,
  `uid` bigint NOT NULL,
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 bilidb.t_topic_item 结构
CREATE TABLE IF NOT EXISTS `t_topic_item` (
  `pkid` int NOT NULL AUTO_INCREMENT,
  `back_color` text,
  `ctime` int DEFAULT NULL,
  `description` text,
  `discuss` bigint DEFAULT NULL,
  `dynamics` bigint DEFAULT NULL,
  `fav` bigint DEFAULT NULL,
  `id` bigint DEFAULT NULL,
  `jump_url` text,
  `like` bigint DEFAULT NULL,
  `name` text,
  `share` bigint DEFAULT NULL,
  `share_pic` text,
  `share_url` text,
  `view` bigint DEFAULT NULL,
  `show_interact_data` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`pkid`)
) ENGINE=InnoDB AUTO_INCREMENT=1103752 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 bilidb.t_top_details 结构
CREATE TABLE IF NOT EXISTS `t_top_details` (
  `id` int NOT NULL AUTO_INCREMENT,
  `close_pub_layer_entry` tinyint(1) DEFAULT NULL,
  `has_create_jurisdiction` tinyint(1) DEFAULT NULL,
  `operation_content` json DEFAULT NULL,
  `word_color` int DEFAULT NULL,
  `head_img_url` varchar(255) DEFAULT NULL,
  `head_img_backcolor` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `topic_item_id` int DEFAULT NULL,
  `topic_creator_id` bigint DEFAULT NULL COMMENT '如果是null代表可能是系统发布的话题，热议类新闻等内容，不算uid',
  PRIMARY KEY (`id`),
  KEY `topic_item_id` (`topic_item_id`),
  KEY `topic_creator_id` (`topic_creator_id`),
  CONSTRAINT `t_top_details_ibfk_1` FOREIGN KEY (`topic_item_id`) REFERENCES `t_topic_item` (`pkid`),
  CONSTRAINT `t_top_details_ibfk_2` FOREIGN KEY (`topic_creator_id`) REFERENCES `t_topic_creator` (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=1103751 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 bilidb.t_traffic_card 结构
CREATE TABLE IF NOT EXISTS `t_traffic_card` (
  `id` int NOT NULL AUTO_INCREMENT,
  `benefit_point` text,
  `card_desc` text,
  `icon_url` text,
  `jump_title` text,
  `jump_url` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '不同的话题可能有相同的活动链接，入库的时候查一下有没有相同的jump_url',
  `name` text,
  `my_activity_status` smallint DEFAULT '0' COMMENT '0：未查询活动\r\n1：已成功查询\r\n2：查询了，但获取到的活动为空，也就是未知的活动\r\n3：查询出错了，去日志里查原因',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4011 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。


-- 导出 biliopusdb 的数据库结构
CREATE DATABASE IF NOT EXISTS `biliopusdb` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `biliopusdb`;

-- 导出  表 biliopusdb.t_lotdyninfo 结构
CREATE TABLE IF NOT EXISTS `t_lotdyninfo` (
  `dynId` bigint NOT NULL DEFAULT (0),
  `dynamicUrl` text,
  `authorName` text,
  `up_uid` bigint DEFAULT NULL,
  `pubTime` datetime DEFAULT NULL,
  `dynContent` text,
  `commentCount` int DEFAULT NULL,
  `repostCount` int DEFAULT NULL,
  `highlightWords` text,
  `officialLotType` text,
  `officialLotId` text,
  `isOfficialAccount` tinyint(1) DEFAULT NULL,
  `isManualReply` text,
  `isFollowed` tinyint(1) DEFAULT NULL,
  `isLot` tinyint(1) DEFAULT NULL,
  `hashTag` text,
  `dynLotRound_id` int DEFAULT NULL,
  `rawJsonStr` json DEFAULT NULL,
  PRIMARY KEY (`dynId`),
  KEY `dynLotRound_id` (`dynLotRound_id`,`up_uid`,`isLot`,`dynId`) USING BTREE,
  CONSTRAINT `t_lotdyninfo_ibfk_1` FOREIGN KEY (`dynLotRound_id`) REFERENCES `t_lotmaininfo` (`lotRound_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 biliopusdb.t_lotmaininfo 结构
CREATE TABLE IF NOT EXISTS `t_lotmaininfo` (
  `id` int NOT NULL AUTO_INCREMENT,
  `lotRound_id` int DEFAULT NULL,
  `allNum` int DEFAULT NULL COMMENT '需要去检查的抽奖动态数量',
  `lotNum` int DEFAULT NULL COMMENT '检查完成之后的总共的抽奖数量',
  `uselessNum` int DEFAULT NULL,
  `isRoundFinished` tinyint(1) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT (now()),
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `lotRound_id` (`lotRound_id`)
) ENGINE=InnoDB AUTO_INCREMENT=782 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 biliopusdb.t_lotuserinfo 结构
CREATE TABLE IF NOT EXISTS `t_lotuserinfo` (
  `uid` bigint NOT NULL AUTO_INCREMENT,
  `uname` text,
  `updateNum` int DEFAULT NULL,
  `updatetime` datetime DEFAULT NULL,
  `isUserSpaceFinished` int DEFAULT NULL,
  `offset` bigint DEFAULT NULL COMMENT '保存每一次循环之后的offset，如果中途推出了，从这个offset接着获取',
  `latestFinishedOffset` bigint DEFAULT NULL COMMENT '最后一次获取结束时候的offset，作为判断是否获取重复的标准',
  `isPubLotUser` tinyint(1) DEFAULT NULL COMMENT '0：要获取的抽奖用户的空间数据（判断这个抽奖号是否活跃的重要标志）\r\n1：发布抽奖用户的空间数据（不重要）',
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=3546973604940064 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 biliopusdb.t_lotuserspaceresp 结构
CREATE TABLE IF NOT EXISTS `t_lotuserspaceresp` (
  `spaceUid` bigint DEFAULT NULL,
  `spaceOffset` bigint NOT NULL DEFAULT (0),
  `spaceRespJson` json DEFAULT NULL,
  `dynLotRound_id` int DEFAULT NULL,
  PRIMARY KEY (`spaceOffset`),
  KEY `spaceUid` (`spaceUid`),
  KEY `FK_t_lotuserspaceresp_t_lotmaininfo` (`dynLotRound_id`),
  CONSTRAINT `FK_t_lotuserspaceresp_t_lotmaininfo` FOREIGN KEY (`dynLotRound_id`) REFERENCES `t_lotmaininfo` (`lotRound_id`),
  CONSTRAINT `t_lotuserspaceresp_ibfk_1` FOREIGN KEY (`spaceUid`) REFERENCES `t_lotuserinfo` (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 biliopusdb.t_riddynid 结构
CREATE TABLE IF NOT EXISTS `t_riddynid` (
  `dynamic_id` bigint NOT NULL,
  `rid` bigint DEFAULT NULL,
  `dynamic_type` tinyint DEFAULT NULL,
  PRIMARY KEY (`dynamic_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。


-- 导出 dyndetail 的数据库结构
CREATE DATABASE IF NOT EXISTS `dyndetail` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `dyndetail`;

-- 导出  表 dyndetail.article_pub_record 结构
CREATE TABLE IF NOT EXISTS `article_pub_record` (
  `round_id` int DEFAULT NULL COMMENT '每一轮的号码',
  `lot_data_business_id` bigint NOT NULL,
  `pk` bigint NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`pk`) USING BTREE,
  UNIQUE KEY `lot_data_business_id` (`lot_data_business_id`),
  CONSTRAINT `FK__lotdata` FOREIGN KEY (`lot_data_business_id`) REFERENCES `lotdata` (`business_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1665 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='发布专栏记录';

-- 数据导出被取消选择。

-- 导出  表 dyndetail.bilidyndetail 结构
CREATE TABLE IF NOT EXISTS `bilidyndetail` (
  `rid` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '',
  `dynamic_id` text COLLATE utf8mb4_general_ci,
  `dynData` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `lot_id` bigint DEFAULT NULL,
  `dynamic_created_time` text COLLATE utf8mb4_general_ci,
  `rid_int` bigint GENERATED ALWAYS AS (cast(`rid` as signed)) STORED,
  `dynamic_id_int` bigint GENERATED ALWAYS AS (cast(`dynamic_id` as signed)) STORED,
  PRIMARY KEY (`rid`),
  KEY `idx_dynamic_id` (`dynamic_id`(255)),
  KEY `idx_lot_id` (`lot_id`),
  KEY `idx_dynamic_created_time` (`dynamic_created_time`(255)),
  KEY `rid` (`rid`),
  KEY `idx_rid_int` (`rid_int`),
  KEY `dynamic_id_int` (`dynamic_id_int`),
  CONSTRAINT `biliDynDetail_FK_0_0` FOREIGN KEY (`lot_id`) REFERENCES `lotdata` (`lottery_id`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 数据导出被取消选择。

-- 导出  表 dyndetail.lotdata 结构
CREATE TABLE IF NOT EXISTS `lotdata` (
  `lottery_id` bigint NOT NULL AUTO_INCREMENT,
  `business_id` bigint DEFAULT NULL,
  `status` bigint DEFAULT NULL,
  `lottery_time` bigint DEFAULT NULL,
  `lottery_at_num` bigint DEFAULT NULL,
  `lottery_feed_limit` bigint DEFAULT NULL,
  `first_prize` bigint DEFAULT NULL,
  `second_prize` bigint DEFAULT NULL,
  `third_prize` bigint DEFAULT NULL,
  `lottery_result` text COLLATE utf8mb4_general_ci,
  `first_prize_cmt` text COLLATE utf8mb4_general_ci,
  `second_prize_cmt` text COLLATE utf8mb4_general_ci,
  `third_prize_cmt` text COLLATE utf8mb4_general_ci,
  `first_prize_pic` text COLLATE utf8mb4_general_ci,
  `second_prize_pic` text COLLATE utf8mb4_general_ci,
  `third_prize_pic` text COLLATE utf8mb4_general_ci,
  `need_post` bigint DEFAULT NULL,
  `business_type` bigint DEFAULT NULL,
  `sender_uid` bigint DEFAULT NULL,
  `prize_type_first` text COLLATE utf8mb4_general_ci,
  `prize_type_second` text COLLATE utf8mb4_general_ci,
  `prize_type_third` text COLLATE utf8mb4_general_ci,
  `pay_status` bigint DEFAULT NULL,
  `ts` bigint DEFAULT NULL,
  `_gt_` bigint DEFAULT NULL,
  `has_charge_right` text COLLATE utf8mb4_general_ci,
  `lottery_detail_url` text COLLATE utf8mb4_general_ci,
  `participants` bigint DEFAULT NULL,
  `participated` text COLLATE utf8mb4_general_ci,
  `vip_batch_sign` text COLLATE utf8mb4_general_ci,
  `exclusive_level` text COLLATE utf8mb4_general_ci,
  `followed` bigint DEFAULT NULL,
  `reposted` bigint DEFAULT NULL,
  `custom_extra_key` text COLLATE utf8mb4_general_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`lottery_id`),
  KEY `business_id` (`business_id`),
  KEY `lottery_time` (`lottery_time`),
  KEY `sender_uid` (`sender_uid`),
  KEY `idx_lottery_id` (`lottery_id`,`business_id`,`lottery_time`,`sender_uid`,`business_type`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=2920829 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 数据导出被取消选择。


-- 导出 information_schema 的数据库结构
CREATE DATABASE IF NOT EXISTS `information_schema` /*!40100 DEFAULT CHARACTER SET utf8mb3 */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `information_schema`;

-- 导出  表 information_schema.ADMINISTRABLE_ROLE_AUTHORIZATIONS 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`ADMINISTRABLE_ROLE_AUTHORIZATIONS` AS select `information_schema`.`applicable_roles`.`USER` AS `USER`,`information_schema`.`applicable_roles`.`HOST` AS `HOST`,`information_schema`.`applicable_roles`.`GRANTEE` AS `GRANTEE`,`information_schema`.`applicable_roles`.`GRANTEE_HOST` AS `GRANTEE_HOST`,`information_schema`.`applicable_roles`.`ROLE_NAME` AS `ROLE_NAME`,`information_schema`.`applicable_roles`.`ROLE_HOST` AS `ROLE_HOST`,`information_schema`.`applicable_roles`.`IS_GRANTABLE`IF NOT EXISTS  AS `IS_GRANTABLE`,`information_schema`.`applicable_roles`.`IS_DEFAULT` AS `IS_DEFAULT`,`information_schema`.`applicable_roles`.`IS_MANDATORY` AS `IS_MANDATORY` from `information_schema`.`APPLICABLE_ROLES` where (`information_schema`.`applicable_roles`.`IS_GRANTABLE` = 'YES');

-- 数据导出被取消选择。

-- 导出  表 information_schema.APPLICABLE_ROLES 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`APPLICABLE_ROLES` AS with recursive `role_graph` (`c_parent_user`,`c_parent_host`,`c_from_user`,`c_from_host`,`c_to_user`,`c_to_host`,`role_path`,`c_with_admin`,`c_enabled`) as (select internal_get_username() AS `INTERNAL_GET_USERNAME()`,internal_get_hostname() AS `INTERNAL_GET_HOSTNAME()`,internal_get_username() AS `INTERNAL_GET_USERNAME()`,internal_get_hostname() AS `INTERNAL_GET_HOSTNAME()`,cast('' as char(64) charset utf8mb4) AS `CAST('' as CHAR(64) CHARSET utf8mb4)`,cast('' as char(255) charset utf8mb4) AS `CAST('' as CHAR(255) CHARSET utf8mb4)`,cast(sha2(concat(quote(internal_get_username()),'@',quote(internal_get_hostname())),256) as char(17000) charset utf8mb4) AS `CAST(SHA2(CONCAT(QUOTE(INTERNAL_GET_USERNAME()),'@',                        QUOTE(INTERNAL_GET_HOSTNAME())), 256)            AS CHAR(17000) CHARSET utf8mb4)`,cast('N' as char(1) charset utf8mb4) AS `CAST('N' as CHAR(1) CHARSET utf8mb4)`,false AS `FALSE` union select internal_get_username() AS `INTERNAL_GET_USERNAME()`,internal_get_hostname() AS `INTERNAL_GET_HOSTNAME()`,`mandatory_roles`.`ROLE_NAME` AS `ROLE_NAME`,`mandatory_roles`.`ROLE_HOST` AS `ROLE_HOST`,internal_get_username() AS `INTERNAL_GET_USERNAME()`,internal_get_hostname() AS `INTERNAL_GET_HOSTNAME()`,cast(sha2(concat(quote(`mandatory_roles`.`ROLE_NAME`),'@',convert(quote(`mandatory_roles`.`ROLE_HOST`) using utf8mb4)),256) as char(17000) charset utf8mb4) AS `CAST(SHA2(CONCAT(QUOTE(ROLE_NAME),'@',                   CONVERT(QUOTE(ROLE_HOST) using utf8mb4)), 256)              AS CHAR(17000) CHARSET utf8mb4)`,cast('N' as char(1) charset utf8mb4) AS `CAST('N' as CHAR(1) CHARSET utf8mb4)`,false AS `FALSE` from json_table(internal_get_mandatory_roles_json(), '$[*]' columns (`ROLE_NAME` varchar(255) character set utf8mb4 path '$.ROLE_NAME', `ROLE_HOST` varchar(255) character set utf8mb4 path '$.ROLE_HOST')) `mandatory_roles` where concat(quote(`mandatory_roles`.`ROLE_NAME`),'@',convert(quote(`mandatory_roles`.`ROLE_HOST`) using utf8mb4)) in (select concat(convert(quote(`mysql`.`role_edges`.`FROM_USER`) using utf8mb4),'@',convert(quote(`mysql`.`role_edges`.`FROM_HOST`) using utf8mb4)) from `mysql`.`role_edges` where ((`mysql`.`role_edges`.`TO_USER` = internal_get_username()) and (convert(`mysql`.`role_edges`.`TO_HOST` using utf8mb4) = convert(internal_get_hostname() using utf8mb4)))) is false union select `role_graph`.`c_parent_user` AS `c_parent_user`,`role_graph`.`c_parent_host` AS `c_parent_host`,`mysql`.`role_edges`.`FROM_USER` AS `FROM_USER`,`mysql`.`role_edges`.`FROM_HOST` AS `FROM_HOST`,`mysql`.`role_edges`.`TO_USER` AS `TO_USER`,`mysql`.`role_edges`.`TO_HOST` AS `TO_HOST`,if((locate(sha2(concat(convert(quote(`mysql`.`role_edges`.`FROM_USER`) using utf8mb4),'@',convert(quote(`mysql`.`role_edges`.`FROM_HOST`) using utf8mb4)),256),`role_graph`.`role_path`) = 0),concat(`role_graph`.`role_path`,'->',convert(sha2(concat(convert(quote(`mysql`.`role_edges`.`FROM_USER`) using utf8mb4),'@',convert(quote(`mysql`.`role_edges`.`FROM_HOST`) using utf8mb4)),256) using utf8mb4)),NULL) AS `IF(LOCATE(SHA2(CONCAT(QUOTE(FROM_USER),'@',                      CONVERT(QUOTE(FROM_HOST) using utf8mb4)), 256),                 role_path) = 0,          CONCAT(role_path,'->', SHA2(CONCAT(QUOTE(FROM_USER),'@',           CONVERT(QUOTE(FROM_HOST) using utf8`,`mysql`.`role_edges`.`WITH_ADMIN_OPTION` AS `WITH_ADMIN_OPTION`,if(((0 <> `role_graph`.`c_enabled`) or (0 <> internal_is_enabled_role(`mysql`.`role_edges`.`FROM_USER`,`mysql`.`role_edges`.`FROM_HOST`))),true,false) AS `IF(c_enabled OR        INTERNAL_IS_ENABLED_ROLE(FROM_USER, FROM_HOST), TRUE, FALSE)` from (`mysql`.`role_edges` join `role_graph`) where ((`mysql`.`role_edges`.`TO_USER` = `role_graph`.`c_from_user`) and (convert(`mysql`.`role_edges`.`TO_HOST` using utf8mb4) = `role_graph`.`c_from_host`) and (`role_graph`.`role_path` is not null))) select distinct `role_graph`.`c_parent_user` AS `USER`,`role_graph`.`c_parent_host` AS `HOST`,`role_graph`.`c_to_user` AS `GRANTEE`,`role_graph`.`c_to_host` AS `GRANTEE_HOST`,`role_graph`.`c_from_user` AS `ROLE_NAME`,`role_graph`.`c_from_host` AS `ROLE_HOST`,if((`role_graph`.`c_with_admin` = 'N'),'NO','YES') AS `IS_GRANTABLE`IF NOT EXISTS ,(select if(count(0),'YES','NO') from `mysql`.`default_roles` where ((`mysql`.`default_roles`.`DEFAULT_ROLE_USER` = `role_graph`.`c_from_user`) and (convert(`mysql`.`default_roles`.`DEFAULT_ROLE_HOST` using utf8mb4) = `role_graph`.`c_from_host`) and (`mysql`.`default_roles`.`USER` = `role_graph`.`c_parent_user`) and (convert(`mysql`.`default_roles`.`HOST` using utf8mb4) = `role_graph`.`c_parent_host`))) AS `IS_DEFAULT`,if(internal_is_mandatory_role(`role_graph`.`c_from_user`,`role_graph`.`c_from_host`),'YES','NO') AS `IS_MANDATORY` from `role_graph` where (`role_graph`.`c_to_user` <> '');

-- 数据导出被取消选择。

-- 导出  表 information_schema.CHARACTER_SETS 结构
CREATIF NOT EXISTS E ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`CHARACTER_SETS` AS select `cs`.`name` AS `CHARACTER_SET_NAME`,`col`.`name` AS `DEFAULT_COLLATE_NAME`,`cs`.`comment` AS `DESCRIPTION`,`cs`.`mb_max_length` AS `MAXLEN` from (`mysql`.`character_sets` `cs` join `mysql`.`collations` `col` on((`cs`.`default_collation_id` = `col`.`id`)));

-- 数据导出被取消选择。

-- 导出  表 information_schema.CHECK_CONSTRAINTS 结构
CREATIF NOT EXISTS E ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`CHECK_CONSTRAINTS` AS select (`cat`.`name` collate utf8mb3_tolower_ci) AS `CONSTRAINT_CATALOG`,(`sch`.`name` collate utf8mb3_tolower_ci) AS `CONSTRAINT_SCHEMA`,`cc`.`name` AS `CONSTRAINT_NAME`,`cc`.`check_clause_utf8` AS `CHECK_CLAUSE` from (((`mysql`.`check_constraints` `cc` join `mysql`.`tables` `tbl` on((`cc`.`table_id` = `tbl`.`id`))) join `mysql`.`schemata` `sch` on((`tbl`.`schema_id` = `sch`.`id`))) join `mysql`.`catalogs` `cat` on((`cat`.`id` = `sch`.`catalog_id`))) where ((0 <> can_access_table(`sch`.`name`,`tbl`.`name`)) and (0 <> is_visible_dd_object(`tbl`.`hidden`)));

-- 数据导出被取消选择。

-- 导出  表 information_schema.COLLATIONS 结构
CREATIF NOT EXISTS E ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`COLLATIONS` AS select `col`.`name` AS `COLLATION_NAME`,`cs`.`name` AS `CHARACTER_SET_NAME`,`col`.`id` AS `ID`,if(exists(select 1 from `mysql`.`character_sets` where (`mysql`.`character_sets`.`default_collation_id` = `col`.`id`)),'Yes','') AS `IS_DEFAULT`,if(`col`.`is_compiled`,'Yes','') AS `IS_COMPILED`,`col`.`sort_length` AS `SORTLEN`,`col`.`pad_attribute` AS `PAD_ATTRIBUTE` from (`mysql`.`collations` `col` join `mysql`.`character_sets` `cs` on((`col`.`character_set_id` = `cs`.`id`)));

-- 数据导出被取消选择。

-- 导出  表 information_schema.COLLATION_CHARACTER_SET_APPLICABILITY 结构
CREATIF NOT EXISTS E ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`COLLATION_CHARACTER_SET_APPLICABILITY` AS select `col`.`name` AS `COLLATION_NAME`,`cs`.`name` AS `CHARACTER_SET_NAME` from (`mysql`.`character_sets` `cs` join `mysql`.`collations` `col` on((`cs`.`id` = `col`.`character_set_id`)));

-- 数据导出被取消选择。

-- 导出  表 information_schema.COLUMNS 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`COLUMNS` AS select (`cat`.`name` collate utf8mb3_tolower_ci) AS `TABLE_IF NOT EXISTS CATALOG`,(`sch`.`name` collate utf8mb3_tolower_ci) AS `TABLE_SCHEMA`,(`tbl`.`name` collate utf8mb3_tolower_ci) AS `TABLE_NAME`,(`col`.`name` collate utf8mb3_tolower_ci) AS `COLUMN_NAME`,`col`.`ordinal_position` AS `ORDINAL_POSITION`,`col`.`default_value_utf8` AS `COLUMN_DEFAULT`,if((`col`.`is_nullable` = 1),'YES','NO') AS `IS_NULLABLE`,substring_index(substring_index(`col`.`column_type_utf8`,'(',1),' ',1) AS `DATA_TYPE`,internal_dd_char_length(`col`.`type`,`col`.`char_length`,`coll`.`name`,0) AS `CHARACTER_MAXIMUM_LENGTH`,internal_dd_char_length(`col`.`type`,`col`.`char_length`,`coll`.`name`,1) AS `CHARACTER_OCTET_LENGTH`,if((`col`.`numeric_precision` = 0),NULL,`col`.`numeric_precision`) AS `NUMERIC_PRECISION`,if(((`col`.`numeric_scale` = 0) and (`col`.`numeric_precision` = 0)),NULL,`col`.`numeric_scale`) AS `NUMERIC_SCALE`,`col`.`datetime_precision` AS `DATETIME_PRECISION`,(case `col`.`type` when 'MYSQL_TYPE_STRING' then if((`cs`.`name` = 'binary'),NULL,`cs`.`name`) when 'MYSQL_TYPE_VAR_STRING' then if((`cs`.`name` = 'binary'),NULL,`cs`.`name`) when 'MYSQL_TYPE_VARCHAR' then if((`cs`.`name` = 'binary'),NULL,`cs`.`name`) when 'MYSQL_TYPE_TINY_BLOB' then if((`cs`.`name` = 'binary'),NULL,`cs`.`name`) when 'MYSQL_TYPE_MEDIUM_BLOB' then if((`cs`.`name` = 'binary'),NULL,`cs`.`name`) when 'MYSQL_TYPE_BLOB' then if((`cs`.`name` = 'binary'),NULL,`cs`.`name`) when 'MYSQL_TYPE_LONG_BLOB' then if((`cs`.`name` = 'binary'),NULL,`cs`.`name`) when 'MYSQL_TYPE_ENUM' then if((`cs`.`name` = 'binary'),NULL,`cs`.`name`) when 'MYSQL_TYPE_SET' then if((`cs`.`name` = 'binary'),NULL,`cs`.`name`) else NULL end) AS `CHARACTER_SET_NAME`,(case `col`.`type` when 'MYSQL_TYPE_STRING' then if((`cs`.`name` = 'binary'),NULL,`coll`.`name`) when 'MYSQL_TYPE_VAR_STRING' then if((`cs`.`name` = 'binary'),NULL,`coll`.`name`) when 'MYSQL_TYPE_VARCHAR' then if((`cs`.`name` = 'binary'),NULL,`coll`.`name`) when 'MYSQL_TYPE_TINY_BLOB' then if((`cs`.`name` = 'binary'),NULL,`coll`.`name`) when 'MYSQL_TYPE_MEDIUM_BLOB' then if((`cs`.`name` = 'binary'),NULL,`coll`.`name`) when 'MYSQL_TYPE_BLOB' then if((`cs`.`name` = 'binary'),NULL,`coll`.`name`) when 'MYSQL_TYPE_LONG_BLOB' then if((`cs`.`name` = 'binary'),NULL,`coll`.`name`) when 'MYSQL_TYPE_ENUM' then if((`cs`.`name` = 'binary'),NULL,`coll`.`name`) when 'MYSQL_TYPE_SET' then if((`cs`.`name` = 'binary'),NULL,`coll`.`name`) else NULL end) AS `COLLATION_NAME`,`col`.`column_type_utf8` AS `COLUMN_TYPE`,`col`.`column_key` AS `COLUMN_KEY`,internal_get_dd_column_extra((`col`.`generation_expression_utf8` is null),`col`.`is_virtual`,`col`.`is_auto_increment`,`col`.`update_option`,if(length(`col`.`default_option`),true,false),`col`.`options`,`col`.`hidden`,`tbl`.`type`) AS `EXTRA`,get_dd_column_privileges(`sch`.`name`,`tbl`.`name`,`col`.`name`) AS `PRIVILEGES`,ifnull(`col`.`comment`,'') AS `COLUMN_COMMENT`,ifnull(`col`.`generation_expression_utf8`,'') AS `GENERATION_EXPRESSION`,`col`.`srs_id` AS `SRS_ID` from (((((`mysql`.`columns` `col` join `mysql`.`tables` `tbl` on((`col`.`table_id` = `tbl`.`id`))) join `mysql`.`schemata` `sch` on((`tbl`.`schema_id` = `sch`.`id`))) join `mysql`.`catalogs` `cat` on((`cat`.`id` = `sch`.`catalog_id`))) join `mysql`.`collations` `coll` on((`col`.`collation_id` = `coll`.`id`))) join `mysql`.`character_sets` `cs` on((`coll`.`character_set_id` = `cs`.`id`))) where ((0 <> internal_get_view_warning_or_error(`sch`.`name`,`tbl`.`name`,`tbl`.`type`,`tbl`.`options`)) and (0 <> can_access_column(`sch`.`name`,`tbl`.`name`,`col`.`name`)) and (0 <> is_visible_dd_object(`tbl`.`hidden`,(`col`.`hidden` not in ('Visible','User')),`col`.`options`)));

-- 数据导出被取消选择。

-- 导出  表 information_schema.COLUMNS_EXTENSIONS 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`COLUMNS_EXTENSIONS` AS select `cat`.`name` AS `TABLE_IF NOT EXISTS CATALOG`,`sch`.`name` AS `TABLE_SCHEMA`,`tbl`.`name` AS `TABLE_NAME`,(`col`.`name` collate utf8mb3_tolower_ci) AS `COLUMN_NAME`,`col`.`engine_attribute` AS `ENGINE_ATTRIBUTE`,`col`.`secondary_engine_attribute` AS `SECONDARY_ENGINE_ATTRIBUTE` from (((`mysql`.`columns` `col` join `mysql`.`tables` `tbl` on((`col`.`table_id` = `tbl`.`id`))) join `mysql`.`schemata` `sch` on((`tbl`.`schema_id` = `sch`.`id`))) join `mysql`.`catalogs` `cat` on((`cat`.`id` = `sch`.`catalog_id`))) where ((0 <> internal_get_view_warning_or_error(`sch`.`name`,`tbl`.`name`,`tbl`.`type`,`tbl`.`options`)) and (0 <> can_access_column(`sch`.`name`,`tbl`.`name`,`col`.`name`)) and (0 <> is_visible_dd_object(`tbl`.`hidden`,(`col`.`hidden` not in ('Visible','User')),`col`.`options`)));

-- 数据导出被取消选择。

-- 导出  表 information_schema.COLUMN_PRIVILEGES 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `COLUMN_PRIVILEGES` (
  `GRANTEE` varchar(292) NOT NULL DEFAULT '',
  `TABLE_CATALOG` varchar(512) NOT NULL DEFAULT '',
  `TABLE_SCHEMA` varchar(64) NOT NULL DEFAULT '',
  `TABLE_NAME` varchar(64) NOT NULL DEFAULT '',
  `COLUMN_NAME` varchar(64) NOT NULL DEFAULT '',
  `PRIVILEGE_TYPE` varchar(64) NOT NULL DEFAULT '',
  `IS_GRANTABLE` varchar(3) NOT NULL DEFAULT ''
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.COLUMN_STATISTICS 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`COLUMN_STATISTICS` AS select `mysql`.`column_statistics`.`schema_name` AS `SCHEMA_NAME`,`mysql`.`column_statistics`.`table_name` AS `TABLE_IF NOT EXISTS NAME`,`mysql`.`column_statistics`.`column_name` AS `COLUMN_NAME`,`mysql`.`column_statistics`.`histogram` AS `HISTOGRAM` from `mysql`.`column_statistics` where (0 <> can_access_table(`mysql`.`column_statistics`.`schema_name`,`mysql`.`column_statistics`.`table_name`));

-- 数据导出被取消选择。

-- 导出  表 information_schema.ENABLED_ROLES 结构
CREATIF NOT EXISTS E ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`ENABLED_ROLES` AS select `current_user_enabled_roles`.`ROLE_NAME` AS `ROLE_NAME`,`current_user_enabled_roles`.`ROLE_HOST` AS `ROLE_HOST`,(select if(count(0),'YES','NO') from `mysql`.`default_roles` where ((`mysql`.`default_roles`.`DEFAULT_ROLE_USER` = `current_user_enabled_roles`.`ROLE_NAME`) and (convert(`mysql`.`default_roles`.`DEFAULT_ROLE_HOST` using utf8mb4) = `current_user_enabled_roles`.`ROLE_HOST`) and (`mysql`.`default_roles`.`USER` = internal_get_username()) and (convert(`mysql`.`default_roles`.`HOST` using utf8mb4) = convert(internal_get_hostname() using utf8mb4)))) AS `IS_DEFAULT`,if(internal_is_mandatory_role(`current_user_enabled_roles`.`ROLE_NAME`,`current_user_enabled_roles`.`ROLE_HOST`),'YES','NO') AS `IS_MANDATORY` from json_table(internal_get_enabled_role_json(), '$[*]' columns (`ROLE_NAME` varchar(255) character set utf8mb4 path '$.ROLE_NAME', `ROLE_HOST` varchar(255) character set utf8mb4 path '$.ROLE_HOST')) `current_user_enabled_roles`;

-- 数据导出被取消选择。

-- 导出  表 information_schema.ENGINES 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `ENGINES` (
  `ENGINE` varchar(64) NOT NULL DEFAULT '',
  `SUPPORT` varchar(8) NOT NULL DEFAULT '',
  `COMMENT` varchar(80) NOT NULL DEFAULT '',
  `TRANSACTIONS` varchar(3) DEFAULT NULL,
  `XA` varchar(3) DEFAULT NULL,
  `SAVEPOINTS` varchar(3) DEFAULT NULL
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.EVENTS 结构
CREATIF NOT EXISTS E ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`EVENTS` AS select (`cat`.`name` collate utf8mb3_tolower_ci) AS `EVENT_CATALOG`,(`sch`.`name` collate utf8mb3_tolower_ci) AS `EVENT_SCHEMA`,`evt`.`name` AS `EVENT_NAME`,`evt`.`definer` AS `DEFINER`,`evt`.`time_zone` AS `TIME_ZONE`,'SQL' AS `EVENT_BODY`,`evt`.`definition_utf8` AS `EVENT_DEFINITION`,if((`evt`.`interval_value` is null),'ONE TIME','RECURRING') AS `EVENT_TYPE`,convert_tz(`evt`.`execute_at`,'+00:00',`evt`.`time_zone`) AS `EXECUTE_AT`,convert_interval_to_user_interval(`evt`.`interval_value`,`evt`.`interval_field`) AS `INTERVAL_VALUE`,`evt`.`interval_field` AS `INTERVAL_FIELD`,`evt`.`sql_mode` AS `SQL_MODE`,convert_tz(`evt`.`starts`,'+00:00',`evt`.`time_zone`) AS `STARTS`,convert_tz(`evt`.`ends`,'+00:00',`evt`.`time_zone`) AS `ENDS`,`evt`.`status` AS `STATUS`,if((`evt`.`on_completion` = 'DROP'),'NOT PRESERVE','PRESERVE') AS `ON_COMPLETION`,`evt`.`created` AS `CREATED`,`evt`.`last_altered` AS `LAST_ALTERED`,convert_tz(`evt`.`last_executed`,'+00:00',`evt`.`time_zone`) AS `LAST_EXECUTED`,`evt`.`comment` AS `EVENT_COMMENT`,`evt`.`originator` AS `ORIGINATOR`,`cs_client`.`name` AS `CHARACTER_SET_CLIENT`,`coll_conn`.`name` AS `COLLATION_CONNECTION`,`coll_db`.`name` AS `DATABASE_COLLATION` from ((((((`mysql`.`events` `evt` join `mysql`.`schemata` `sch` on((`evt`.`schema_id` = `sch`.`id`))) join `mysql`.`catalogs` `cat` on((`cat`.`id` = `sch`.`catalog_id`))) join `mysql`.`collations` `coll_client` on((`coll_client`.`id` = `evt`.`client_collation_id`))) join `mysql`.`character_sets` `cs_client` on((`cs_client`.`id` = `coll_client`.`character_set_id`))) join `mysql`.`collations` `coll_conn` on((`coll_conn`.`id` = `evt`.`connection_collation_id`))) join `mysql`.`collations` `coll_db` on((`coll_db`.`id` = `evt`.`schema_collation_id`))) where (0 <> can_access_event(`sch`.`name`));

-- 数据导出被取消选择。

-- 导出  表 information_schema.FILES 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`FILES` AS select internal_tablespace_id(`ts`.`name`,`tsf`.`file_name`,`ts`.`engine`,`ts`.`se_private_data`) AS `FILE_ID`,replace(if(((locate(left(`tsf`.`file_name`,1),'./') = 0) and (substr(`tsf`.`file_name`,2,1) <> ':')),concat('./',`tsf`.`file_name`),`tsf`.`file_name`),'\\','/') AS `FILE_NAME`,internal_tablespace_type(`ts`.`name`,`tsf`.`file_name`,`ts`.`engine`,`ts`.`se_private_data`) AS `FILE_TYPE`,`ts`.`name` AS `TABLESIF NOT EXISTS PACE_NAME`,'' AS `TABLE_CATALOG`,NULL AS `TABLE_SCHEMA`,NULL AS `TABLE_NAME`,internal_tablespace_logfile_group_name(`ts`.`name`,`tsf`.`file_name`,`ts`.`engine`,`ts`.`se_private_data`) AS `LOGFILE_GROUP_NAME`,internal_tablespace_logfile_group_number(`ts`.`name`,`tsf`.`file_name`,`ts`.`engine`,`ts`.`se_private_data`) AS `LOGFILE_GROUP_NUMBER`,`ts`.`engine` AS `ENGINE`,NULL AS `FULLTEXT_KEYS`,NULL AS `DELETED_ROWS`,NULL AS `UPDATE_COUNT`,internal_tablespace_free_extents(`ts`.`name`,`tsf`.`file_name`,`ts`.`engine`,`ts`.`se_private_data`) AS `FREE_EXTENTS`,internal_tablespace_total_extents(`ts`.`name`,`tsf`.`file_name`,`ts`.`engine`,`ts`.`se_private_data`) AS `TOTAL_EXTENTS`,internal_tablespace_extent_size(`ts`.`name`,`tsf`.`file_name`,`ts`.`engine`,`ts`.`se_private_data`) AS `EXTENT_SIZE`,internal_tablespace_initial_size(`ts`.`name`,`tsf`.`file_name`,`ts`.`engine`,`ts`.`se_private_data`) AS `INITIAL_SIZE`,internal_tablespace_maximum_size(`ts`.`name`,`tsf`.`file_name`,`ts`.`engine`,`ts`.`se_private_data`) AS `MAXIMUM_SIZE`,internal_tablespace_autoextend_size(`ts`.`name`,`tsf`.`file_name`,`ts`.`engine`,`ts`.`se_private_data`) AS `AUTOEXTEND_SIZE`,NULL AS `CREATION_TIME`,NULL AS `LAST_UPDATE_TIME`,NULL AS `LAST_ACCESS_TIME`,NULL AS `RECOVER_TIME`,NULL AS `TRANSACTION_COUNTER`,internal_tablespace_version(`ts`.`name`,`tsf`.`file_name`,`ts`.`engine`,`ts`.`se_private_data`) AS `VERSION`,internal_tablespace_row_format(`ts`.`name`,`tsf`.`file_name`,`ts`.`engine`,`ts`.`se_private_data`) AS `ROW_FORMAT`,NULL AS `TABLE_ROWS`,NULL AS `AVG_ROW_LENGTH`,NULL AS `DATA_LENGTH`,NULL AS `MAX_DATA_LENGTH`,NULL AS `INDEX_LENGTH`,internal_tablespace_data_free(`ts`.`name`,`tsf`.`file_name`,`ts`.`engine`,`ts`.`se_private_data`) AS `DATA_FREE`,NULL AS `CREATE_TIME`,NULL AS `UPDATE_TIME`,NULL AS `CHECK_TIME`,NULL AS `CHECKSUM`,internal_tablespace_status(`ts`.`name`,`tsf`.`file_name`,`ts`.`engine`,`ts`.`se_private_data`) AS `STATUS`,internal_tablespace_extra(`ts`.`name`,`tsf`.`file_name`,`ts`.`engine`,`ts`.`se_private_data`) AS `EXTRA` from (`mysql`.`tablespaces` `ts` join `mysql`.`tablespace_files` `tsf` on((`ts`.`id` = `tsf`.`tablespace_id`)));

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_BUFFER_PAGE 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_BUFFER_PAGE` (
  `POOL_ID` bigint unsigned NOT NULL DEFAULT '0',
  `BLOCK_ID` bigint unsigned NOT NULL DEFAULT '0',
  `SPACE` bigint unsigned NOT NULL DEFAULT '0',
  `PAGE_NUMBER` bigint unsigned NOT NULL DEFAULT '0',
  `PAGE_TYPE` varchar(64) DEFAULT NULL,
  `FLUSH_TYPE` bigint unsigned NOT NULL DEFAULT '0',
  `FIX_COUNT` bigint unsigned NOT NULL DEFAULT '0',
  `IS_HASHED` varchar(3) DEFAULT NULL,
  `NEWEST_MODIFICATION` bigint unsigned NOT NULL DEFAULT '0',
  `OLDEST_MODIFICATION` bigint unsigned NOT NULL DEFAULT '0',
  `ACCESS_TIME` bigint unsigned NOT NULL DEFAULT '0',
  `TABLE_NAME` varchar(1024) DEFAULT NULL,
  `INDEX_NAME` varchar(1024) DEFAULT NULL,
  `NUMBER_RECORDS` bigint unsigned NOT NULL DEFAULT '0',
  `DATA_SIZE` bigint unsigned NOT NULL DEFAULT '0',
  `COMPRESSED_SIZE` bigint unsigned NOT NULL DEFAULT '0',
  `PAGE_STATE` varchar(64) DEFAULT NULL,
  `IO_FIX` varchar(64) DEFAULT NULL,
  `IS_OLD` varchar(3) DEFAULT NULL,
  `FREE_PAGE_CLOCK` bigint unsigned NOT NULL DEFAULT '0',
  `IS_STALE` varchar(3) DEFAULT NULL
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_BUFFER_PAGE_LRU 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_BUFFER_PAGE_LRU` (
  `POOL_ID` bigint unsigned NOT NULL DEFAULT '0',
  `LRU_POSITION` bigint unsigned NOT NULL DEFAULT '0',
  `SPACE` bigint unsigned NOT NULL DEFAULT '0',
  `PAGE_NUMBER` bigint unsigned NOT NULL DEFAULT '0',
  `PAGE_TYPE` varchar(64) DEFAULT NULL,
  `FLUSH_TYPE` bigint unsigned NOT NULL DEFAULT '0',
  `FIX_COUNT` bigint unsigned NOT NULL DEFAULT '0',
  `IS_HASHED` varchar(3) DEFAULT NULL,
  `NEWEST_MODIFICATION` bigint unsigned NOT NULL DEFAULT '0',
  `OLDEST_MODIFICATION` bigint unsigned NOT NULL DEFAULT '0',
  `ACCESS_TIME` bigint unsigned NOT NULL DEFAULT '0',
  `TABLE_NAME` varchar(1024) DEFAULT NULL,
  `INDEX_NAME` varchar(1024) DEFAULT NULL,
  `NUMBER_RECORDS` bigint unsigned NOT NULL DEFAULT '0',
  `DATA_SIZE` bigint unsigned NOT NULL DEFAULT '0',
  `COMPRESSED_SIZE` bigint unsigned NOT NULL DEFAULT '0',
  `COMPRESSED` varchar(3) DEFAULT NULL,
  `IO_FIX` varchar(64) DEFAULT NULL,
  `IS_OLD` varchar(3) DEFAULT NULL,
  `FREE_PAGE_CLOCK` bigint unsigned NOT NULL DEFAULT '0'
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_BUFFER_POOL_STATS 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_BUFFER_POOL_STATS` (
  `POOL_ID` bigint unsigned NOT NULL DEFAULT '0',
  `POOL_SIZE` bigint unsigned NOT NULL DEFAULT '0',
  `FREE_BUFFERS` bigint unsigned NOT NULL DEFAULT '0',
  `DATABASE_PAGES` bigint unsigned NOT NULL DEFAULT '0',
  `OLD_DATABASE_PAGES` bigint unsigned NOT NULL DEFAULT '0',
  `MODIFIED_DATABASE_PAGES` bigint unsigned NOT NULL DEFAULT '0',
  `PENDING_DECOMPRESS` bigint unsigned NOT NULL DEFAULT '0',
  `PENDING_READS` bigint unsigned NOT NULL DEFAULT '0',
  `PENDING_FLUSH_LRU` bigint unsigned NOT NULL DEFAULT '0',
  `PENDING_FLUSH_LIST` bigint unsigned NOT NULL DEFAULT '0',
  `PAGES_MADE_YOUNG` bigint unsigned NOT NULL DEFAULT '0',
  `PAGES_NOT_MADE_YOUNG` bigint unsigned NOT NULL DEFAULT '0',
  `PAGES_MADE_YOUNG_RATE` double NOT NULL DEFAULT '0',
  `PAGES_MADE_NOT_YOUNG_RATE` double NOT NULL DEFAULT '0',
  `NUMBER_PAGES_READ` bigint unsigned NOT NULL DEFAULT '0',
  `NUMBER_PAGES_CREATED` bigint unsigned NOT NULL DEFAULT '0',
  `NUMBER_PAGES_WRITTEN` bigint unsigned NOT NULL DEFAULT '0',
  `PAGES_READ_RATE` double NOT NULL DEFAULT '0',
  `PAGES_CREATE_RATE` double NOT NULL DEFAULT '0',
  `PAGES_WRITTEN_RATE` double NOT NULL DEFAULT '0',
  `NUMBER_PAGES_GET` bigint unsigned NOT NULL DEFAULT '0',
  `HIT_RATE` bigint unsigned NOT NULL DEFAULT '0',
  `YOUNG_MAKE_PER_THOUSAND_GETS` bigint unsigned NOT NULL DEFAULT '0',
  `NOT_YOUNG_MAKE_PER_THOUSAND_GETS` bigint unsigned NOT NULL DEFAULT '0',
  `NUMBER_PAGES_READ_AHEAD` bigint unsigned NOT NULL DEFAULT '0',
  `NUMBER_READ_AHEAD_EVICTED` bigint unsigned NOT NULL DEFAULT '0',
  `READ_AHEAD_RATE` double NOT NULL DEFAULT '0',
  `READ_AHEAD_EVICTED_RATE` double NOT NULL DEFAULT '0',
  `LRU_IO_TOTAL` bigint unsigned NOT NULL DEFAULT '0',
  `LRU_IO_CURRENT` bigint unsigned NOT NULL DEFAULT '0',
  `UNCOMPRESS_TOTAL` bigint unsigned NOT NULL DEFAULT '0',
  `UNCOMPRESS_CURRENT` bigint unsigned NOT NULL DEFAULT '0'
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_CACHED_INDEXES 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_CACHED_INDEXES` (
  `SPACE_ID` int unsigned NOT NULL DEFAULT '0',
  `INDEX_ID` bigint unsigned NOT NULL DEFAULT '0',
  `N_CACHED_PAGES` bigint unsigned NOT NULL DEFAULT '0'
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_CMP 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_CMP` (
  `page_size` int NOT NULL DEFAULT '0',
  `compress_ops` int NOT NULL DEFAULT '0',
  `compress_ops_ok` int NOT NULL DEFAULT '0',
  `compress_time` int NOT NULL DEFAULT '0',
  `uncompress_ops` int NOT NULL DEFAULT '0',
  `uncompress_time` int NOT NULL DEFAULT '0'
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_CMPMEM 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_CMPMEM` (
  `page_size` int NOT NULL DEFAULT '0',
  `buffer_pool_instance` int NOT NULL DEFAULT '0',
  `pages_used` int NOT NULL DEFAULT '0',
  `pages_free` int NOT NULL DEFAULT '0',
  `relocation_ops` bigint NOT NULL DEFAULT '0',
  `relocation_time` int NOT NULL DEFAULT '0'
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_CMPMEM_RESET 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_CMPMEM_RESET` (
  `page_size` int NOT NULL DEFAULT '0',
  `buffer_pool_instance` int NOT NULL DEFAULT '0',
  `pages_used` int NOT NULL DEFAULT '0',
  `pages_free` int NOT NULL DEFAULT '0',
  `relocation_ops` bigint NOT NULL DEFAULT '0',
  `relocation_time` int NOT NULL DEFAULT '0'
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_CMP_PER_INDEX 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_CMP_PER_INDEX` (
  `database_name` varchar(192) NOT NULL DEFAULT '',
  `table_name` varchar(192) NOT NULL DEFAULT '',
  `index_name` varchar(192) NOT NULL DEFAULT '',
  `compress_ops` int NOT NULL DEFAULT '0',
  `compress_ops_ok` int NOT NULL DEFAULT '0',
  `compress_time` int NOT NULL DEFAULT '0',
  `uncompress_ops` int NOT NULL DEFAULT '0',
  `uncompress_time` int NOT NULL DEFAULT '0'
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_CMP_PER_INDEX_RESET 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_CMP_PER_INDEX_RESET` (
  `database_name` varchar(192) NOT NULL DEFAULT '',
  `table_name` varchar(192) NOT NULL DEFAULT '',
  `index_name` varchar(192) NOT NULL DEFAULT '',
  `compress_ops` int NOT NULL DEFAULT '0',
  `compress_ops_ok` int NOT NULL DEFAULT '0',
  `compress_time` int NOT NULL DEFAULT '0',
  `uncompress_ops` int NOT NULL DEFAULT '0',
  `uncompress_time` int NOT NULL DEFAULT '0'
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_CMP_RESET 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_CMP_RESET` (
  `page_size` int NOT NULL DEFAULT '0',
  `compress_ops` int NOT NULL DEFAULT '0',
  `compress_ops_ok` int NOT NULL DEFAULT '0',
  `compress_time` int NOT NULL DEFAULT '0',
  `uncompress_ops` int NOT NULL DEFAULT '0',
  `uncompress_time` int NOT NULL DEFAULT '0'
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_COLUMNS 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_COLUMNS` (
  `TABLE_ID` bigint unsigned NOT NULL DEFAULT '0',
  `NAME` varchar(193) NOT NULL DEFAULT '',
  `POS` bigint unsigned NOT NULL DEFAULT '0',
  `MTYPE` int NOT NULL DEFAULT '0',
  `PRTYPE` int NOT NULL DEFAULT '0',
  `LEN` int NOT NULL DEFAULT '0',
  `HAS_DEFAULT` int NOT NULL DEFAULT '0',
  `DEFAULT_VALUE` mediumblob
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_DATAFILES 结构
CREATIF NOT EXISTS E ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`INNODB_DATAFILES` AS select get_dd_tablespace_private_data(`ts`.`se_private_data`,'id') AS `SPACE`,`ts_files`.`file_name` AS `PATH` from (`mysql`.`tablespace_files` `ts_files` join `mysql`.`tablespaces` `ts` on((`ts`.`id` = `ts_files`.`tablespace_id`))) where ((`ts`.`se_private_data` is not null) and (`ts`.`engine` = 'InnoDB') and (`ts`.`name` <> 'mysql') and (`ts`.`name` <> 'innodb_temporary'));

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_FIELDS 结构
CREATIF NOT EXISTS E ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`INNODB_FIELDS` AS select get_dd_index_private_data(`idx`.`se_private_data`,'id') AS `INDEX_ID`,`col`.`name` AS `NAME`,(`fld`.`ordinal_position` - 1) AS `POS` from (((`mysql`.`index_column_usage` `fld` join `mysql`.`columns` `col` on((`fld`.`column_id` = `col`.`id`))) join `mysql`.`indexes` `idx` on((`fld`.`index_id` = `idx`.`id`))) join `mysql`.`tables` `tbl` on((`tbl`.`id` = `idx`.`table_id`))) where ((`tbl`.`type` <> 'VIEW') and (`tbl`.`hidden` = 'Visible') and (0 = `fld`.`hidden`) and (`tbl`.`se_private_id` is not null) and (`tbl`.`engine` = 'INNODB'));

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_FOREIGN 结构
CREATIF NOT EXISTS E ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`INNODB_FOREIGN` AS select (concat(`sch`.`name`,'/',`fk`.`name`) collate utf8mb3_tolower_ci) AS `ID`,concat(`sch`.`name`,'/',`tbl`.`name`) AS `FOR_NAME`,concat(`fk`.`referenced_table_schema`,'/',`fk`.`referenced_table_name`) AS `REF_NAME`,count(0) AS `N_COLS`,(((((if((`fk`.`delete_rule` = 'CASCADE'),1,0) | if((`fk`.`delete_rule` = 'SET NULL'),2,0)) | if((`fk`.`update_rule` = 'CASCADE'),4,0)) | if((`fk`.`update_rule` = 'SET NULL'),8,0)) | if((`fk`.`delete_rule` = 'NO ACTION'),16,0)) | if((`fk`.`update_rule` = 'NO ACTION'),32,0)) AS `TYPE` from (((`mysql`.`foreign_keys` `fk` join `mysql`.`tables` `tbl` on((`fk`.`table_id` = `tbl`.`id`))) join `mysql`.`schemata` `sch` on((`fk`.`schema_id` = `sch`.`id`))) join `mysql`.`foreign_key_column_usage` `col` on((`fk`.`id` = `col`.`foreign_key_id`))) where ((`tbl`.`type` <> 'VIEW') and (`tbl`.`hidden` = 'Visible') and (`tbl`.`se_private_id` is not null) and (`tbl`.`engine` = 'INNODB')) group by `fk`.`id`;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_FOREIGN_COLS 结构
CREATIF NOT EXISTS E ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`INNODB_FOREIGN_COLS` AS select (concat(`sch`.`name`,'/',`fk`.`name`) collate utf8mb3_tolower_ci) AS `ID`,`col`.`name` AS `FOR_COL_NAME`,`fk_col`.`referenced_column_name` AS `REF_COL_NAME`,`fk_col`.`ordinal_position` AS `POS` from ((((`mysql`.`foreign_key_column_usage` `fk_col` join `mysql`.`foreign_keys` `fk` on((`fk`.`id` = `fk_col`.`foreign_key_id`))) join `mysql`.`tables` `tbl` on((`fk`.`table_id` = `tbl`.`id`))) join `mysql`.`schemata` `sch` on((`fk`.`schema_id` = `sch`.`id`))) join `mysql`.`columns` `col` on(((`tbl`.`id` = `col`.`table_id`) and (`fk_col`.`column_id` = `col`.`id`)))) where ((`tbl`.`type` <> 'VIEW') and (`tbl`.`hidden` = 'Visible') and (`tbl`.`se_private_id` is not null) and (`tbl`.`engine` = 'INNODB'));

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_FT_BEING_DELETED 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_FT_BEING_DELETED` (
  `DOC_ID` bigint unsigned NOT NULL DEFAULT '0'
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_FT_CONFIG 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_FT_CONFIG` (
  `KEY` varchar(193) NOT NULL DEFAULT '',
  `VALUE` varchar(193) NOT NULL DEFAULT ''
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_FT_DEFAULT_STOPWORD 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_FT_DEFAULT_STOPWORD` (
  `value` varchar(18) NOT NULL DEFAULT ''
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_FT_DELETED 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_FT_DELETED` (
  `DOC_ID` bigint unsigned NOT NULL DEFAULT '0'
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_FT_INDEX_CACHE 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_FT_INDEX_CACHE` (
  `WORD` varchar(337) NOT NULL DEFAULT '',
  `FIRST_DOC_ID` bigint unsigned NOT NULL DEFAULT '0',
  `LAST_DOC_ID` bigint unsigned NOT NULL DEFAULT '0',
  `DOC_COUNT` bigint unsigned NOT NULL DEFAULT '0',
  `DOC_ID` bigint unsigned NOT NULL DEFAULT '0',
  `POSITION` bigint unsigned NOT NULL DEFAULT '0'
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_FT_INDEX_TABLE 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_FT_INDEX_TABLE` (
  `WORD` varchar(337) NOT NULL DEFAULT '',
  `FIRST_DOC_ID` bigint unsigned NOT NULL DEFAULT '0',
  `LAST_DOC_ID` bigint unsigned NOT NULL DEFAULT '0',
  `DOC_COUNT` bigint unsigned NOT NULL DEFAULT '0',
  `DOC_ID` bigint unsigned NOT NULL DEFAULT '0',
  `POSITION` bigint unsigned NOT NULL DEFAULT '0'
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_INDEXES 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_INDEXES` (
  `INDEX_ID` bigint unsigned NOT NULL DEFAULT '0',
  `NAME` varchar(193) NOT NULL DEFAULT '',
  `TABLE_ID` bigint unsigned NOT NULL DEFAULT '0',
  `TYPE` int NOT NULL DEFAULT '0',
  `N_FIELDS` int NOT NULL DEFAULT '0',
  `PAGE_NO` int NOT NULL DEFAULT '0',
  `SPACE` int NOT NULL DEFAULT '0',
  `MERGE_THRESHOLD` int NOT NULL DEFAULT '0'
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_METRICS 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_METRICS` (
  `NAME` varchar(193) NOT NULL DEFAULT '',
  `SUBSYSTEM` varchar(193) NOT NULL DEFAULT '',
  `COUNT` bigint NOT NULL DEFAULT '0',
  `MAX_COUNT` bigint DEFAULT NULL,
  `MIN_COUNT` bigint DEFAULT NULL,
  `AVG_COUNT` double DEFAULT NULL,
  `COUNT_RESET` bigint NOT NULL DEFAULT '0',
  `MAX_COUNT_RESET` bigint DEFAULT NULL,
  `MIN_COUNT_RESET` bigint DEFAULT NULL,
  `AVG_COUNT_RESET` double DEFAULT NULL,
  `TIME_ENABLED` datetime DEFAULT NULL,
  `TIME_DISABLED` datetime DEFAULT NULL,
  `TIME_ELAPSED` bigint DEFAULT NULL,
  `TIME_RESET` datetime DEFAULT NULL,
  `STATUS` varchar(193) NOT NULL DEFAULT '',
  `TYPE` varchar(193) NOT NULL DEFAULT '',
  `COMMENT` varchar(193) NOT NULL DEFAULT ''
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_SESSION_TEMP_TABLESPACES 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_SESSION_TEMP_TABLESPACES` (
  `ID` int unsigned NOT NULL DEFAULT '0',
  `SPACE` int unsigned NOT NULL DEFAULT '0',
  `PATH` varchar(4001) NOT NULL DEFAULT '',
  `SIZE` bigint unsigned NOT NULL DEFAULT '0',
  `STATE` varchar(192) NOT NULL DEFAULT '',
  `PURPOSE` varchar(192) NOT NULL DEFAULT ''
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_TABLES 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_TABLES` (
  `TABLE_ID` bigint unsigned NOT NULL DEFAULT '0',
  `NAME` varchar(655) NOT NULL DEFAULT '',
  `FLAG` int NOT NULL DEFAULT '0',
  `N_COLS` int NOT NULL DEFAULT '0',
  `SPACE` bigint NOT NULL DEFAULT '0',
  `ROW_FORMAT` varchar(12) DEFAULT NULL,
  `ZIP_PAGE_SIZE` int unsigned NOT NULL DEFAULT '0',
  `SPACE_TYPE` varchar(10) DEFAULT NULL,
  `INSTANT_COLS` int NOT NULL DEFAULT '0',
  `TOTAL_ROW_VERSIONS` int NOT NULL DEFAULT '0'
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_TABLESPACES 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_TABLESPACES` (
  `SPACE` int unsigned NOT NULL DEFAULT '0',
  `NAME` varchar(655) NOT NULL DEFAULT '',
  `FLAG` int unsigned NOT NULL DEFAULT '0',
  `ROW_FORMAT` varchar(22) DEFAULT NULL,
  `PAGE_SIZE` int unsigned NOT NULL DEFAULT '0',
  `ZIP_PAGE_SIZE` int unsigned NOT NULL DEFAULT '0',
  `SPACE_TYPE` varchar(10) DEFAULT NULL,
  `FS_BLOCK_SIZE` int unsigned NOT NULL DEFAULT '0',
  `FILE_SIZE` bigint unsigned NOT NULL DEFAULT '0',
  `ALLOCATED_SIZE` bigint unsigned NOT NULL DEFAULT '0',
  `AUTOEXTEND_SIZE` bigint unsigned NOT NULL DEFAULT '0',
  `SERVER_VERSION` varchar(10) DEFAULT NULL,
  `SPACE_VERSION` int unsigned NOT NULL DEFAULT '0',
  `ENCRYPTION` varchar(1) DEFAULT NULL,
  `STATE` varchar(10) DEFAULT NULL
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_TABLESPACES_BRIEF 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`INNODB_TABLESIF NOT EXISTS PACES_BRIEF` AS select get_dd_tablespace_private_data(`ts`.`se_private_data`,'id') AS `SPACE`,`ts`.`name` AS `NAME`,`ts_files`.`file_name` AS `PATH`,get_dd_tablespace_private_data(`ts`.`se_private_data`,'flags') AS `FLAG`,if((get_dd_tablespace_private_data(`ts`.`se_private_data`,'id') = 0),'System',if((((get_dd_tablespace_private_data(`ts`.`se_private_data`,'flags') & 2048) >> 11) <> 0),'General','Single')) AS `SPACE_TYPE` from (`mysql`.`tablespace_files` `ts_files` join `mysql`.`tablespaces` `ts` on((`ts`.`id` = `ts_files`.`tablespace_id`))) where ((`ts`.`se_private_data` is not null) and (`ts`.`engine` = 'InnoDB') and (`ts`.`name` <> 'mysql') and (`ts`.`name` <> 'innodb_temporary'));

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_TABLESTATS 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_TABLESTATS` (
  `TABLE_ID` bigint unsigned NOT NULL DEFAULT '0',
  `NAME` varchar(193) NOT NULL DEFAULT '',
  `STATS_INITIALIZED` varchar(193) NOT NULL DEFAULT '',
  `NUM_ROWS` bigint unsigned NOT NULL DEFAULT '0',
  `CLUST_INDEX_SIZE` bigint unsigned NOT NULL DEFAULT '0',
  `OTHER_INDEX_SIZE` bigint unsigned NOT NULL DEFAULT '0',
  `MODIFIED_COUNTER` bigint unsigned NOT NULL DEFAULT '0',
  `AUTOINC` bigint unsigned NOT NULL DEFAULT '0',
  `REF_COUNT` int NOT NULL DEFAULT '0'
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_TEMP_TABLE_INFO 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_TEMP_TABLE_INFO` (
  `TABLE_ID` bigint unsigned NOT NULL DEFAULT '0',
  `NAME` varchar(64) DEFAULT NULL,
  `N_COLS` int unsigned NOT NULL DEFAULT '0',
  `SPACE` int unsigned NOT NULL DEFAULT '0'
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_TRX 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_TRX` (
  `trx_id` bigint unsigned NOT NULL DEFAULT '0',
  `trx_state` varchar(13) NOT NULL DEFAULT '',
  `trx_started` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `trx_requested_lock_id` varchar(126) DEFAULT NULL,
  `trx_wait_started` datetime DEFAULT NULL,
  `trx_weight` bigint unsigned NOT NULL DEFAULT '0',
  `trx_mysql_thread_id` bigint unsigned NOT NULL DEFAULT '0',
  `trx_query` varchar(1024) DEFAULT NULL,
  `trx_operation_state` varchar(64) DEFAULT NULL,
  `trx_tables_in_use` bigint unsigned NOT NULL DEFAULT '0',
  `trx_tables_locked` bigint unsigned NOT NULL DEFAULT '0',
  `trx_lock_structs` bigint unsigned NOT NULL DEFAULT '0',
  `trx_lock_memory_bytes` bigint unsigned NOT NULL DEFAULT '0',
  `trx_rows_locked` bigint unsigned NOT NULL DEFAULT '0',
  `trx_rows_modified` bigint unsigned NOT NULL DEFAULT '0',
  `trx_concurrency_tickets` bigint unsigned NOT NULL DEFAULT '0',
  `trx_isolation_level` varchar(16) NOT NULL DEFAULT '',
  `trx_unique_checks` int NOT NULL DEFAULT '0',
  `trx_foreign_key_checks` int NOT NULL DEFAULT '0',
  `trx_last_foreign_key_error` varchar(256) DEFAULT NULL,
  `trx_adaptive_hash_latched` int NOT NULL DEFAULT '0',
  `trx_adaptive_hash_timeout` bigint unsigned NOT NULL DEFAULT '0',
  `trx_is_read_only` int NOT NULL DEFAULT '0',
  `trx_autocommit_non_locking` int NOT NULL DEFAULT '0',
  `trx_schedule_weight` bigint unsigned DEFAULT NULL
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.INNODB_VIRTUAL 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `INNODB_VIRTUAL` (
  `TABLE_ID` bigint unsigned NOT NULL DEFAULT '0',
  `POS` int unsigned NOT NULL DEFAULT '0',
  `BASE_POS` int unsigned NOT NULL DEFAULT '0'
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.KEYWORDS 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`KEYWORDS` AS select `j`.`word` AS `WORD`,`j`.`reserved` AS `RESERVED` from json_table('[["ACCESSIBLE",1],["ACCOUNT",0],["ACTION",0],["ACTIVE",0],["ADD",1],["ADMIN",0],["AFTER",0],["AGAINST",0],["AGGREGATE",0],["ALGORITHM",0],["ALL",1],["ALTER",1],["ALWAYS",0],["ANALYZE",1],["AND",1],["ANY",0],["ARRAY",0],["AS",1],["ASC",1],["ASCII",0],["ASENSITIVE",1],["ASSIGN_GTIDS_TO_ANONYMOUS_TRANSACTIONS",0],["AT",0],["ATTRIBUTE",0],["AUTHENTICATION",0],["AUTOEXTEND_SIZE",0],["AUTO_INCREMENT",0],["AVG",0],["AVG_ROW_LENGTH",0],["BACKUP",0],["BEFORE",1],["BEGIN",0],["BETWEEN",1],["BIGINT",1],["BINARY",1],["BINLOG",0],["BIT",0],["BLOB",1],["BLOCK",0],["BOOL",0],["BOOLEAN",0],["BOTH",1],["BTREE",0],["BUCKETS",0],["BULK",0],["BY",1],["BYTE",0],["CACHE",0],["CALL",1],["CASCADE",1],["CASCADED",0],["CASE",1],["CATALOG_NAME",0],["CHAIN",0],["CHALLENGE_RESPONSE",0],["CHANGE",1],["CHANGED",0],["CHANNEL",0],["CHAR",1],["CHARACTER",1],["CHARSET",0],["CHECK",1],["CHECKSUM",0],["CIPHER",0],["CLASS_ORIGIN",0],["CLIENT",0],["CLONE",0],["CLOSE",0],["COALESCE",0],["CODE",0],["COLLATE",1],["COLLATION",0],["COLUMN",1],["COLUMNS",0],["COLUMN_FORMAT",0],["COLUMN_NAME",0],["COMMENT",0],["COMMIT",0],["COMMITTED",0],["COMPACT",0],["COMPLETION",0],["COMPONENT",0],["COMPRESSED",0],["COMPRESSION",0],["CONCURRENT",0],["CONDITION",1],["CONNECTION",0],["CONSISTENT",0],["CONSTRAINT",1],["CONSTRAINT_CATALOG",0],["CONSTRAINT_NAME",0],["CONSTRAINT_SCHEMA",0],["CONTAINS",0],["CONTEXT",0],["CONTINUE",1],["CONVERT",1],["CPU",0],["CREATE",1],["CROSS",1],["CUBE",1],["CUME_DIST",1],["CURRENT",0],["CURRENT_DATE",1],["CURRENT_TIME",1],["CURRENT_TIMESTAMP",1],["CURRENT_USER",1],["CURSOR",1],["CURSOR_NAME",0],["DATA",0],["DATABASE",1],["DATABASES",1],["DATAFILE",0],["DATE",0],["DATETIME",0],["DAY",0],["DAY_HOUR",1],["DAY_MICROSECOND",1],["DAY_MINUTE",1],["DAY_SECOND",1],["DEALLOCATE",0],["DEC",1],["DECIMAL",1],["DECLARE",1],["DEFAULT",1],["DEFAULT_AUTH",0],["DEFINER",0],["DEFINITION",0],["DELAYED",1],["DELAY_KEY_WRITE",0],["DELETE",1],["DENSE_RANK",1],["DESC",1],["DESCRIBE",1],["DESCRIPTION",0],["DETERMINISTIC",1],["DIAGNOSTICS",0],["DIRECTORY",0],["DISABLE",0],["DISCARD",0],["DISK",0],["DISTINCT",1],["DISTINCTROW",1],["DIV",1],["DO",0],["DOUBLE",1],["DROP",1],["DUAL",1],["DUMPFILE",0],["DUPLICATE",0],["DYNAMIC",0],["EACH",1],["ELSE",1],["ELSEIF",1],["EMPTY",1],["ENABLE",0],["ENCLOSED",1],["ENCRYPTION",0],["END",0],["ENDS",0],["ENFORCED",0],["ENGINE",0],["ENGINES",0],["ENGINE_ATTRIBUTE",0],["ENUM",0],["ERROR",0],["ERRORS",0],["ESCAPE",0],["ESCAPED",1],["EVENT",0],["EVENTS",0],["EVERY",0],["EXCEPT",1],["EXCHANGE",0],["EXCLUDE",0],["EXECUTE",0],["EXISTS",1],["EXIT",1],["EXPANSION",0],["EXPIRE",0],["EXPLAIN",1],["EXPORT",0],["EXTENDED",0],["EXTENT_SIZE",0],["FACTOR",0],["FAILED_LOGIN_ATTEMPTS",0],["FALSE",1],["FAST",0],["FAULTS",0],["FETCH",1],["FIELDS",0],["FILE",0],["FILE_BLOCK_SIZE",0],["FILTER",0],["FINISH",0],["FIRST",0],["FIRST_VALUE",1],["FIXED",0],["FLOAT",1],["FLOAT4",1],["FLOAT8",1],["FLUSH",0],["FOLLOWING",0],["FOLLOWS",0],["FOR",1],["FORCE",1],["FOREIGN",1],["FORMAT",0],["FOUND",0],["FROM",1],["FULL",0],["FULLTEXT",1],["FUNCTION",1],["GENERAL",0],["GENERATE",0],["GENERATED",1],["GEOMCOLLECTION",0],["GEOMETRY",0],["GEOMETRYCOLLECTION",0],["GET",1],["GET_FORMAT",0],["GET_MASTER_PUBLIC_KEY",0],["GET_SOURCE_PUBLIC_KEY",0],["GLOBAL",0],["GRANT",1],["GRANTS",0],["GROUP",1],["GROUPING",1],["GROUPS",1],["GROUP_REPLICATION",0],["GTID_ONLY",0],["HANDLER",0],["HASH",0],["HAVING",1],["HELP",0],["HIGH_PRIORITY",1],["HISTOGRAM",0],["HISTORY",0],["HOST",0],["HOSTS",0],["HOUR",0],["HOUR_MICROSECOND",1],["HOUR_MINUTE",1],["HOUR_SECOND",1],["IDENTIFIED",0],["IF",1],["IGNORE",1],["IGNORE_SERVER_IDS",0],["IMPORT",0],["IN",1],["INACTIVE",0],["INDEX",1],["INDEXES",0],["INFILE",1],["INITIAL",0],["INITIAL_SIZE",0],["INITIATE",0],["INNER",1],["INOUT",1],["INSENSITIVE",1],["INSERT",1],["INSERT_METHOD",0],["INSTALL",0],["INSTANCE",0],["INT",1],["INT1",1],["INT2",1],["INT3",1],["INT4",1],["INT8",1],["INTEGER",1],["INTERSECT",1],["INTERVAL",1],["INTO",1],["INVISIBLE",0],["INVOKER",0],["IO",0],["IO_AFTER_GTIDS",1],["IO_BEFORE_GTIDS",1],["IO_THREAD",0],["IPC",0],["IS",1],["ISOLATION",0],["ISSUER",0],["ITERATE",1],["JOIN",1],["JSON",0],["JSON_TABLE"IF NOT EXISTS ,1],["JSON_VALUE",0],["KEY",1],["KEYRING",0],["KEYS",1],["KEY_BLOCK_SIZE",0],["KILL",1],["LAG",1],["LANGUAGE",0],["LAST",0],["LAST_VALUE",1],["LATERAL",1],["LEAD",1],["LEADING",1],["LEAVE",1],["LEAVES",0],["LEFT",1],["LESS",0],["LEVEL",0],["LIKE",1],["LIMIT",1],["LINEAR",1],["LINES",1],["LINESTRING",0],["LIST",0],["LOAD",1],["LOCAL",0],["LOCALTIME",1],["LOCALTIMESTAMP",1],["LOCK",1],["LOCKED",0],["LOCKS",0],["LOGFILE",0],["LOGS",0],["LONG",1],["LONGBLOB",1],["LONGTEXT",1],["LOOP",1],["LOW_PRIORITY",1],["MASTER",0],["MASTER_AUTO_POSITION",0],["MASTER_BIND",1],["MASTER_COMPRESSION_ALGORITHMS",0],["MASTER_CONNECT_RETRY",0],["MASTER_DELAY",0],["MASTER_HEARTBEAT_PERIOD",0],["MASTER_HOST",0],["MASTER_LOG_FILE",0],["MASTER_LOG_POS",0],["MASTER_PASSWORD",0],["MASTER_PORT",0],["MASTER_PUBLIC_KEY_PATH",0],["MASTER_RETRY_COUNT",0],["MASTER_SSL",0],["MASTER_SSL_CA",0],["MASTER_SSL_CAPATH",0],["MASTER_SSL_CERT",0],["MASTER_SSL_CIPHER",0],["MASTER_SSL_CRL",0],["MASTER_SSL_CRLPATH",0],["MASTER_SSL_KEY",0],["MASTER_SSL_VERIFY_SERVER_CERT",1],["MASTER_TLS_CIPHERSUITES",0],["MASTER_TLS_VERSION",0],["MASTER_USER",0],["MASTER_ZSTD_COMPRESSION_LEVEL",0],["MATCH",1],["MAXVALUE",1],["MAX_CONNECTIONS_PER_HOUR",0],["MAX_QUERIES_PER_HOUR",0],["MAX_ROWS",0],["MAX_SIZE",0],["MAX_UPDATES_PER_HOUR",0],["MAX_USER_CONNECTIONS",0],["MEDIUM",0],["MEDIUMBLOB",1],["MEDIUMINT",1],["MEDIUMTEXT",1],["MEMBER",0],["MEMORY",0],["MERGE",0],["MESSAGE_TEXT",0],["MICROSECOND",0],["MIDDLEINT",1],["MIGRATE",0],["MINUTE",0],["MINUTE_MICROSECOND",1],["MINUTE_SECOND",1],["MIN_ROWS",0],["MOD",1],["MODE",0],["MODIFIES",1],["MODIFY",0],["MONTH",0],["MULTILINESTRING",0],["MULTIPOINT",0],["MULTIPOLYGON",0],["MUTEX",0],["MYSQL_ERRNO",0],["NAME",0],["NAMES",0],["NATIONAL",0],["NATURAL",1],["NCHAR",0],["NDB",0],["NDBCLUSTER",0],["NESTED",0],["NETWORK_NAMESPACE",0],["NEVER",0],["NEW",0],["NEXT",0],["NO",0],["NODEGROUP",0],["NONE",0],["NOT",1],["NOWAIT",0],["NO_WAIT",0],["NO_WRITE_TO_BINLOG",1],["NTH_VALUE",1],["NTILE",1],["NULL",1],["NULLS",0],["NUMBER",0],["NUMERIC",1],["NVARCHAR",0],["OF",1],["OFF",0],["OFFSET",0],["OJ",0],["OLD",0],["ON",1],["ONE",0],["ONLY",0],["OPEN",0],["OPTIMIZE",1],["OPTIMIZER_COSTS",1],["OPTION",1],["OPTIONAL",0],["OPTIONALLY",1],["OPTIONS",0],["OR",1],["ORDER",1],["ORDINALITY",0],["ORGANIZATION",0],["OTHERS",0],["OUT",1],["OUTER",1],["OUTFILE",1],["OVER",1],["OWNER",0],["PACK_KEYS",0],["PAGE",0],["PARSER",0],["PARTIAL",0],["PARTITION",1],["PARTITIONING",0],["PARTITIONS",0],["PASSWORD",0],["PASSWORD_LOCK_TIME",0],["PATH",0],["PERCENT_RANK",1],["PERSIST",0],["PERSIST_ONLY",0],["PHASE",0],["PLUGIN",0],["PLUGINS",0],["PLUGIN_DIR",0],["POINT",0],["POLYGON",0],["PORT",0],["PRECEDES",0],["PRECEDING",0],["PRECISION",1],["PREPARE",0],["PRESERVE",0],["PREV",0],["PRIMARY",1],["PRIVILEGES",0],["PRIVILEGE_CHECKS_USER",0],["PROCEDURE",1],["PROCESS",0],["PROCESSLIST",0],["PROFILE",0],["PROFILES",0],["PROXY",0],["PURGE",1],["QUARTER",0],["QUERY",0],["QUICK",0],["RANDOM",0],["RANGE",1],["RANK",1],["READ",1],["READS",1],["READ_ONLY",0],["READ_WRITE",1],["REAL",1],["REBUILD",0],["RECOVER",0],["RECURSIVE",1],["REDO_BUFFER_SIZE",0],["REDUNDANT",0],["REFERENCE",0],["REFERENCES",1],["REGEXP",1],["REGISTRATION",0],["RELAY",0],["RELAYLOG",0],["RELAY_LOG_FILE",0],["RELAY_LOG_POS",0],["RELAY_THREAD",0],["RELEASE",1],["RELOAD",0],["REMOVE",0],["RENAME",1],["REORGANIZE",0],["REPAIR",0],["REPEAT",1],["REPEATABLE",0],["REPLACE",1],["REPLICA",0],["REPLICAS",0],["REPLICATE_DO_DB",0],["REPLICATE_DO_TABLE",0],["REPLICATE_IGNORE_DB",0],["REPLICATE_IGNORE_TABLE",0],["REPLICATE_REWRITE_DB",0],["REPLICATE_WILD_DO_TABLE",0],["REPLICATE_WILD_IGNORE_TABLE",0],["REPLICATION",0],["REQUIRE",1],["REQUIRE_ROW_FORMAT",0],["REQUIRE_TABLE_PRIMARY_KEY_CHECK",0],["RESET",0],["RESIGNAL",1],["RESOURCE",0],["RESPECT",0],["RESTART",0],["RESTORE",0],["RESTRICT",1],["RESUME",0],["RETAIN",0],["RETURN",1],["RETURNED_SQLSTATE",0],["RETURNING",0],["RETURNS",0],["REUSE",0],["REVERSE",0],["REVOKE",1],["RIGHT",1],["RLIKE",1],["ROLE",0],["ROLLBACK",0],["ROLLUP",0],["ROTATE",0],["ROUTINE",0],["ROW",1],["ROWS",1],["ROW_COUNT",0],["ROW_FORMAT",0],["ROW_NUMBER",1],["RTREE",0],["SAVEPOINT",0],["SCHEDULE",0],["SCHEMA",1],["SCHEMAS",1],["SCHEMA_NAME",0],["SECOND",0],["SECONDARY",0],["SECONDARY_ENGINE",0],["SECONDARY_ENGINE_ATTRIBUTE",0],["SECONDARY_LOAD",0],["SECONDARY_UNLOAD",0],["SECOND_MICROSECOND",1],["SECURITY",0],["SELECT",1],["SENSITIVE",1],["SEPARATOR",1],["SERIAL",0],["SERIALIZABLE",0],["SERVER",0],["SESSION",0],["SET",1],["SHARE",0],["SHOW",1],["SHUTDOWN",0],["SIGNAL",1],["SIGNED",0],["SIMPLE",0],["SKIP",0],["SLAVE",0],["SLOW",0],["SMALLINT",1],["SNAPSHOT",0],["SOCKET",0],["SOME",0],["SONAME",0],["SOUNDS",0],["SOURCE",0],["SOURCE_AUTO_POSITION",0],["SOURCE_BIND",0],["SOURCE_COMPRESSION_ALGORITHMS",0],["SOURCE_CONNECTION_AUTO_FAILOVER",0],["SOURCE_CONNECT_RETRY",0],["SOURCE_DELAY",0],["SOURCE_HEARTBEAT_PERIOD",0],["SOURCE_HOST",0],["SOURCE_LOG_FILE",0],["SOURCE_LOG_POS",0],["SOURCE_PASSWORD",0],["SOURCE_PORT",0],["SOURCE_PUBLIC_KEY_PATH",0],["SOURCE_RETRY_COUNT",0],["SOURCE_SSL",0],["SOURCE_SSL_CA",0],["SOURCE_SSL_CAPATH",0],["SOURCE_SSL_CERT",0],["SOURCE_SSL_CIPHER",0],["SOURCE_SSL_CRL",0],["SOURCE_SSL_CRLPATH",0],["SOURCE_SSL_KEY",0],["SOURCE_SSL_VERIFY_SERVER_CERT",0],["SOURCE_TLS_CIPHERSUITES",0],["SOURCE_TLS_VERSION",0],["SOURCE_USER",0],["SOURCE_ZSTD_COMPRESSION_LEVEL",0],["SPATIAL",1],["SPECIFIC",1],["SQL",1],["SQLEXCEPTION",1],["SQLSTATE",1],["SQLWARNING",1],["SQL_AFTER_GTIDS",0],["SQL_AFTER_MTS_GAPS",0],["SQL_BEFORE_GTIDS",0],["SQL_BIG_RESULT",1],["SQL_BUFFER_RESULT",0],["SQL_CALC_FOUND_ROWS",1],["SQL_NO_CACHE",0],["SQL_SMALL_RESULT",1],["SQL_THREAD",0],["SQL_TSI_DAY",0],["SQL_TSI_HOUR",0],["SQL_TSI_MINUTE",0],["SQL_TSI_MONTH",0],["SQL_TSI_QUARTER",0],["SQL_TSI_SECOND",0],["SQL_TSI_WEEK",0],["SQL_TSI_YEAR",0],["SRID",0],["SSL",1],["STACKED",0],["START",0],["STARTING",1],["STARTS",0],["STATS_AUTO_RECALC",0],["STATS_PERSISTENT",0],["STATS_SAMPLE_PAGES",0],["STATUS",0],["STOP",0],["STORAGE",0],["STORED",1],["STRAIGHT_JOIN",1],["STREAM",0],["STRING",0],["SUBCLASS_ORIGIN",0],["SUBJECT",0],["SUBPARTITION",0],["SUBPARTITIONS",0],["SUPER",0],["SUSPEND",0],["SWAPS",0],["SWITCHES",0],["SYSTEM",1],["TABLE",1],["TABLES",0],["TABLESPACE",0],["TABLE_CHECKSUM",0],["TABLE_NAME",0],["TEMPORARY",0],["TEMPTABLE",0],["TERMINATED",1],["TEXT",0],["THAN",0],["THEN",1],["THREAD_PRIORITY",0],["TIES",0],["TIME",0],["TIMESTAMP",0],["TIMESTAMPADD",0],["TIMESTAMPDIFF",0],["TINYBLOB",1],["TINYINT",1],["TINYTEXT",1],["TLS",0],["TO",1],["TRAILING",1],["TRANSACTION",0],["TRIGGER",1],["TRIGGERS",0],["TRUE",1],["TRUNCATE",0],["TYPE",0],["TYPES",0],["UNBOUNDED",0],["UNCOMMITTED",0],["UNDEFINED",0],["UNDO",1],["UNDOFILE",0],["UNDO_BUFFER_SIZE",0],["UNICODE",0],["UNINSTALL",0],["UNION",1],["UNIQUE",1],["UNKNOWN",0],["UNLOCK",1],["UNREGISTER",0],["UNSIGNED",1],["UNTIL",0],["UPDATE",1],["UPGRADE",0],["URL",0],["USAGE",1],["USE",1],["USER",0],["USER_RESOURCES",0],["USE_FRM",0],["USING",1],["UTC_DATE",1],["UTC_TIME",1],["UTC_TIMESTAMP",1],["VALIDATION",0],["VALUE",0],["VALUES",1],["VARBINARY",1],["VARCHAR",1],["VARCHARACTER",1],["VARIABLES",0],["VARYING",1],["VCPU",0],["VIEW",0],["VIRTUAL",1],["VISIBLE",0],["WAIT",0],["WARNINGS",0],["WEEK",0],["WEIGHT_STRING",0],["WHEN",1],["WHERE",1],["WHILE",1],["WINDOW",1],["WITH",1],["WITHOUT",0],["WORK",0],["WRAPPER",0],["WRITE",1],["X509",0],["XA",0],["XID",0],["XML",0],["XOR",1],["YEAR",0],["YEAR_MONTH",1],["ZEROFILL",1],["ZONE",0]]', '$[*]' columns (`word` varchar(128) character set utf8mb4 path '$[0]', `reserved` int path '$[1]')) `j`;

-- 数据导出被取消选择。

-- 导出  表 information_schema.KEY_COLUMN_USAGE 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`KEY_COLUMN_USAGE` AS select (`cat`.`name` collate utf8mb3_tolower_ci) AS `CONSTRAINT_CATALOG`,(`sch`.`name` collate utf8mb3_tolower_ci) AS `CONSTRAINT_SCHEMA`,`constraints`.`CONSTRAINT_NAME` AS `CONSTRAINT_NAME`,(`cat`.`name` collate utf8mb3_tolower_ci) AS `TABLE_IF NOT EXISTS CATALOG`,(`sch`.`name` collate utf8mb3_tolower_ci) AS `TABLE_SCHEMA`,(`tbl`.`name` collate utf8mb3_tolower_ci) AS `TABLE_NAME`,(`col`.`name` collate utf8mb3_tolower_ci) AS `COLUMN_NAME`,`constraints`.`ORDINAL_POSITION` AS `ORDINAL_POSITION`,`constraints`.`POSITION_IN_UNIQUE_CONSTRAINT` AS `POSITION_IN_UNIQUE_CONSTRAINT`,`constraints`.`REFERENCED_TABLE_SCHEMA` AS `REFERENCED_TABLE_SCHEMA`,`constraints`.`REFERENCED_TABLE_NAME` AS `REFERENCED_TABLE_NAME`,`constraints`.`REFERENCED_COLUMN_NAME` AS `REFERENCED_COLUMN_NAME` from (((`mysql`.`tables` `tbl` join `mysql`.`schemata` `sch` on((`tbl`.`schema_id` = `sch`.`id`))) join `mysql`.`catalogs` `cat` on((`cat`.`id` = `sch`.`catalog_id`))) join (lateral (select `idx`.`name` AS `CONSTRAINT_NAME`,`icu`.`ordinal_position` AS `ORDINAL_POSITION`,NULL AS `POSITION_IN_UNIQUE_CONSTRAINT`,NULL AS `REFERENCED_TABLE_SCHEMA`,NULL AS `REFERENCED_TABLE_NAME`,NULL AS `REFERENCED_COLUMN_NAME`,`icu`.`column_id` AS `column_id`,((0 <> `idx`.`hidden`) or (0 <> `icu`.`hidden`)) AS `HIDDEN` from (`mysql`.`indexes` `idx` join `mysql`.`index_column_usage` `icu` on((`icu`.`index_id` = `idx`.`id`))) where ((`idx`.`table_id` = `tbl`.`id`) and (`idx`.`type` in ('PRIMARY','UNIQUE'))) union all select (`fk`.`name` collate utf8mb3_tolower_ci) AS `CONSTRAINT_NAME`,`fkcu`.`ordinal_position` AS `ORDINAL_POSITION`,`fkcu`.`ordinal_position` AS `POSITION_IN_UNIQUE_CONSTRAINT`,`fk`.`referenced_table_schema` AS `REFERENCED_TABLE_SCHEMA`,`fk`.`referenced_table_name` AS `REFERENCED_TABLE_NAME`,`fkcu`.`referenced_column_name` AS `REFERENCED_COLUMN_NAME`,`fkcu`.`column_id` AS `column_id`,false AS `HIDDEN` from (`mysql`.`foreign_keys` `fk` join `mysql`.`foreign_key_column_usage` `fkcu` on((`fkcu`.`foreign_key_id` = `fk`.`id`))) where (`fk`.`table_id` = `tbl`.`id`)) `constraints` join `mysql`.`columns` `col` on((`constraints`.`column_id` = `col`.`id`)))) where ((0 <> can_access_column(`sch`.`name`,`tbl`.`name`,`col`.`name`)) and (0 <> is_visible_dd_object(`tbl`.`hidden`,((`col`.`hidden` not in ('Visible','User')) or (0 <> `constraints`.`HIDDEN`)),`col`.`options`)));

-- 数据导出被取消选择。

-- 导出  表 information_schema.OPTIMIZER_TRACE 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `OPTIMIZER_TRACE` (
  `QUERY` longtext NOT NULL,
  `TRACE` longtext NOT NULL,
  `MISSING_BYTES_BEYOND_MAX_MEM_SIZE` int NOT NULL DEFAULT '0',
  `INSUFFICIENT_PRIVILEGES` tinyint NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.PARAMETERS 结构
CREATIF NOT EXISTS E ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`PARAMETERS` AS select (`cat`.`name` collate utf8mb3_tolower_ci) AS `SPECIFIC_CATALOG`,(`sch`.`name` collate utf8mb3_tolower_ci) AS `SPECIFIC_SCHEMA`,`rtn`.`name` AS `SPECIFIC_NAME`,if((`rtn`.`type` = 'FUNCTION'),(`prm`.`ordinal_position` - 1),`prm`.`ordinal_position`) AS `ORDINAL_POSITION`,if(((`rtn`.`type` = 'FUNCTION') and (`prm`.`ordinal_position` = 1)),NULL,`prm`.`mode`) AS `PARAMETER_MODE`,if(((`rtn`.`type` = 'FUNCTION') and (`prm`.`ordinal_position` = 1)),NULL,`prm`.`name`) AS `PARAMETER_NAME`,substring_index(substring_index(`prm`.`data_type_utf8`,'(',1),' ',1) AS `DATA_TYPE`,internal_dd_char_length(`prm`.`data_type`,`prm`.`char_length`,`col`.`name`,0) AS `CHARACTER_MAXIMUM_LENGTH`,internal_dd_char_length(`prm`.`data_type`,`prm`.`char_length`,`col`.`name`,1) AS `CHARACTER_OCTET_LENGTH`,`prm`.`numeric_precision` AS `NUMERIC_PRECISION`,if((`prm`.`numeric_precision` is null),NULL,ifnull(`prm`.`numeric_scale`,0)) AS `NUMERIC_SCALE`,`prm`.`datetime_precision` AS `DATETIME_PRECISION`,(case `prm`.`data_type` when 'MYSQL_TYPE_STRING' then if((`cs`.`name` = 'binary'),NULL,`cs`.`name`) when 'MYSQL_TYPE_VAR_STRING' then if((`cs`.`name` = 'binary'),NULL,`cs`.`name`) when 'MYSQL_TYPE_VARCHAR' then if((`cs`.`name` = 'binary'),NULL,`cs`.`name`) when 'MYSQL_TYPE_TINY_BLOB' then if((`cs`.`name` = 'binary'),NULL,`cs`.`name`) when 'MYSQL_TYPE_MEDIUM_BLOB' then if((`cs`.`name` = 'binary'),NULL,`cs`.`name`) when 'MYSQL_TYPE_BLOB' then if((`cs`.`name` = 'binary'),NULL,`cs`.`name`) when 'MYSQL_TYPE_LONG_BLOB' then if((`cs`.`name` = 'binary'),NULL,`cs`.`name`) when 'MYSQL_TYPE_ENUM' then if((`cs`.`name` = 'binary'),NULL,`cs`.`name`) when 'MYSQL_TYPE_SET' then if((`cs`.`name` = 'binary'),NULL,`cs`.`name`) else NULL end) AS `CHARACTER_SET_NAME`,(case `prm`.`data_type` when 'MYSQL_TYPE_STRING' then if((`cs`.`name` = 'binary'),NULL,`col`.`name`) when 'MYSQL_TYPE_VAR_STRING' then if((`cs`.`name` = 'binary'),NULL,`col`.`name`) when 'MYSQL_TYPE_VARCHAR' then if((`cs`.`name` = 'binary'),NULL,`col`.`name`) when 'MYSQL_TYPE_TINY_BLOB' then if((`cs`.`name` = 'binary'),NULL,`col`.`name`) when 'MYSQL_TYPE_MEDIUM_BLOB' then if((`cs`.`name` = 'binary'),NULL,`col`.`name`) when 'MYSQL_TYPE_BLOB' then if((`cs`.`name` = 'binary'),NULL,`col`.`name`) when 'MYSQL_TYPE_LONG_BLOB' then if((`cs`.`name` = 'binary'),NULL,`col`.`name`) when 'MYSQL_TYPE_ENUM' then if((`cs`.`name` = 'binary'),NULL,`col`.`name`) when 'MYSQL_TYPE_SET' then if((`cs`.`name` = 'binary'),NULL,`col`.`name`) else NULL end) AS `COLLATION_NAME`,`prm`.`data_type_utf8` AS `DTD_IDENTIFIER`,`rtn`.`type` AS `ROUTINE_TYPE` from (((((`mysql`.`parameters` `prm` join `mysql`.`routines` `rtn` on((`prm`.`routine_id` = `rtn`.`id`))) join `mysql`.`schemata` `sch` on((`rtn`.`schema_id` = `sch`.`id`))) join `mysql`.`catalogs` `cat` on((`cat`.`id` = `sch`.`catalog_id`))) join `mysql`.`collations` `col` on((`prm`.`collation_id` = `col`.`id`))) join `mysql`.`character_sets` `cs` on((`col`.`character_set_id` = `cs`.`id`))) where (0 <> can_access_routine(`sch`.`name`,`rtn`.`name`,`rtn`.`type`,`rtn`.`definer`,false));

-- 数据导出被取消选择。

-- 导出  表 information_schema.PARTITIONS 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`PARTITIONS` AS select (`cat`.`name` collate utf8mb3_tolower_ci) AS `TABLE_IF NOT EXISTS CATALOG`,(`sch`.`name` collate utf8mb3_tolower_ci) AS `TABLE_SCHEMA`,`tbl`.`name` AS `TABLE_NAME`,`part`.`name` AS `PARTITION_NAME`,`sub_part`.`name` AS `SUBPARTITION_NAME`,(`part`.`number` + 1) AS `PARTITION_ORDINAL_POSITION`,(`sub_part`.`number` + 1) AS `SUBPARTITION_ORDINAL_POSITION`,(case `tbl`.`partition_type` when 'HASH' then 'HASH' when 'RANGE' then 'RANGE' when 'LIST' then 'LIST' when 'AUTO' then 'AUTO' when 'KEY_51' then 'KEY' when 'KEY_55' then 'KEY' when 'LINEAR_KEY_51' then 'LINEAR KEY' when 'LINEAR_KEY_55' then 'LINEAR KEY' when 'LINEAR_HASH' then 'LINEAR HASH' when 'RANGE_COLUMNS' then 'RANGE COLUMNS' when 'LIST_COLUMNS' then 'LIST COLUMNS' else NULL end) AS `PARTITION_METHOD`,(case `tbl`.`subpartition_type` when 'HASH' then 'HASH' when 'RANGE' then 'RANGE' when 'LIST' then 'LIST' when 'AUTO' then 'AUTO' when 'KEY_51' then 'KEY' when 'KEY_55' then 'KEY' when 'LINEAR_KEY_51' then 'LINEAR KEY' when 'LINEAR_KEY_55' then 'LINEAR KEY' when 'LINEAR_HASH' then 'LINEAR HASH' when 'RANGE_COLUMNS' then 'RANGE COLUMNS' when 'LIST_COLUMNS' then 'LIST COLUMNS' else NULL end) AS `SUBPARTITION_METHOD`,`tbl`.`partition_expression_utf8` AS `PARTITION_EXPRESSION`,`tbl`.`subpartition_expression_utf8` AS `SUBPARTITION_EXPRESSION`,`part`.`description_utf8` AS `PARTITION_DESCRIPTION`,internal_table_rows(`sch`.`name`,`tbl`.`name`,if((`tbl`.`partition_type` is null),`tbl`.`engine`,''),`tbl`.`se_private_id`,(`tbl`.`hidden` <> 'Visible'),if((`sub_part`.`name` is null),if((`part`.`name` is null),`tbl`.`se_private_data`,`part_ts`.`se_private_data`),`sub_part_ts`.`se_private_data`),0,0,ifnull(`sub_part`.`name`,`part`.`name`)) AS `TABLE_ROWS`,internal_avg_row_length(`sch`.`name`,`tbl`.`name`,if((`tbl`.`partition_type` is null),`tbl`.`engine`,''),`tbl`.`se_private_id`,(`tbl`.`hidden` <> 'Visible'),if((`sub_part`.`name` is null),if((`part`.`name` is null),`tbl`.`se_private_data`,`part_ts`.`se_private_data`),`sub_part_ts`.`se_private_data`),0,0,ifnull(`sub_part`.`name`,`part`.`name`)) AS `AVG_ROW_LENGTH`,internal_data_length(`sch`.`name`,`tbl`.`name`,if((`tbl`.`partition_type` is null),`tbl`.`engine`,''),`tbl`.`se_private_id`,(`tbl`.`hidden` <> 'Visible'),if((`sub_part`.`name` is null),if((`part`.`name` is null),`tbl`.`se_private_data`,`part_ts`.`se_private_data`),`sub_part_ts`.`se_private_data`),0,0,ifnull(`sub_part`.`name`,`part`.`name`)) AS `DATA_LENGTH`,internal_max_data_length(`sch`.`name`,`tbl`.`name`,if((`tbl`.`partition_type` is null),`tbl`.`engine`,''),`tbl`.`se_private_id`,(`tbl`.`hidden` <> 'Visible'),if((`sub_part`.`name` is null),if((`part`.`name` is null),`tbl`.`se_private_data`,`part_ts`.`se_private_data`),`sub_part_ts`.`se_private_data`),0,0,ifnull(`sub_part`.`name`,`part`.`name`)) AS `MAX_DATA_LENGTH`,internal_index_length(`sch`.`name`,`tbl`.`name`,if((`tbl`.`partition_type` is null),`tbl`.`engine`,''),`tbl`.`se_private_id`,(`tbl`.`hidden` <> 'Visible'),if((`sub_part`.`name` is null),if((`part`.`name` is null),`tbl`.`se_private_data`,`part_ts`.`se_private_data`),`sub_part_ts`.`se_private_data`),0,0,ifnull(`sub_part`.`name`,`part`.`name`)) AS `INDEX_LENGTH`,internal_data_free(`sch`.`name`,`tbl`.`name`,if((`tbl`.`partition_type` is null),`tbl`.`engine`,''),`tbl`.`se_private_id`,(`tbl`.`hidden` <> 'Visible'),if((`sub_part`.`name` is null),if((`part`.`name` is null),`tbl`.`se_private_data`,`part_ts`.`se_private_data`),`sub_part_ts`.`se_private_data`),0,0,ifnull(`sub_part`.`name`,`part`.`name`)) AS `DATA_FREE`,`tbl`.`created` AS `CREATE_TIME`,internal_update_time(`sch`.`name`,`tbl`.`name`,if((`tbl`.`partition_type` is null),`tbl`.`engine`,''),`tbl`.`se_private_id`,(`tbl`.`hidden` <> 'Visible'),if((`sub_part`.`name` is null),if((`part`.`name` is null),`tbl`.`se_private_data`,`part_ts`.`se_private_data`),`sub_part_ts`.`se_private_data`),0,0,ifnull(`sub_part`.`name`,`part`.`name`)) AS `UPDATE_TIME`,internal_check_time(`sch`.`name`,`tbl`.`name`,if((`tbl`.`partition_type` is null),`tbl`.`engine`,''),`tbl`.`se_private_id`,(`tbl`.`hidden` <> 'Visible'),if((`sub_part`.`name` is null),if((`part`.`name` is null),`tbl`.`se_private_data`,`part_ts`.`se_private_data`),`sub_part_ts`.`se_private_data`),0,0,ifnull(`sub_part`.`name`,`part`.`name`)) AS `CHECK_TIME`,internal_checksum(`sch`.`name`,`tbl`.`name`,if((`tbl`.`partition_type` is null),`tbl`.`engine`,''),`tbl`.`se_private_id`,(`tbl`.`hidden` <> 'Visible'),if((`sub_part`.`name` is null),if((`part`.`name` is null),`tbl`.`se_private_data`,`part_ts`.`se_private_data`),`sub_part_ts`.`se_private_data`),0,0,ifnull(`sub_part`.`name`,`part`.`name`)) AS `CHECKSUM`,if((`sub_part`.`name` is null),ifnull(`part`.`comment`,''),ifnull(`sub_part`.`comment`,'')) AS `PARTITION_COMMENT`,if((`part`.`name` is null),'',internal_get_partition_nodegroup(if((`sub_part`.`name` is null),`part`.`options`,`sub_part`.`options`))) AS `NODEGROUP`,ifnull(`sub_part_ts`.`name`,`part_ts`.`name`) AS `TABLESPACE_NAME` from ((((((`mysql`.`tables` `tbl` join `mysql`.`schemata` `sch` on((`sch`.`id` = `tbl`.`schema_id`))) join `mysql`.`catalogs` `cat` on((`cat`.`id` = `sch`.`catalog_id`))) left join `mysql`.`table_partitions` `part` on((`part`.`table_id` = `tbl`.`id`))) left join `mysql`.`table_partitions` `sub_part` on((`sub_part`.`parent_partition_id` = `part`.`id`))) left join `mysql`.`tablespaces` `part_ts` on((`part_ts`.`id` = `part`.`tablespace_id`))) left join `mysql`.`tablespaces` `sub_part_ts` on(((`sub_part`.`tablespace_id` is not null) and (`sub_part_ts`.`id` = `sub_part`.`tablespace_id`)))) where ((0 <> can_access_table(`sch`.`name`,`tbl`.`name`)) and (0 <> is_visible_dd_object(`tbl`.`hidden`)) and (`part`.`parent_partition_id` is null));

-- 数据导出被取消选择。

-- 导出  表 information_schema.PLUGINS 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `PLUGINS` (
  `PLUGIN_NAME` varchar(64) NOT NULL DEFAULT '',
  `PLUGIN_VERSION` varchar(20) NOT NULL DEFAULT '',
  `PLUGIN_STATUS` varchar(10) NOT NULL DEFAULT '',
  `PLUGIN_TYPE` varchar(80) NOT NULL DEFAULT '',
  `PLUGIN_TYPE_VERSION` varchar(20) NOT NULL DEFAULT '',
  `PLUGIN_LIBRARY` varchar(64) DEFAULT NULL,
  `PLUGIN_LIBRARY_VERSION` varchar(20) DEFAULT NULL,
  `PLUGIN_AUTHOR` varchar(64) DEFAULT NULL,
  `PLUGIN_DESCRIPTION` longtext,
  `PLUGIN_LICENSE` varchar(80) DEFAULT NULL,
  `LOAD_OPTION` varchar(64) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.PROCESSLIST 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `PROCESSLIST` (
  `ID` bigint unsigned NOT NULL DEFAULT '0',
  `USER` varchar(32) NOT NULL DEFAULT '',
  `HOST` varchar(261) NOT NULL DEFAULT '',
  `DB` varchar(64) DEFAULT NULL,
  `COMMAND` varchar(16) NOT NULL DEFAULT '',
  `TIME` int NOT NULL DEFAULT '0',
  `STATE` varchar(64) DEFAULT NULL,
  `INFO` longtext
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.PROFILING 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `PROFILING` (
  `QUERY_ID` int NOT NULL DEFAULT '0',
  `SEQ` int NOT NULL DEFAULT '0',
  `STATE` varchar(30) NOT NULL DEFAULT '',
  `DURATION` decimal(9,6) NOT NULL DEFAULT '0.000000',
  `CPU_USER` decimal(9,6) DEFAULT NULL,
  `CPU_SYSTEM` decimal(9,6) DEFAULT NULL,
  `CONTEXT_VOLUNTARY` int DEFAULT NULL,
  `CONTEXT_INVOLUNTARY` int DEFAULT NULL,
  `BLOCK_OPS_IN` int DEFAULT NULL,
  `BLOCK_OPS_OUT` int DEFAULT NULL,
  `MESSAGES_SENT` int DEFAULT NULL,
  `MESSAGES_RECEIVED` int DEFAULT NULL,
  `PAGE_FAULTS_MAJOR` int DEFAULT NULL,
  `PAGE_FAULTS_MINOR` int DEFAULT NULL,
  `SWAPS` int DEFAULT NULL,
  `SOURCE_FUNCTION` varchar(30) DEFAULT NULL,
  `SOURCE_FILE` varchar(20) DEFAULT NULL,
  `SOURCE_LINE` int DEFAULT NULL
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.REFERENTIAL_CONSTRAINTS 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`REFERENTIAL_CONSTRAINTS` AS select `cat`.`name` AS `CONSTRAINT_CATALOG`,`sch`.`name` AS `CONSTRAINT_SCHEMA`,(`fk`.`name` collate utf8mb3_tolower_ci) AS `CONSTRAINT_NAME`,`fk`.`referenced_table_catalog` AS `UNIQUE_CONSTRAINT_CATALOG`,`fk`.`referenced_table_schema` AS `UNIQUE_CONSTRAINT_SCHEMA`,`fk`.`unique_constraint_name` AS `UNIQUE_CONSTRAINT_NAME`,`fk`.`match_option` AS `MATCH_OPTION`,`fk`.`update_rule` AS `UPDATE_RULE`,`fk`.`delete_rule` AS `DELETE_RULE`,`tbl`.`name` AS `TABLE_IF NOT EXISTS NAME`,`fk`.`referenced_table_name` AS `REFERENCED_TABLE_NAME` from (((`mysql`.`foreign_keys` `fk` join `mysql`.`tables` `tbl` on((`fk`.`table_id` = `tbl`.`id`))) join `mysql`.`schemata` `sch` on((`fk`.`schema_id` = `sch`.`id`))) join `mysql`.`catalogs` `cat` on((`cat`.`id` = `sch`.`catalog_id`))) where ((0 <> can_access_table(`sch`.`name`,`tbl`.`name`)) and (0 <> is_visible_dd_object(`tbl`.`hidden`)));

-- 数据导出被取消选择。

-- 导出  表 information_schema.RESOURCE_GROUPS 结构
CREATIF NOT EXISTS E ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`RESOURCE_GROUPS` AS select `res`.`resource_group_name` AS `RESOURCE_GROUP_NAME`,`res`.`resource_group_type` AS `RESOURCE_GROUP_TYPE`,`res`.`resource_group_enabled` AS `RESOURCE_GROUP_ENABLED`,convert_cpu_id_mask(`res`.`cpu_id_mask`) AS `VCPU_IDS`,`res`.`thread_priority` AS `THREAD_PRIORITY` from `mysql`.`resource_groups` `res` where (0 <> can_access_resource_group(`res`.`resource_group_name`));

-- 数据导出被取消选择。

-- 导出  表 information_schema.ROLE_COLUMN_GRANTS 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`ROLE_COLUMN_GRANTS` AS with recursive `role_graph` (`c_parent_user`,`c_parent_host`,`c_from_user`,`c_from_host`,`c_to_user`,`c_to_host`,`role_path`,`c_with_admin`,`c_enabled`) as (select internal_get_username() AS `INTERNAL_GET_USERNAME()`,internal_get_hostname() AS `INTERNAL_GET_HOSTNAME()`,internal_get_username() AS `INTERNAL_GET_USERNAME()`,internal_get_hostname() AS `INTERNAL_GET_HOSTNAME()`,cast('' as char(64) charset utf8mb4) AS `CAST('' as CHAR(64) CHARSET utf8mb4)`,cast('' as char(255) charset utf8mb4) AS `CAST('' as CHAR(255) CHARSET utf8mb4)`,cast(sha2(concat(quote(internal_get_username()),'@',quote(internal_get_hostname())),256) as char(17000) charset utf8mb4) AS `CAST(SHA2(CONCAT(QUOTE(INTERNAL_GET_USERNAME()),'@',                        QUOTE(INTERNAL_GET_HOSTNAME())), 256)            AS CHAR(17000) CHARSET utf8mb4)`,cast('N' as char(1) charset utf8mb4) AS `CAST('N' as CHAR(1) CHARSET utf8mb4)`,false AS `FALSE` union select internal_get_username() AS `INTERNAL_GET_USERNAME()`,internal_get_hostname() AS `INTERNAL_GET_HOSTNAME()`,`mandatory_roles`.`ROLE_NAME` AS `ROLE_NAME`,`mandatory_roles`.`ROLE_HOST` AS `ROLE_HOST`,internal_get_username() AS `INTERNAL_GET_USERNAME()`,internal_get_hostname() AS `INTERNAL_GET_HOSTNAME()`,cast(sha2(concat(quote(`mandatory_roles`.`ROLE_NAME`),'@',convert(quote(`mandatory_roles`.`ROLE_HOST`) using utf8mb4)),256) as char(17000) charset utf8mb4) AS `CAST(SHA2(CONCAT(QUOTE(ROLE_NAME),'@',                   CONVERT(QUOTE(ROLE_HOST) using utf8mb4)), 256)              AS CHAR(17000) CHARSET utf8mb4)`,cast('N' as char(1) charset utf8mb4) AS `CAST('N' as CHAR(1) CHARSET utf8mb4)`,false AS `FALSE` from json_table(internal_get_mandatory_roles_json(), '$[*]' columns (`ROLE_NAME` varchar(255) character set utf8mb4 path '$.ROLE_NAME', `ROLE_HOST` varchar(255) character set utf8mb4 path '$.ROLE_HOST')) `mandatory_roles` where concat(quote(`mandatory_roles`.`ROLE_NAME`),'@',convert(quote(`mandatory_roles`.`ROLE_HOST`) using utf8mb4)) in (select concat(convert(quote(`mysql`.`role_edges`.`FROM_USER`) using utf8mb4),'@',convert(quote(`mysql`.`role_edges`.`FROM_HOST`) using utf8mb4)) from `mysql`.`role_edges` where ((`mysql`.`role_edges`.`TO_USER` = internal_get_username()) and (convert(`mysql`.`role_edges`.`TO_HOST` using utf8mb4) = convert(internal_get_hostname() using utf8mb4)))) is false union select `role_graph`.`c_parent_user` AS `c_parent_user`,`role_graph`.`c_parent_host` AS `c_parent_host`,`mysql`.`role_edges`.`FROM_USER` AS `FROM_USER`,`mysql`.`role_edges`.`FROM_HOST` AS `FROM_HOST`,`mysql`.`role_edges`.`TO_USER` AS `TO_USER`,`mysql`.`role_edges`.`TO_HOST` AS `TO_HOST`,if((locate(sha2(concat(convert(quote(`mysql`.`role_edges`.`FROM_USER`) using utf8mb4),'@',convert(quote(`mysql`.`role_edges`.`FROM_HOST`) using utf8mb4)),256),`role_graph`.`role_path`) = 0),concat(`role_graph`.`role_path`,'->',convert(sha2(concat(convert(quote(`mysql`.`role_edges`.`FROM_USER`) using utf8mb4),'@',convert(quote(`mysql`.`role_edges`.`FROM_HOST`) using utf8mb4)),256) using utf8mb4)),NULL) AS `IF(LOCATE(SHA2(CONCAT(QUOTE(FROM_USER),'@',                      CONVERT(QUOTE(FROM_HOST) using utf8mb4)), 256),                 role_path) = 0,          CONCAT(role_path,'->', SHA2(CONCAT(QUOTE(FROM_USER),'@',           CONVERT(QUOTE(FROM_HOST) using utf8`,`mysql`.`role_edges`.`WITH_ADMIN_OPTION` AS `WITH_ADMIN_OPTION`,if(((0 <> `role_graph`.`c_enabled`) or (0 <> internal_is_enabled_role(`mysql`.`role_edges`.`FROM_USER`,`mysql`.`role_edges`.`FROM_HOST`))),true,false) AS `IF(c_enabled OR        INTERNAL_IS_ENABLED_ROLE(FROM_USER, FROM_HOST), TRUE, FALSE)` from (`mysql`.`role_edges` join `role_graph`) where ((`mysql`.`role_edges`.`TO_USER` = `role_graph`.`c_from_user`) and (convert(`mysql`.`role_edges`.`TO_HOST` using utf8mb4) = `role_graph`.`c_from_host`) and (`role_graph`.`role_path` is not null))) select distinct internal_get_username(`tp`.`Grantor`) AS `GRANTOR`,internal_get_hostname(`tp`.`Grantor`) AS `GRANTOR_HOST`,`cp`.`User` AS `GRANTEE`,`cp`.`Host` AS `GRANTEE_HOST`,'def' AS `TABLE_IF NOT EXISTS CATALOG`,`cp`.`Db` AS `TABLE_SCHEMA`,`cp`.`Table_name` AS `TABLE_NAME`,`cp`.`Column_name` AS `COLUMN_NAME`,`cp`.`Column_priv` AS `PRIVILEGE_TYPE`,if((find_in_set('Grant',`tp`.`Table_priv`) > 0),'YES','NO') AS `IS_GRANTABLE` from ((`mysql`.`tables_priv` `tp` join `role_graph` `rg` on(((`tp`.`User` = `rg`.`c_from_user`) and (convert(`tp`.`Host` using utf8mb4) = `rg`.`c_from_host`)))) join `mysql`.`columns_priv` `cp` on(((convert(`tp`.`Host` using utf8mb4) = `cp`.`Host`) and (`cp`.`Db` = `tp`.`Db`) and (`cp`.`User` = `tp`.`User`) and (`cp`.`Table_name` = `tp`.`Table_name`)))) where ((`cp`.`Column_priv` > 0) and (`rg`.`c_to_user` <> '') and (`rg`.`c_enabled` = true));

-- 数据导出被取消选择。

-- 导出  表 information_schema.ROLE_ROUTINE_GRANTS 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`ROLE_ROUTINE_GRANTS` AS with recursive `role_graph` (`c_parent_user`,`c_parent_host`,`c_from_user`,`c_from_host`,`c_to_user`,`c_to_host`,`role_path`,`c_with_admin`,`c_enabled`) as (select internal_get_username() AS `INTERNAL_GET_USERNAME()`,internal_get_hostname() AS `INTERNAL_GET_HOSTNAME()`,internal_get_username() AS `INTERNAL_GET_USERNAME()`,internal_get_hostname() AS `INTERNAL_GET_HOSTNAME()`,cast('' as char(64) charset utf8mb4) AS `CAST('' as CHAR(64) CHARSET utf8mb4)`,cast('' as char(255) charset utf8mb4) AS `CAST('' as CHAR(255) CHARSET utf8mb4)`,cast(sha2(concat(quote(internal_get_username()),'@',quote(internal_get_hostname())),256) as char(17000) charset utf8mb4) AS `CAST(SHA2(CONCAT(QUOTE(INTERNAL_GET_USERNAME()),'@',                        QUOTE(INTERNAL_GET_HOSTNAME())), 256)            AS CHAR(17000) CHARSET utf8mb4)`,cast('N' as char(1) charset utf8mb4) AS `CAST('N' as CHAR(1) CHARSET utf8mb4)`,false AS `FALSE` union select internal_get_username() AS `INTERNAL_GET_USERNAME()`,internal_get_hostname() AS `INTERNAL_GET_HOSTNAME()`,`mandatory_roles`.`ROLE_NAME` AS `ROLE_NAME`,`mandatory_roles`.`ROLE_HOST` AS `ROLE_HOST`,internal_get_username() AS `INTERNAL_GET_USERNAME()`,internal_get_hostname() AS `INTERNAL_GET_HOSTNAME()`,cast(sha2(concat(quote(`mandatory_roles`.`ROLE_NAME`),'@',convert(quote(`mandatory_roles`.`ROLE_HOST`) using utf8mb4)),256) as char(17000) charset utf8mb4) AS `CAST(SHA2(CONCAT(QUOTE(ROLE_NAME),'@',                   CONVERT(QUOTE(ROLE_HOST) using utf8mb4)), 256)              AS CHAR(17000) CHARSET utf8mb4)`,cast('N' as char(1) charset utf8mb4) AS `CAST('N' as CHAR(1) CHARSET utf8mb4)`,false AS `FALSE` from json_table(internal_get_mandatory_roles_json(), '$[*]' columns (`ROLE_NAME` varchar(255) character set utf8mb4 path '$.ROLE_NAME', `ROLE_HOST` varchar(255) character set utf8mb4 path '$.ROLE_HOST')) `mandatory_roles` where concat(quote(`mandatory_roles`.`ROLE_NAME`),'@',convert(quote(`mandatory_roles`.`ROLE_HOST`) using utf8mb4)) in (select concat(convert(quote(`mysql`.`role_edges`.`FROM_USER`) using utf8mb4),'@',convert(quote(`mysql`.`role_edges`.`FROM_HOST`) using utf8mb4)) from `mysql`.`role_edges` where ((`mysql`.`role_edges`.`TO_USER` = internal_get_username()) and (convert(`mysql`.`role_edges`.`TO_HOST` using utf8mb4) = convert(internal_get_hostname() using utf8mb4)))) is false union select `role_graph`.`c_parent_user` AS `c_parent_user`,`role_graph`.`c_parent_host` AS `c_parent_host`,`mysql`.`role_edges`.`FROM_USER` AS `FROM_USER`,`mysql`.`role_edges`.`FROM_HOST` AS `FROM_HOST`,`mysql`.`role_edges`.`TO_USER` AS `TO_USER`,`mysql`.`role_edges`.`TO_HOST` AS `TO_HOST`,if((locate(sha2(concat(convert(quote(`mysql`.`role_edges`.`FROM_USER`) using utf8mb4),'@',convert(quote(`mysql`.`role_edges`.`FROM_HOST`) using utf8mb4)),256),`role_graph`.`role_path`) = 0),concat(`role_graph`.`role_path`,'->',convert(sha2(concat(convert(quote(`mysql`.`role_edges`.`FROM_USER`) using utf8mb4),'@',convert(quote(`mysql`.`role_edges`.`FROM_HOST`) using utf8mb4)),256) using utf8mb4)),NULL) AS `IF(LOCATE(SHA2(CONCAT(QUOTE(FROM_USER),'@',                      CONVERT(QUOTE(FROM_HOST) using utf8mb4)), 256),                 role_path) = 0,          CONCAT(role_path,'->', SHA2(CONCAT(QUOTE(FROM_USER),'@',           CONVERT(QUOTE(FROM_HOST) using utf8`,`mysql`.`role_edges`.`WITH_ADMIN_OPTION` AS `WITH_ADMIN_OPTION`,if(((0 <> `role_graph`.`c_enabled`) or (0 <> internal_is_enabled_role(`mysql`.`role_edges`.`FROM_USER`,`mysql`.`role_edges`.`FROM_HOST`))),true,false) AS `IF(c_enabled OR        INTERNAL_IS_ENABLED_ROLE(FROM_USER, FROM_HOST), TRUE, FALSE)` from (`mysql`.`role_edges` join `role_graph`) where ((`mysql`.`role_edges`.`TO_USER` = `role_graph`.`c_from_user`) and (convert(`mysql`.`role_edges`.`TO_HOST` using utf8mb4) = `role_graph`.`c_from_host`) and (`role_graph`.`role_path` is not null))) select distinct internal_get_username(`pp`.`Grantor`) AS `GRANTOR`,internal_get_hostname(`pp`.`Grantor`) AS `GRANTOR_HOST`,`pp`.`User` AS `GRANTEE`,`pp`.`Host` AS `GRANTEE_HOST`,'def' AS `SPECIFIC_CATALOG`,`pp`.`Db` AS `SPECIFIC_SCHEMA`,`pp`.`Routine_name` AS `SPECIFIC_NAME`,'def' AS `ROUTINE_CATALOG`,`pp`.`Db` AS `ROUTINE_SCHEMA`,`pp`.`Routine_name` AS `ROUTINE_NAME`,`pp`.`Proc_priv` AS `PRIVILEGE_TYPE`,if((find_in_set('Grant',`pp`.`Proc_priv`) > 0),'YES','NO') AS `IS_GRANTABLE`IF NOT EXISTS  from (`mysql`.`procs_priv` `pp` join `role_graph` `rg` on(((`pp`.`User` = `rg`.`c_from_user`) and (convert(`pp`.`Host` using utf8mb4) = `rg`.`c_from_host`)))) where ((`pp`.`Proc_priv` > 0) and (`rg`.`c_to_user` <> '') and (`rg`.`c_enabled` = true));

-- 数据导出被取消选择。

-- 导出  表 information_schema.ROLE_TABLE_GRANTS 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`ROLE_TABLE_IF NOT EXISTS GRANTS` AS with recursive `role_graph` (`c_parent_user`,`c_parent_host`,`c_from_user`,`c_from_host`,`c_to_user`,`c_to_host`,`role_path`,`c_with_admin`,`c_enabled`) as (select internal_get_username() AS `INTERNAL_GET_USERNAME()`,internal_get_hostname() AS `INTERNAL_GET_HOSTNAME()`,internal_get_username() AS `INTERNAL_GET_USERNAME()`,internal_get_hostname() AS `INTERNAL_GET_HOSTNAME()`,cast('' as char(64) charset utf8mb4) AS `CAST('' as CHAR(64) CHARSET utf8mb4)`,cast('' as char(255) charset utf8mb4) AS `CAST('' as CHAR(255) CHARSET utf8mb4)`,cast(sha2(concat(quote(internal_get_username()),'@',quote(internal_get_hostname())),256) as char(17000) charset utf8mb4) AS `CAST(SHA2(CONCAT(QUOTE(INTERNAL_GET_USERNAME()),'@',                        QUOTE(INTERNAL_GET_HOSTNAME())), 256)            AS CHAR(17000) CHARSET utf8mb4)`,cast('N' as char(1) charset utf8mb4) AS `CAST('N' as CHAR(1) CHARSET utf8mb4)`,false AS `FALSE` union select internal_get_username() AS `INTERNAL_GET_USERNAME()`,internal_get_hostname() AS `INTERNAL_GET_HOSTNAME()`,`mandatory_roles`.`ROLE_NAME` AS `ROLE_NAME`,`mandatory_roles`.`ROLE_HOST` AS `ROLE_HOST`,internal_get_username() AS `INTERNAL_GET_USERNAME()`,internal_get_hostname() AS `INTERNAL_GET_HOSTNAME()`,cast(sha2(concat(quote(`mandatory_roles`.`ROLE_NAME`),'@',convert(quote(`mandatory_roles`.`ROLE_HOST`) using utf8mb4)),256) as char(17000) charset utf8mb4) AS `CAST(SHA2(CONCAT(QUOTE(ROLE_NAME),'@',                   CONVERT(QUOTE(ROLE_HOST) using utf8mb4)), 256)              AS CHAR(17000) CHARSET utf8mb4)`,cast('N' as char(1) charset utf8mb4) AS `CAST('N' as CHAR(1) CHARSET utf8mb4)`,false AS `FALSE` from json_table(internal_get_mandatory_roles_json(), '$[*]' columns (`ROLE_NAME` varchar(255) character set utf8mb4 path '$.ROLE_NAME', `ROLE_HOST` varchar(255) character set utf8mb4 path '$.ROLE_HOST')) `mandatory_roles` where concat(quote(`mandatory_roles`.`ROLE_NAME`),'@',convert(quote(`mandatory_roles`.`ROLE_HOST`) using utf8mb4)) in (select concat(convert(quote(`mysql`.`role_edges`.`FROM_USER`) using utf8mb4),'@',convert(quote(`mysql`.`role_edges`.`FROM_HOST`) using utf8mb4)) from `mysql`.`role_edges` where ((`mysql`.`role_edges`.`TO_USER` = internal_get_username()) and (convert(`mysql`.`role_edges`.`TO_HOST` using utf8mb4) = convert(internal_get_hostname() using utf8mb4)))) is false union select `role_graph`.`c_parent_user` AS `c_parent_user`,`role_graph`.`c_parent_host` AS `c_parent_host`,`mysql`.`role_edges`.`FROM_USER` AS `FROM_USER`,`mysql`.`role_edges`.`FROM_HOST` AS `FROM_HOST`,`mysql`.`role_edges`.`TO_USER` AS `TO_USER`,`mysql`.`role_edges`.`TO_HOST` AS `TO_HOST`,if((locate(sha2(concat(convert(quote(`mysql`.`role_edges`.`FROM_USER`) using utf8mb4),'@',convert(quote(`mysql`.`role_edges`.`FROM_HOST`) using utf8mb4)),256),`role_graph`.`role_path`) = 0),concat(`role_graph`.`role_path`,'->',convert(sha2(concat(convert(quote(`mysql`.`role_edges`.`FROM_USER`) using utf8mb4),'@',convert(quote(`mysql`.`role_edges`.`FROM_HOST`) using utf8mb4)),256) using utf8mb4)),NULL) AS `IF(LOCATE(SHA2(CONCAT(QUOTE(FROM_USER),'@',                      CONVERT(QUOTE(FROM_HOST) using utf8mb4)), 256),                 role_path) = 0,          CONCAT(role_path,'->', SHA2(CONCAT(QUOTE(FROM_USER),'@',           CONVERT(QUOTE(FROM_HOST) using utf8`,`mysql`.`role_edges`.`WITH_ADMIN_OPTION` AS `WITH_ADMIN_OPTION`,if(((0 <> `role_graph`.`c_enabled`) or (0 <> internal_is_enabled_role(`mysql`.`role_edges`.`FROM_USER`,`mysql`.`role_edges`.`FROM_HOST`))),true,false) AS `IF(c_enabled OR        INTERNAL_IS_ENABLED_ROLE(FROM_USER, FROM_HOST), TRUE, FALSE)` from (`mysql`.`role_edges` join `role_graph`) where ((`mysql`.`role_edges`.`TO_USER` = `role_graph`.`c_from_user`) and (convert(`mysql`.`role_edges`.`TO_HOST` using utf8mb4) = `role_graph`.`c_from_host`) and (`role_graph`.`role_path` is not null))) select distinct internal_get_username(`tp`.`Grantor`) AS `GRANTOR`,internal_get_hostname(`tp`.`Grantor`) AS `GRANTOR_HOST`,`tp`.`User` AS `GRANTEE`,`tp`.`Host` AS `GRANTEE_HOST`,'def' AS `TABLE_CATALOG`,`tp`.`Db` AS `TABLE_SCHEMA`,`tp`.`Table_name` AS `TABLE_NAME`,`tp`.`Table_priv` AS `PRIVILEGE_TYPE`,if((find_in_set('Grant',`tp`.`Table_priv`) > 0),'YES','NO') AS `IS_GRANTABLE` from (`mysql`.`tables_priv` `tp` join `role_graph` `rg` on(((`tp`.`User` = `rg`.`c_from_user`) and (convert(`tp`.`Host` using utf8mb4) = `rg`.`c_from_host`)))) where ((`tp`.`Table_priv` > 0) and (`rg`.`c_to_user` <> '') and (`rg`.`c_enabled` = true));

-- 数据导出被取消选择。

-- 导出  表 information_schema.ROUTINES 结构
CREATIF NOT EXISTS E ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`ROUTINES` AS select `rtn`.`name` AS `SPECIFIC_NAME`,(`cat`.`name` collate utf8mb3_tolower_ci) AS `ROUTINE_CATALOG`,(`sch`.`name` collate utf8mb3_tolower_ci) AS `ROUTINE_SCHEMA`,`rtn`.`name` AS `ROUTINE_NAME`,`rtn`.`type` AS `ROUTINE_TYPE`,if((`rtn`.`type` = 'PROCEDURE'),'',substring_index(substring_index(`rtn`.`result_data_type_utf8`,'(',1),' ',1)) AS `DATA_TYPE`,internal_dd_char_length(`rtn`.`result_data_type`,`rtn`.`result_char_length`,`coll_result`.`name`,0) AS `CHARACTER_MAXIMUM_LENGTH`,internal_dd_char_length(`rtn`.`result_data_type`,`rtn`.`result_char_length`,`coll_result`.`name`,1) AS `CHARACTER_OCTET_LENGTH`,`rtn`.`result_numeric_precision` AS `NUMERIC_PRECISION`,`rtn`.`result_numeric_scale` AS `NUMERIC_SCALE`,`rtn`.`result_datetime_precision` AS `DATETIME_PRECISION`,(case `rtn`.`result_data_type` when 'MYSQL_TYPE_STRING' then if((`cs_result`.`name` = 'binary'),NULL,`cs_result`.`name`) when 'MYSQL_TYPE_VAR_STRING' then if((`cs_result`.`name` = 'binary'),NULL,`cs_result`.`name`) when 'MYSQL_TYPE_VARCHAR' then if((`cs_result`.`name` = 'binary'),NULL,`cs_result`.`name`) when 'MYSQL_TYPE_TINY_BLOB' then if((`cs_result`.`name` = 'binary'),NULL,`cs_result`.`name`) when 'MYSQL_TYPE_MEDIUM_BLOB' then if((`cs_result`.`name` = 'binary'),NULL,`cs_result`.`name`) when 'MYSQL_TYPE_BLOB' then if((`cs_result`.`name` = 'binary'),NULL,`cs_result`.`name`) when 'MYSQL_TYPE_LONG_BLOB' then if((`cs_result`.`name` = 'binary'),NULL,`cs_result`.`name`) when 'MYSQL_TYPE_ENUM' then if((`cs_result`.`name` = 'binary'),NULL,`cs_result`.`name`) when 'MYSQL_TYPE_SET' then if((`cs_result`.`name` = 'binary'),NULL,`cs_result`.`name`) else NULL end) AS `CHARACTER_SET_NAME`,(case `rtn`.`result_data_type` when 'MYSQL_TYPE_STRING' then if((`cs_result`.`name` = 'binary'),NULL,`coll_result`.`name`) when 'MYSQL_TYPE_VAR_STRING' then if((`cs_result`.`name` = 'binary'),NULL,`coll_result`.`name`) when 'MYSQL_TYPE_VARCHAR' then if((`cs_result`.`name` = 'binary'),NULL,`coll_result`.`name`) when 'MYSQL_TYPE_TINY_BLOB' then if((`cs_result`.`name` = 'binary'),NULL,`coll_result`.`name`) when 'MYSQL_TYPE_MEDIUM_BLOB' then if((`cs_result`.`name` = 'binary'),NULL,`coll_result`.`name`) when 'MYSQL_TYPE_BLOB' then if((`cs_result`.`name` = 'binary'),NULL,`coll_result`.`name`) when 'MYSQL_TYPE_LONG_BLOB' then if((`cs_result`.`name` = 'binary'),NULL,`coll_result`.`name`) when 'MYSQL_TYPE_ENUM' then if((`cs_result`.`name` = 'binary'),NULL,`coll_result`.`name`) when 'MYSQL_TYPE_SET' then if((`cs_result`.`name` = 'binary'),NULL,`coll_result`.`name`) else NULL end) AS `COLLATION_NAME`,if((`rtn`.`type` = 'PROCEDURE'),NULL,`rtn`.`result_data_type_utf8`) AS `DTD_IDENTIFIER`,'SQL' AS `ROUTINE_BODY`,if(can_access_routine(`sch`.`name`,`rtn`.`name`,`rtn`.`type`,`rtn`.`definer`,true),`rtn`.`definition_utf8`,NULL) AS `ROUTINE_DEFINITION`,NULL AS `EXTERNAL_NAME`,`rtn`.`external_language` AS `EXTERNAL_LANGUAGE`,'SQL' AS `PARAMETER_STYLE`,if((`rtn`.`is_deterministic` = 0),'NO','YES') AS `IS_DETERMINISTIC`,`rtn`.`sql_data_access` AS `SQL_DATA_ACCESS`,NULL AS `SQL_PATH`,`rtn`.`security_type` AS `SECURITY_TYPE`,`rtn`.`created` AS `CREATED`,`rtn`.`last_altered` AS `LAST_ALTERED`,`rtn`.`sql_mode` AS `SQL_MODE`,`rtn`.`comment` AS `ROUTINE_COMMENT`,`rtn`.`definer` AS `DEFINER`,`cs_client`.`name` AS `CHARACTER_SET_CLIENT`,`coll_conn`.`name` AS `COLLATION_CONNECTION`,`coll_db`.`name` AS `DATABASE_COLLATION` from ((((((((`mysql`.`routines` `rtn` join `mysql`.`schemata` `sch` on((`rtn`.`schema_id` = `sch`.`id`))) join `mysql`.`catalogs` `cat` on((`cat`.`id` = `sch`.`catalog_id`))) join `mysql`.`collations` `coll_client` on((`coll_client`.`id` = `rtn`.`client_collation_id`))) join `mysql`.`character_sets` `cs_client` on((`cs_client`.`id` = `coll_client`.`character_set_id`))) join `mysql`.`collations` `coll_conn` on((`coll_conn`.`id` = `rtn`.`connection_collation_id`))) join `mysql`.`collations` `coll_db` on((`coll_db`.`id` = `rtn`.`schema_collation_id`))) left join `mysql`.`collations` `coll_result` on((`coll_result`.`id` = `rtn`.`result_collation_id`))) left join `mysql`.`character_sets` `cs_result` on((`cs_result`.`id` = `coll_result`.`character_set_id`))) where (0 <> can_access_routine(`sch`.`name`,`rtn`.`name`,`rtn`.`type`,`rtn`.`definer`,false));

-- 数据导出被取消选择。

-- 导出  表 information_schema.SCHEMATA 结构
CREATIF NOT EXISTS E ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`SCHEMATA` AS select (`cat`.`name` collate utf8mb3_tolower_ci) AS `CATALOG_NAME`,(`sch`.`name` collate utf8mb3_tolower_ci) AS `SCHEMA_NAME`,`cs`.`name` AS `DEFAULT_CHARACTER_SET_NAME`,`col`.`name` AS `DEFAULT_COLLATION_NAME`,NULL AS `SQL_PATH`,`sch`.`default_encryption` AS `DEFAULT_ENCRYPTION` from (((`mysql`.`schemata` `sch` join `mysql`.`catalogs` `cat` on((`cat`.`id` = `sch`.`catalog_id`))) join `mysql`.`collations` `col` on((`sch`.`default_collation_id` = `col`.`id`))) join `mysql`.`character_sets` `cs` on((`col`.`character_set_id` = `cs`.`id`))) where (0 <> can_access_database(`sch`.`name`));

-- 数据导出被取消选择。

-- 导出  表 information_schema.SCHEMATA_EXTENSIONS 结构
CREATIF NOT EXISTS E ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`SCHEMATA_EXTENSIONS` AS select (`cat`.`name` collate utf8mb3_tolower_ci) AS `CATALOG_NAME`,(`sch`.`name` collate utf8mb3_tolower_ci) AS `SCHEMA_NAME`,get_dd_schema_options(`sch`.`options`) AS `OPTIONS` from (`mysql`.`schemata` `sch` join `mysql`.`catalogs` `cat` on((`cat`.`id` = `sch`.`catalog_id`))) where (0 <> can_access_database(`sch`.`name`));

-- 数据导出被取消选择。

-- 导出  表 information_schema.SCHEMA_PRIVILEGES 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `SCHEMA_PRIVILEGES` (
  `GRANTEE` varchar(292) NOT NULL DEFAULT '',
  `TABLE_CATALOG` varchar(512) NOT NULL DEFAULT '',
  `TABLE_SCHEMA` varchar(64) NOT NULL DEFAULT '',
  `PRIVILEGE_TYPE` varchar(64) NOT NULL DEFAULT '',
  `IS_GRANTABLE` varchar(3) NOT NULL DEFAULT ''
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.STATISTICS 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`STATISTICS` AS select (`cat`.`name` collate utf8mb3_tolower_ci) AS `TABLE_IF NOT EXISTS CATALOG`,(`sch`.`name` collate utf8mb3_tolower_ci) AS `TABLE_SCHEMA`,(`tbl`.`name` collate utf8mb3_tolower_ci) AS `TABLE_NAME`,if(((`idx`.`type` = 'PRIMARY') or (`idx`.`type` = 'UNIQUE')),0,1) AS `NON_UNIQUE`,(`sch`.`name` collate utf8mb3_tolower_ci) AS `INDEX_SCHEMA`,(`idx`.`name` collate utf8mb3_tolower_ci) AS `INDEX_NAME`,`icu`.`ordinal_position` AS `SEQ_IN_INDEX`,if((`col`.`hidden` = 'SQL'),NULL,(`col`.`name` collate utf8mb3_tolower_ci)) AS `COLUMN_NAME`,(case when (`icu`.`order` = 'DESC') then 'D' when (`icu`.`order` = 'ASC') then 'A' else NULL end) AS `COLLATION`,internal_index_column_cardinality(`sch`.`name`,`tbl`.`name`,`idx`.`name`,`col`.`name`,`idx`.`ordinal_position`,`icu`.`ordinal_position`,if((`tbl`.`partition_type` is null),`tbl`.`engine`,''),`tbl`.`se_private_id`,((`tbl`.`hidden` <> 'Visible') or (0 <> `idx`.`hidden`) or (0 <> `icu`.`hidden`)),coalesce(`stat`.`cardinality`,cast(-(1) as unsigned)),coalesce(cast(`stat`.`cached_time` as unsigned),0)) AS `CARDINALITY`,get_dd_index_sub_part_length(`icu`.`length`,`col`.`type`,`col`.`char_length`,`col`.`collation_id`,`idx`.`type`) AS `SUB_PART`,NULL AS `PACKED`,if((`col`.`is_nullable` = 1),'YES','') AS `NULLABLE`,(case when (`idx`.`type` = 'SPATIAL') then 'SPATIAL' when (`idx`.`algorithm` = 'SE_PRIVATE') then '' else `idx`.`algorithm` end) AS `INDEX_TYPE`,if(((`idx`.`type` = 'PRIMARY') or (`idx`.`type` = 'UNIQUE')),'',if(internal_keys_disabled(`tbl`.`options`),'disabled','')) AS `COMMENT`,`idx`.`comment` AS `INDEX_COMMENT`,if(`idx`.`is_visible`,'YES','NO') AS `IS_VISIBLE`,if((`col`.`hidden` = 'SQL'),`col`.`generation_expression_utf8`,NULL) AS `EXPRESSION` from (((((((`mysql`.`index_column_usage` `icu` join `mysql`.`indexes` `idx` on((`idx`.`id` = `icu`.`index_id`))) join `mysql`.`tables` `tbl` on((`idx`.`table_id` = `tbl`.`id`))) join `mysql`.`columns` `col` on((`icu`.`column_id` = `col`.`id`))) join `mysql`.`schemata` `sch` on((`tbl`.`schema_id` = `sch`.`id`))) join `mysql`.`catalogs` `cat` on((`cat`.`id` = `sch`.`catalog_id`))) join `mysql`.`collations` `coll` on((`tbl`.`collation_id` = `coll`.`id`))) left join `mysql`.`index_stats` `stat` on(((`tbl`.`name` = `stat`.`table_name`) and (`sch`.`name` = `stat`.`schema_name`) and (`idx`.`name` = `stat`.`index_name`) and (`col`.`name` = `stat`.`column_name`)))) where ((0 <> can_access_table(`sch`.`name`,`tbl`.`name`)) and (0 <> is_visible_dd_object(`tbl`.`hidden`,((0 <> `idx`.`hidden`) or (0 <> `icu`.`hidden`)),`idx`.`options`)));

-- 数据导出被取消选择。

-- 导出  表 information_schema.ST_GEOMETRY_COLUMNS 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`ST_GEOMETRY_COLUMNS` AS select `information_schema`.`cols`.`TABLE_IF NOT EXISTS CATALOG` AS `TABLE_CATALOG`,`information_schema`.`cols`.`TABLE_SCHEMA` AS `TABLE_SCHEMA`,`information_schema`.`cols`.`TABLE_NAME` AS `TABLE_NAME`,`information_schema`.`cols`.`COLUMN_NAME` AS `COLUMN_NAME`,`information_schema`.`srs`.`SRS_NAME` AS `SRS_NAME`,`information_schema`.`cols`.`SRS_ID` AS `SRS_ID`,`information_schema`.`cols`.`DATA_TYPE` AS `GEOMETRY_TYPE_NAME` from (`information_schema`.`COLUMNS` `cols` left join `information_schema`.`ST_SPATIAL_REFERENCE_SYSTEMS` `srs` on((`information_schema`.`cols`.`SRS_ID` = `information_schema`.`srs`.`SRS_ID`))) where (`information_schema`.`cols`.`DATA_TYPE` in ('geometry','point','linestring','polygon','multipoint','multilinestring','multipolygon','geomcollection'));

-- 数据导出被取消选择。

-- 导出  表 information_schema.ST_SPATIAL_REFERENCE_SYSTEMS 结构
CREATIF NOT EXISTS E ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`ST_SPATIAL_REFERENCE_SYSTEMS` AS select `mysql`.`st_spatial_reference_systems`.`name` AS `SRS_NAME`,`mysql`.`st_spatial_reference_systems`.`id` AS `SRS_ID`,`mysql`.`st_spatial_reference_systems`.`organization` AS `ORGANIZATION`,`mysql`.`st_spatial_reference_systems`.`organization_coordsys_id` AS `ORGANIZATION_COORDSYS_ID`,`mysql`.`st_spatial_reference_systems`.`definition` AS `DEFINITION`,`mysql`.`st_spatial_reference_systems`.`description` AS `DESCRIPTION` from `mysql`.`st_spatial_reference_systems`;

-- 数据导出被取消选择。

-- 导出  表 information_schema.ST_UNITS_OF_MEASURE 结构
CREATIF NOT EXISTS E ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`ST_UNITS_OF_MEASURE` AS select `st_units_of_measure`.`UNIT_NAME` AS `UNIT_NAME`,`st_units_of_measure`.`UNIT_TYPE` AS `UNIT_TYPE`,`st_units_of_measure`.`CONVERSION_FACTOR` AS `CONVERSION_FACTOR`,`st_units_of_measure`.`DESCRIPTION` AS `DESCRIPTION` from json_table('[["metre","LINEAR","",1],["millimetre","LINEAR","",0.001],["centimetre","LINEAR","",0.01],["German legal metre","LINEAR","",1.0000135965],["foot","LINEAR","",0.3048],["US survey foot","LINEAR","",0.30480060960121924],["Clarke\'s yard","LINEAR","",0.9143917962],["Clarke\'s foot","LINEAR","",0.3047972654],["British link (Sears 1922 truncated)","LINEAR","",0.20116756],["nautical mile","LINEAR","",1852],["fathom","LINEAR","",1.8288],["US survey chain","LINEAR","",20.11684023368047],["US survey link","LINEAR","",0.2011684023368047],["US survey mile","LINEAR","",1609.3472186944375],["Indian yard","LINEAR","",0.9143985307444408],["kilometre","LINEAR","",1000],["Clarke\'s chain","LINEAR","",20.1166195164],["Clarke\'s link","LINEAR","",0.201166195164],["British yard (Benoit 1895 A)","LINEAR","",0.9143992],["British yard (Sears 1922)","LINEAR","",0.9143984146160287],["British foot (Sears 1922)","LINEAR","",0.3047994715386762],["Gold Coast foot","LINEAR","",0.3047997101815088],["British chain (Sears 1922)","LINEAR","",20.116765121552632],["yard","LINEAR","",0.9144],["British link (Sears 1922)","LINEAR","",0.2011676512155263],["British foot (Benoit 1895 A)","LINEAR","",0.3047997333333333],["Indian foot (1962)","LINEAR","",0.3047996],["British chain (Benoit 1895 A)","LINEAR","",20.1167824],["chain","LINEAR","",20.1168],["British link (Benoit 1895 A)","LINEAR","",0.201167824],["British yard (Benoit 1895 B)","LINEAR","",0.9143992042898124],["British foot (Benoit 1895 B)","LINEAR","",0.30479973476327077],["British chain (Benoit 1895 B)","LINEAR","",20.116782494375872],["British link (Benoit 1895 B)","LINEAR","",0.2011678249437587],["British foot (1865)","LINEAR","",0.30480083333333335],["Indian foot","LINEAR","",0.30479951024814694],["Indian foot (1937)","LINEAR","",0.30479841],["Indian foot (1975)","LINEAR","",0.3047995],["British foot (1936)","LINEAR","",0.3048007491],["Indian yard (1937)","LINEAR","",0.91439523],["Indian yard (1962)","LINEAR","",0.9143988],["Indian yard (1975)","LINEAR","",0.9143985],["Statute mile","LINEAR","",1609.344],["link","LINEAR","",0.201168],["British yard (Sears 1922 truncated)","LINEAR","",0.914398],["British foot (Sears 1922 truncated)","LINEAR","",0.30479933333333337],["British chain (Sears 1922 truncated)","LINEAR","",20.116756]]', '$[*]' columns (`UNIT_NAME` varchar(255) character set utf8mb4 path '$[0]', `UNIT_TYPE` varchar(7) character set utf8mb4 path '$[1]', `DESCRIPTION` varchar(255) character set utf8mb4 path '$[2]', `CONVERSION_FACTOR` double path '$[3]')) `st_units_of_measure`;

-- 数据导出被取消选择。

-- 导出  表 information_schema.TABLES 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`TABLESIF NOT EXISTS ` AS select (`cat`.`name` collate utf8mb3_tolower_ci) AS `TABLE_CATALOG`,(`sch`.`name` collate utf8mb3_tolower_ci) AS `TABLE_SCHEMA`,(`tbl`.`name` collate utf8mb3_tolower_ci) AS `TABLE_NAME`,`tbl`.`type` AS `TABLE_TYPE`,if((`tbl`.`type` = 'BASE TABLE'),`tbl`.`engine`,NULL) AS `ENGINE`,if((`tbl`.`type` = 'VIEW'),NULL,10) AS `VERSION`,`tbl`.`row_format` AS `ROW_FORMAT`,if((`tbl`.`type` = 'VIEW'),NULL,internal_table_rows(`sch`.`name`,`tbl`.`name`,if((`tbl`.`partition_type` is null),`tbl`.`engine`,''),`tbl`.`se_private_id`,(`tbl`.`hidden` <> 'Visible'),`ts`.`se_private_data`,coalesce(`stat`.`table_rows`,0),coalesce(cast(`stat`.`cached_time` as unsigned),0))) AS `TABLE_ROWS`,if((`tbl`.`type` = 'VIEW'),NULL,internal_avg_row_length(`sch`.`name`,`tbl`.`name`,if((`tbl`.`partition_type` is null),`tbl`.`engine`,''),`tbl`.`se_private_id`,(`tbl`.`hidden` <> 'Visible'),`ts`.`se_private_data`,coalesce(`stat`.`avg_row_length`,0),coalesce(cast(`stat`.`cached_time` as unsigned),0))) AS `AVG_ROW_LENGTH`,if((`tbl`.`type` = 'VIEW'),NULL,internal_data_length(`sch`.`name`,`tbl`.`name`,if((`tbl`.`partition_type` is null),`tbl`.`engine`,''),`tbl`.`se_private_id`,(`tbl`.`hidden` <> 'Visible'),`ts`.`se_private_data`,coalesce(`stat`.`data_length`,0),coalesce(cast(`stat`.`cached_time` as unsigned),0))) AS `DATA_LENGTH`,if((`tbl`.`type` = 'VIEW'),NULL,internal_max_data_length(`sch`.`name`,`tbl`.`name`,if((`tbl`.`partition_type` is null),`tbl`.`engine`,''),`tbl`.`se_private_id`,(`tbl`.`hidden` <> 'Visible'),`ts`.`se_private_data`,coalesce(`stat`.`max_data_length`,0),coalesce(cast(`stat`.`cached_time` as unsigned),0))) AS `MAX_DATA_LENGTH`,if((`tbl`.`type` = 'VIEW'),NULL,internal_index_length(`sch`.`name`,`tbl`.`name`,if((`tbl`.`partition_type` is null),`tbl`.`engine`,''),`tbl`.`se_private_id`,(`tbl`.`hidden` <> 'Visible'),`ts`.`se_private_data`,coalesce(`stat`.`index_length`,0),coalesce(cast(`stat`.`cached_time` as unsigned),0))) AS `INDEX_LENGTH`,if((`tbl`.`type` = 'VIEW'),NULL,internal_data_free(`sch`.`name`,`tbl`.`name`,if((`tbl`.`partition_type` is null),`tbl`.`engine`,''),`tbl`.`se_private_id`,(`tbl`.`hidden` <> 'Visible'),`ts`.`se_private_data`,coalesce(`stat`.`data_free`,0),coalesce(cast(`stat`.`cached_time` as unsigned),0))) AS `DATA_FREE`,if((`tbl`.`type` = 'VIEW'),NULL,internal_auto_increment(`sch`.`name`,`tbl`.`name`,if((`tbl`.`partition_type` is null),`tbl`.`engine`,''),`tbl`.`se_private_id`,((0 <> is_visible_dd_object(`tbl`.`hidden`,false,`tbl`.`options`)) is false),`ts`.`se_private_data`,coalesce(`stat`.`auto_increment`,0),coalesce(cast(`stat`.`cached_time` as unsigned),0),`tbl`.`se_private_data`)) AS `AUTO_INCREMENT`,`tbl`.`created` AS `CREATE_TIME`,if((`tbl`.`type` = 'VIEW'),NULL,internal_update_time(`sch`.`name`,`tbl`.`name`,if((`tbl`.`partition_type` is null),`tbl`.`engine`,''),`tbl`.`se_private_id`,(`tbl`.`hidden` <> 'Visible'),`ts`.`se_private_data`,coalesce(cast(`stat`.`update_time` as unsigned),0),coalesce(cast(`stat`.`cached_time` as unsigned),0))) AS `UPDATE_TIME`,if((`tbl`.`type` = 'VIEW'),NULL,internal_check_time(`sch`.`name`,`tbl`.`name`,if((`tbl`.`partition_type` is null),`tbl`.`engine`,''),`tbl`.`se_private_id`,(`tbl`.`hidden` <> 'Visible'),`ts`.`se_private_data`,coalesce(cast(`stat`.`check_time` as unsigned),0),coalesce(cast(`stat`.`cached_time` as unsigned),0))) AS `CHECK_TIME`,`col`.`name` AS `TABLE_COLLATION`,if((`tbl`.`type` = 'VIEW'),NULL,internal_checksum(`sch`.`name`,`tbl`.`name`,if((`tbl`.`partition_type` is null),`tbl`.`engine`,''),`tbl`.`se_private_id`,(`tbl`.`hidden` <> 'Visible'),`ts`.`se_private_data`,coalesce(`stat`.`checksum`,0),coalesce(cast(`stat`.`cached_time` as unsigned),0))) AS `CHECKSUM`,if((`tbl`.`type` = 'VIEW'),NULL,get_dd_create_options(`tbl`.`options`,if((ifnull(`tbl`.`partition_expression`,'NOT_PART_TBL') = 'NOT_PART_TBL'),0,1),if((`sch`.`default_encryption` = 'YES'),1,0))) AS `CREATE_OPTIONS`,internal_get_comment_or_error(`sch`.`name`,`tbl`.`name`,`tbl`.`type`,`tbl`.`options`,`tbl`.`comment`) AS `TABLE_COMMENT` from (((((`mysql`.`tables` `tbl` join `mysql`.`schemata` `sch` on((`tbl`.`schema_id` = `sch`.`id`))) join `mysql`.`catalogs` `cat` on((`cat`.`id` = `sch`.`catalog_id`))) left join `mysql`.`collations` `col` on((`tbl`.`collation_id` = `col`.`id`))) left join `mysql`.`tablespaces` `ts` on((`tbl`.`tablespace_id` = `ts`.`id`))) left join `mysql`.`table_stats` `stat` on(((`tbl`.`name` = `stat`.`table_name`) and (`sch`.`name` = `stat`.`schema_name`)))) where ((0 <> can_access_table(`sch`.`name`,`tbl`.`name`)) and (0 <> is_visible_dd_object(`tbl`.`hidden`)));

-- 数据导出被取消选择。

-- 导出  表 information_schema.TABLESPACES 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `TABLESPACES` (
  `TABLESPACE_NAME` varchar(64) NOT NULL DEFAULT '',
  `ENGINE` varchar(64) NOT NULL DEFAULT '',
  `TABLESPACE_TYPE` varchar(64) DEFAULT NULL,
  `LOGFILE_GROUP_NAME` varchar(64) DEFAULT NULL,
  `EXTENT_SIZE` bigint unsigned DEFAULT NULL,
  `AUTOEXTEND_SIZE` bigint unsigned DEFAULT NULL,
  `MAXIMUM_SIZE` bigint unsigned DEFAULT NULL,
  `NODEGROUP_ID` bigint unsigned DEFAULT NULL,
  `TABLESPACE_COMMENT` varchar(2048) DEFAULT NULL
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.TABLESPACES_EXTENSIONS 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`TABLESIF NOT EXISTS PACES_EXTENSIONS` AS select `tsps`.`name` AS `TABLESPACE_NAME`,`tsps`.`engine_attribute` AS `ENGINE_ATTRIBUTE` from `mysql`.`tablespaces` `tsps`;

-- 数据导出被取消选择。

-- 导出  表 information_schema.TABLES_EXTENSIONS 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`TABLESIF NOT EXISTS _EXTENSIONS` AS select `cat`.`name` AS `TABLE_CATALOG`,`sch`.`name` AS `TABLE_SCHEMA`,`tbl`.`name` AS `TABLE_NAME`,`tbl`.`engine_attribute` AS `ENGINE_ATTRIBUTE`,`tbl`.`secondary_engine_attribute` AS `SECONDARY_ENGINE_ATTRIBUTE` from ((`mysql`.`tables` `tbl` join `mysql`.`schemata` `sch` on((`tbl`.`schema_id` = `sch`.`id`))) join `mysql`.`catalogs` `cat` on((`cat`.`id` = `sch`.`catalog_id`))) where ((0 <> can_access_table(`sch`.`name`,`tbl`.`name`)) and (0 <> is_visible_dd_object(`tbl`.`hidden`)));

-- 数据导出被取消选择。

-- 导出  表 information_schema.TABLE_CONSTRAINTS 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`TABLE_IF NOT EXISTS CONSTRAINTS` AS select (`cat`.`name` collate utf8mb3_tolower_ci) AS `CONSTRAINT_CATALOG`,(`sch`.`name` collate utf8mb3_tolower_ci) AS `CONSTRAINT_SCHEMA`,`constraints`.`CONSTRAINT_NAME` AS `CONSTRAINT_NAME`,(`sch`.`name` collate utf8mb3_tolower_ci) AS `TABLE_SCHEMA`,(`tbl`.`name` collate utf8mb3_tolower_ci) AS `TABLE_NAME`,`constraints`.`CONSTRAINT_TYPE` AS `CONSTRAINT_TYPE`,`constraints`.`ENFORCED` AS `ENFORCED` from (((`mysql`.`tables` `tbl` join `mysql`.`schemata` `sch` on((`tbl`.`schema_id` = `sch`.`id`))) join `mysql`.`catalogs` `cat` on((`cat`.`id` = `sch`.`catalog_id`))) join lateral (select `idx`.`name` AS `CONSTRAINT_NAME`,if((`idx`.`type` = 'PRIMARY'),'PRIMARY KEY',`idx`.`type`) AS `CONSTRAINT_TYPE`,'YES' AS `ENFORCED` from `mysql`.`indexes` `idx` where ((`idx`.`table_id` = `tbl`.`id`) and (`idx`.`type` in ('PRIMARY','UNIQUE')) and (0 <> is_visible_dd_object(`tbl`.`hidden`,`idx`.`hidden`,`idx`.`options`))) union all select (`fk`.`name` collate utf8mb3_tolower_ci) AS `CONSTRAINT_NAME`,'FOREIGN KEY' AS `CONSTRAINT_TYPE`,'YES' AS `ENFORCED` from `mysql`.`foreign_keys` `fk` where (`fk`.`table_id` = `tbl`.`id`) union all select `cc`.`name` AS `CONSTRAINT_NAME`,'CHECK' AS `CONSTRAINT_TYPE`,`cc`.`enforced` AS `ENFORCED` from `mysql`.`check_constraints` `cc` where (`cc`.`table_id` = `tbl`.`id`)) `constraints`) where ((0 <> can_access_table(`sch`.`name`,`tbl`.`name`)) and (0 <> is_visible_dd_object(`tbl`.`hidden`)));

-- 数据导出被取消选择。

-- 导出  表 information_schema.TABLE_CONSTRAINTS_EXTENSIONS 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`TABLE_IF NOT EXISTS CONSTRAINTS_EXTENSIONS` AS select `cat`.`name` AS `CONSTRAINT_CATALOG`,`sch`.`name` AS `CONSTRAINT_SCHEMA`,`idx`.`name` AS `CONSTRAINT_NAME`,`tbl`.`name` AS `TABLE_NAME`,`idx`.`engine_attribute` AS `ENGINE_ATTRIBUTE`,`idx`.`secondary_engine_attribute` AS `SECONDARY_ENGINE_ATTRIBUTE` from (((`mysql`.`indexes` `idx` join `mysql`.`tables` `tbl` on((`idx`.`table_id` = `tbl`.`id`))) join `mysql`.`schemata` `sch` on((`tbl`.`schema_id` = `sch`.`id`))) join `mysql`.`catalogs` `cat` on((`cat`.`id` = `sch`.`catalog_id`))) where ((0 <> can_access_table(`sch`.`name`,`tbl`.`name`)) and (0 <> is_visible_dd_object(`tbl`.`hidden`,false,`idx`.`options`)));

-- 数据导出被取消选择。

-- 导出  表 information_schema.TABLE_PRIVILEGES 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `TABLE_PRIVILEGES` (
  `GRANTEE` varchar(292) NOT NULL DEFAULT '',
  `TABLE_CATALOG` varchar(512) NOT NULL DEFAULT '',
  `TABLE_SCHEMA` varchar(64) NOT NULL DEFAULT '',
  `TABLE_NAME` varchar(64) NOT NULL DEFAULT '',
  `PRIVILEGE_TYPE` varchar(64) NOT NULL DEFAULT '',
  `IS_GRANTABLE` varchar(3) NOT NULL DEFAULT ''
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.TRIGGERS 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`TRIGGERS` AS select (`cat`.`name` collate utf8mb3_tolower_ci) AS `TRIGGER_CATALOG`,(`sch`.`name` collate utf8mb3_tolower_ci) AS `TRIGGER_SCHEMA`,`trg`.`name` AS `TRIGGER_NAME`,`trg`.`event_type` AS `EVENT_MANIPULATION`,(`cat`.`name` collate utf8mb3_tolower_ci) AS `EVENT_OBJECT_CATALOG`,(`sch`.`name` collate utf8mb3_tolower_ci) AS `EVENT_OBJECT_SCHEMA`,(`tbl`.`name` collate utf8mb3_tolower_ci) AS `EVENT_OBJECT_TABLE`IF NOT EXISTS ,`trg`.`action_order` AS `ACTION_ORDER`,NULL AS `ACTION_CONDITION`,`trg`.`action_statement_utf8` AS `ACTION_STATEMENT`,'ROW' AS `ACTION_ORIENTATION`,`trg`.`action_timing` AS `ACTION_TIMING`,NULL AS `ACTION_REFERENCE_OLD_TABLE`,NULL AS `ACTION_REFERENCE_NEW_TABLE`,'OLD' AS `ACTION_REFERENCE_OLD_ROW`,'NEW' AS `ACTION_REFERENCE_NEW_ROW`,`trg`.`created` AS `CREATED`,`trg`.`sql_mode` AS `SQL_MODE`,`trg`.`definer` AS `DEFINER`,`cs_client`.`name` AS `CHARACTER_SET_CLIENT`,`coll_conn`.`name` AS `COLLATION_CONNECTION`,`coll_db`.`name` AS `DATABASE_COLLATION` from (((((((`mysql`.`triggers` `trg` join `mysql`.`tables` `tbl` on((`tbl`.`id` = `trg`.`table_id`))) join `mysql`.`schemata` `sch` on((`tbl`.`schema_id` = `sch`.`id`))) join `mysql`.`catalogs` `cat` on((`cat`.`id` = `sch`.`catalog_id`))) join `mysql`.`collations` `coll_client` on((`coll_client`.`id` = `trg`.`client_collation_id`))) join `mysql`.`character_sets` `cs_client` on((`cs_client`.`id` = `coll_client`.`character_set_id`))) join `mysql`.`collations` `coll_conn` on((`coll_conn`.`id` = `trg`.`connection_collation_id`))) join `mysql`.`collations` `coll_db` on((`coll_db`.`id` = `trg`.`schema_collation_id`))) where ((`tbl`.`type` <> 'VIEW') and (0 <> can_access_trigger(`sch`.`name`,`tbl`.`name`)) and (0 <> is_visible_dd_object(`tbl`.`hidden`)));

-- 数据导出被取消选择。

-- 导出  表 information_schema.USER_ATTRIBUTES 结构
CREATIF NOT EXISTS E ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`USER_ATTRIBUTES` AS select `mysql`.`user`.`User` AS `USER`,`mysql`.`user`.`Host` AS `HOST`,json_unquote(json_extract(`mysql`.`user`.`User_attributes`,'$.metadata')) AS `ATTRIBUTE` from `mysql`.`user` where (0 <> can_access_user(`mysql`.`user`.`User`,`mysql`.`user`.`Host`));

-- 数据导出被取消选择。

-- 导出  表 information_schema.USER_PRIVILEGES 结构
CREATE TEMPORARY TABLE IF NOT EXISTS `USER_PRIVILEGES` (
  `GRANTEE` varchar(292) NOT NULL DEFAULT '',
  `TABLE_CATALOG` varchar(512) NOT NULL DEFAULT '',
  `PRIVILEGE_TYPE` varchar(64) NOT NULL DEFAULT '',
  `IS_GRANTABLE` varchar(3) NOT NULL DEFAULT ''
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb3;

-- 数据导出被取消选择。

-- 导出  表 information_schema.VIEWS 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`VIEWS` AS select (`cat`.`name` collate utf8mb3_tolower_ci) AS `TABLE_IF NOT EXISTS CATALOG`,(`sch`.`name` collate utf8mb3_tolower_ci) AS `TABLE_SCHEMA`,(`vw`.`name` collate utf8mb3_tolower_ci) AS `TABLE_NAME`,if((can_access_view(`sch`.`name`,`vw`.`name`,`vw`.`view_definer`,`vw`.`options`) = true),`vw`.`view_definition_utf8`,'') AS `VIEW_DEFINITION`,`vw`.`view_check_option` AS `CHECK_OPTION`,`vw`.`view_is_updatable` AS `IS_UPDATABLE`,`vw`.`view_definer` AS `DEFINER`,if((`vw`.`view_security_type` = 'DEFAULT'),'DEFINER',`vw`.`view_security_type`) AS `SECURITY_TYPE`,`cs`.`name` AS `CHARACTER_SET_CLIENT`,`conn_coll`.`name` AS `COLLATION_CONNECTION` from (((((`mysql`.`tables` `vw` join `mysql`.`schemata` `sch` on((`vw`.`schema_id` = `sch`.`id`))) join `mysql`.`catalogs` `cat` on((`cat`.`id` = `sch`.`catalog_id`))) join `mysql`.`collations` `conn_coll` on((`conn_coll`.`id` = `vw`.`view_connection_collation_id`))) join `mysql`.`collations` `client_coll` on((`client_coll`.`id` = `vw`.`view_client_collation_id`))) join `mysql`.`character_sets` `cs` on((`cs`.`id` = `client_coll`.`character_set_id`))) where ((0 <> can_access_table(`sch`.`name`,`vw`.`name`)) and (`vw`.`type` = 'VIEW'));

-- 数据导出被取消选择。

-- 导出  表 information_schema.VIEW_ROUTINE_USAGE 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`VIEW_ROUTINE_USAGE` AS select (`cat`.`name` collate utf8mb3_tolower_ci) AS `TABLE_IF NOT EXISTS CATALOG`,(`sch`.`name` collate utf8mb3_tolower_ci) AS `TABLE_SCHEMA`,(`vw`.`name` collate utf8mb3_tolower_ci) AS `TABLE_NAME`,(`vru`.`routine_catalog` collate utf8mb3_tolower_ci) AS `SPECIFIC_CATALOG`,(`vru`.`routine_schema` collate utf8mb3_tolower_ci) AS `SPECIFIC_SCHEMA`,`vru`.`routine_name` AS `SPECIFIC_NAME` from ((((`mysql`.`tables` `vw` join `mysql`.`schemata` `sch` on((`vw`.`schema_id` = `sch`.`id`))) join `mysql`.`catalogs` `cat` on((`cat`.`id` = `sch`.`catalog_id`))) join `mysql`.`view_routine_usage` `vru` on((`vru`.`view_id` = `vw`.`id`))) join `mysql`.`routines` `rtn` on(((`vru`.`routine_catalog` = `cat`.`name`) and (`vru`.`routine_schema` = `sch`.`name`) and (`vru`.`routine_name` = `rtn`.`name`)))) where ((`vw`.`type` = 'VIEW') and (0 <> can_access_routine(`vru`.`routine_schema`,`vru`.`routine_name`,`rtn`.`type`,`rtn`.`definer`,false)) and (0 <> can_access_view(`sch`.`name`,`vw`.`name`,`vw`.`view_definer`,`vw`.`options`)));

-- 数据导出被取消选择。

-- 导出  表 information_schema.VIEW_TABLE_USAGE 结构
CREATE ALGORITHM=UNDEFINED DEFINER=`mysql.infoschema`@`localhost` SQL SECURITY DEFINER VIEW `information_schema`.`VIEW_TABLE_IF NOT EXISTS USAGE` AS select (`cat`.`name` collate utf8mb3_tolower_ci) AS `VIEW_CATALOG`,(`sch`.`name` collate utf8mb3_tolower_ci) AS `VIEW_SCHEMA`,(`vw`.`name` collate utf8mb3_tolower_ci) AS `VIEW_NAME`,(`vtu`.`table_catalog` collate utf8mb3_tolower_ci) AS `TABLE_CATALOG`,(`vtu`.`table_schema` collate utf8mb3_tolower_ci) AS `TABLE_SCHEMA`,(`vtu`.`table_name` collate utf8mb3_tolower_ci) AS `TABLE_NAME` from (((`mysql`.`tables` `vw` join `mysql`.`schemata` `sch` on((`vw`.`schema_id` = `sch`.`id`))) join `mysql`.`catalogs` `cat` on((`cat`.`id` = `sch`.`catalog_id`))) join `mysql`.`view_table_usage` `vtu` on((`vtu`.`view_id` = `vw`.`id`))) where ((0 <> can_access_table(`vtu`.`table_schema`,`vtu`.`table_name`)) and (`vw`.`type` = 'VIEW') and (0 <> can_access_view(`sch`.`name`,`vw`.`name`,`vw`.`view_definer`,`vw`.`options`)));

-- 数据导出被取消选择。


-- 导出 proxy_db 的数据库结构
CREATE DATABASE IF NOT EXISTS `proxy_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `proxy_db`;

-- 导出  表 proxy_db.available_proxy 结构
CREATE TABLE IF NOT EXISTS `available_proxy` (
  `proxy_tab_id` int NOT NULL,
  `pk` int NOT NULL AUTO_INCREMENT,
  `ip` varchar(1024) DEFAULT NULL,
  `counter` int DEFAULT NULL,
  `max_counter_ts` timestamp NULL DEFAULT NULL,
  `resp_code` smallint DEFAULT NULL,
  `available` tinyint(1) DEFAULT NULL,
  `latest_352_ts` timestamp NULL DEFAULT NULL,
  `latest_used_ts` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`pk`),
  UNIQUE KEY `proxy_tab_id` (`proxy_tab_id`),
  KEY `idx_proxy_tab_id` (`proxy_tab_id`),
  CONSTRAINT `FK_available_proxy_proxy_tab` FOREIGN KEY (`proxy_tab_id`) REFERENCES `proxy_tab` (`proxy_id`)
) ENGINE=InnoDB AUTO_INCREMENT=9005125 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 proxy_db.proxy_tab 结构
CREATE TABLE IF NOT EXISTS `proxy_tab` (
  `proxy_id` int NOT NULL AUTO_INCREMENT,
  `proxy` json NOT NULL,
  `status` int NOT NULL DEFAULT '0',
  `update_ts` int NOT NULL,
  `score` int NOT NULL,
  `add_ts` int DEFAULT NULL,
  `success_times` int DEFAULT '0',
  `zhihu_status` int DEFAULT '0',
  `computed_proxy_str` varchar(255) GENERATED ALWAYS AS (json_unquote(json_extract(`proxy`,concat(_utf8mb4'$.',json_unquote(json_extract(json_keys(`proxy`),_utf8mb4'$[0]')))))) STORED,
  PRIMARY KEY (`proxy_id`),
  UNIQUE KEY `proxy_id` (`proxy_id`),
  KEY `覆盖索引` (`proxy_id`,`status`,`update_ts`,`score`,`add_ts`,`success_times`,`zhihu_status`) USING BTREE,
  KEY `刷新代理索引` (`status`,`score`,`success_times`,`update_ts`) USING BTREE,
  KEY `获取可用代理索引` (`status`,`score`,`update_ts`) USING BTREE,
  KEY `computed_proxy_str` (`computed_proxy_str`)
) ENGINE=InnoDB AUTO_INCREMENT=3676662 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。


-- 导出 samsclub 的数据库结构
CREATE DATABASE IF NOT EXISTS `samsclub` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `samsclub`;

-- 导出  表 samsclub.crawl_task_progress 结构
CREATE TABLE IF NOT EXISTS `crawl_task_progress` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `first_category_id` int NOT NULL,
  `second_category_id` int NOT NULL,
  `last_page_num` int DEFAULT '1',
  `is_finished` tinyint DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `udx_task_key` (`first_category_id`,`second_category_id`)
) ENGINE=InnoDB AUTO_INCREMENT=216 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 samsclub.grouping_info 结构
CREATE TABLE IF NOT EXISTS `grouping_info` (
  `pk` bigint NOT NULL AUTO_INCREMENT,
  `parentGroupingId` int DEFAULT NULL,
  `groupingId` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `groupingIdInt` int GENERATED ALWAYS AS (cast(`groupingId` as signed)) STORED,
  `image` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `level` tinyint NOT NULL,
  `navigationId` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `navigationIdInt` int GENERATED ALWAYS AS (cast(`navigationId` as signed)) STORED,
  `storeId` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `storeIdInt` int GENERATED ALWAYS AS (cast(`storeId` as signed)) STORED,
  `title` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `children` json DEFAULT NULL,
  PRIMARY KEY (`pk`),
  UNIQUE KEY `groupingId` (`groupingId`)
) ENGINE=InnoDB AUTO_INCREMENT=23068 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 samsclub.spu_category 结构
CREATE TABLE IF NOT EXISTS `spu_category` (
  `pk` bigint NOT NULL AUTO_INCREMENT,
  `spu_id` varchar(50) DEFAULT NULL,
  `categoryId` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`pk`) USING BTREE,
  UNIQUE KEY `uq_spuId_categoryId` (`spu_id`,`categoryId`) USING BTREE,
  KEY `create_time` (`create_time`,`update_time`,`categoryId`,`spu_id`,`pk`),
  CONSTRAINT `spu_category_ibfk_1` FOREIGN KEY (`spu_id`) REFERENCES `spu_info` (`spuId`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2269406 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 samsclub.spu_info 结构
CREATE TABLE IF NOT EXISTS `spu_info` (
  `spuId` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'SPU ID',
  `brandId` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `title` varchar(255) NOT NULL,
  `subTitle` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `image` varchar(512) DEFAULT NULL,
  `isAvailable` tinyint(1) DEFAULT NULL,
  `isSerial` tinyint(1) DEFAULT NULL,
  `serialId` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `seriesId` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `deliveryMethod` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `deliveryAttr` int DEFAULT NULL,
  `storeId` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `venderCode` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `masterBizType` int DEFAULT NULL,
  `viceBizType` int DEFAULT NULL,
  `hostItemId` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `exclusiveSpu` tinyint(1) DEFAULT NULL,
  `onlyStoreSale` tinyint(1) DEFAULT NULL,
  `hasVideo` tinyint(1) DEFAULT NULL,
  `isGlobalDirectPurchase` tinyint(1) DEFAULT NULL,
  `isImport` tinyint(1) DEFAULT NULL,
  `isShowXPlusTag` tinyint(1) DEFAULT NULL,
  `isStoreExtent` tinyint(1) DEFAULT NULL,
  `availableStores` json DEFAULT NULL,
  `cityCodes` json DEFAULT NULL,
  `giveSpuList` json DEFAULT NULL,
  `limitInfo` json DEFAULT NULL,
  `beltInfo` json DEFAULT NULL,
  `specInfo` json DEFAULT NULL,
  `specList` json DEFAULT NULL,
  `spuSpecInfo` json DEFAULT NULL,
  `zoneTypeList` json DEFAULT NULL,
  `categoryOuterService` json DEFAULT NULL,
  `smallPackagePriceDisplay` varchar(255) DEFAULT NULL,
  `commonOuterService` json DEFAULT NULL,
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `unknow_field` json DEFAULT NULL,
  `onlyBarSale` tinyint(1) DEFAULT NULL COMMENT '是否只在餐吧销售',
  `arrivalEndTimeDesc` text,
  `attrGroupInfo` json DEFAULT NULL,
  `attrInfo` json DEFAULT NULL,
  `complianceInfo` json DEFAULT NULL,
  `couponContentList` json DEFAULT NULL,
  `couponList` json DEFAULT NULL,
  `customTabList` json DEFAULT NULL,
  `deliveryCapacityCountList` json DEFAULT NULL,
  `desc` text,
  `descVideo` json DEFAULT NULL,
  `detailVideos` json DEFAULT NULL,
  `extendedWarrantyList` json DEFAULT NULL,
  `favorite` tinyint(1) DEFAULT NULL,
  `giveaway` tinyint(1) DEFAULT NULL,
  `imageSizeThreeFour` json DEFAULT NULL,
  `images` json DEFAULT NULL,
  `intro` text,
  `isAllowDelivery` tinyint(1) DEFAULT NULL,
  `isCollectOrder` int DEFAULT NULL,
  `isCompare` tinyint(1) DEFAULT NULL,
  `isCrabCard` tinyint(1) DEFAULT NULL,
  `isGlobalOwnPickUp` tinyint(1) DEFAULT NULL,
  `isGovSpu` tinyint(1) DEFAULT NULL,
  `isPutOnSale` tinyint(1) DEFAULT NULL COMMENT 'false 就代表下架了',
  `isStoreAvailable` tinyint(1) DEFAULT NULL,
  `isTicket` tinyint(1) DEFAULT NULL,
  `netWeight` double DEFAULT NULL,
  `preSellList` json DEFAULT NULL,
  `promotionDetailList` json DEFAULT NULL,
  `promotionList` json DEFAULT NULL,
  `serviceInfo` json DEFAULT NULL,
  `sevenDaysReturn` tinyint(1) DEFAULT NULL,
  `spuExtDTO` json DEFAULT NULL,
  `standardForIntactGoodsUrl` text,
  `temperature` int DEFAULT NULL,
  `valuable` tinyint(1) DEFAULT NULL,
  `weight` double DEFAULT NULL,
  `purchaseLimitText` text,
  `purchaseLimitMinNum` int DEFAULT NULL,
  `globalShoppingTaxRateExplain` text,
  `hostItem` text,
  PRIMARY KEY (`spuId`) USING BTREE,
  KEY `title` (`title`,`update_time`,`spuId`,`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 samsclub.spu_new_tag_info 结构
CREATE TABLE IF NOT EXISTS `spu_new_tag_info` (
  `pk` bigint NOT NULL AUTO_INCREMENT,
  `spu_id` varchar(50) DEFAULT NULL,
  `beginTime` bigint DEFAULT NULL,
  `endTime` bigint DEFAULT NULL,
  `originalPrice` varchar(50) DEFAULT NULL,
  `promotionPrice` varchar(50) DEFAULT NULL,
  `savedMoney` int DEFAULT NULL,
  `titleCn` varchar(50) DEFAULT NULL,
  `logoImageCn` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `logoImageEn` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `logoImageZhCn` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `logoImageWide` int DEFAULT NULL,
  `logoImageHigh` int DEFAULT NULL,
  `placeType` int DEFAULT NULL,
  `priorityValue` int DEFAULT NULL,
  `promotionTag` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `styleCode` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `styleType` int DEFAULT NULL,
  `tagManageId` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `tagMark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `tagPlace` int DEFAULT NULL,
  `tagSortType` int DEFAULT NULL,
  `tagStyleId` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `id` varchar(50) DEFAULT NULL,
  `unknow_field` json DEFAULT NULL,
  PRIMARY KEY (`pk`) USING BTREE,
  UNIQUE KEY `uq_spuId_tagManageId` (`spu_id`,`tagManageId`) USING BTREE,
  KEY `title` (`title`,`spu_id`) USING BTREE,
  CONSTRAINT `spu_new_tag_info_ibfk_1` FOREIGN KEY (`spu_id`) REFERENCES `spu_info` (`spuId`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1255626 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 samsclub.spu_price_info 结构
CREATE TABLE IF NOT EXISTS `spu_price_info` (
  `pk` bigint NOT NULL AUTO_INCREMENT,
  `spu_id` varchar(50) DEFAULT NULL,
  `price` int DEFAULT NULL,
  `priceType` int DEFAULT NULL,
  `priceTypeName` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `unknow_field` json DEFAULT NULL,
  PRIMARY KEY (`pk`),
  KEY `spu_id` (`spu_id`,`price`,`priceType`,`update_time`,`create_time`) USING BTREE,
  CONSTRAINT `FK_spu_price_info_spu_info` FOREIGN KEY (`spu_id`) REFERENCES `spu_info` (`spuId`)
) ENGINE=InnoDB AUTO_INCREMENT=15516 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 samsclub.spu_stock_info 结构
CREATE TABLE IF NOT EXISTS `spu_stock_info` (
  `pk` bigint NOT NULL AUTO_INCREMENT,
  `spu_id` varchar(50) NOT NULL,
  `safeStockQuantity` int DEFAULT NULL,
  `soldQuantity` int DEFAULT NULL,
  `stockQuantity` int DEFAULT NULL,
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `unknow_field` json DEFAULT NULL,
  PRIMARY KEY (`pk`),
  UNIQUE KEY `spu_id` (`spu_id`),
  CONSTRAINT `spu_stock_info_ibfk_1` FOREIGN KEY (`spu_id`) REFERENCES `spu_info` (`spuId`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=686743 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 samsclub.spu_tag_info 结构
CREATE TABLE IF NOT EXISTS `spu_tag_info` (
  `pk` bigint NOT NULL AUTO_INCREMENT,
  `spu_id` varchar(50) DEFAULT NULL,
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `title` varchar(1024) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `tagMark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `tagPlace` int DEFAULT NULL,
  `tagSortType` int DEFAULT NULL,
  `priorityValue` int DEFAULT NULL,
  `promotionTag` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `beginTime` bigint DEFAULT NULL,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `unknow_field` json DEFAULT NULL,
  PRIMARY KEY (`pk`) USING BTREE,
  UNIQUE KEY `spu_id_tag_mark` (`spu_id`,`tagMark`) USING BTREE,
  UNIQUE KEY `spu_id_tag_Id` (`spu_id`,`id`),
  CONSTRAINT `spu_tag_info_ibfk_1` FOREIGN KEY (`spu_id`) REFERENCES `spu_info` (`spuId`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1271233 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 samsclub.spu_video_info 结构
CREATE TABLE IF NOT EXISTS `spu_video_info` (
  `pk` bigint NOT NULL AUTO_INCREMENT,
  `spu_id` varchar(50) DEFAULT NULL,
  `videoUrl` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `videoCover` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `duration` int DEFAULT NULL,
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `unknow_field` json DEFAULT NULL,
  PRIMARY KEY (`pk`) USING BTREE,
  KEY `spu_id` (`spu_id`),
  CONSTRAINT `spu_video_info_ibfk_1` FOREIGN KEY (`spu_id`) REFERENCES `spu_info` (`spuId`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
