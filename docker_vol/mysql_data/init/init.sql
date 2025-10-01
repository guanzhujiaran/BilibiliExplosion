-- --------------------------------------------------------
-- 主机:                           127.0.0.1
-- 服务器版本:                        8.4.6 - MySQL Community Server - GPL
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
) ENGINE=InnoDB AUTO_INCREMENT=432 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
) ENGINE=InnoDB AUTO_INCREMENT=328 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
) ENGINE=InnoDB AUTO_INCREMENT=4131 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
) ENGINE=InnoDB AUTO_INCREMENT=1104855 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
) ENGINE=InnoDB AUTO_INCREMENT=1104854 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
) ENGINE=InnoDB AUTO_INCREMENT=4019 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
) ENGINE=InnoDB AUTO_INCREMENT=784 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
) ENGINE=InnoDB AUTO_INCREMENT=3546979896395999 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
  CONSTRAINT `FK_article_pub_record_lotdata` FOREIGN KEY (`lot_data_business_id`) REFERENCES `lotdata` (`business_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1665 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='发布专栏记录';

-- 数据导出被取消选择。

-- 导出  表 dyndetail.bilidyndetail 结构
CREATE TABLE IF NOT EXISTS `bilidyndetail` (
  `rid` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '',
  `dynamic_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `dynData` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `lot_id` bigint DEFAULT NULL,
  `dynamic_created_time` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `rid_int` bigint GENERATED ALWAYS AS (cast(`rid` as signed)) STORED,
  `dynamic_id_int` bigint GENERATED ALWAYS AS (cast(`dynamic_id` as signed)) STORED,
  PRIMARY KEY (`rid`),
  KEY `biliDynDetail_FK_0_0` (`lot_id`,`rid`,`dynamic_id`,`dynamic_created_time`,`rid_int`,`dynamic_id_int`) USING BTREE,
  KEY `rid` (`rid`),
  KEY `dynamic_id` (`dynamic_id`),
  KEY `lot_id` (`lot_id`),
  KEY `rid_int` (`rid_int`),
  KEY `dynamic_id_int` (`dynamic_id_int`),
  CONSTRAINT `biliDynDetail_FK_0_0` FOREIGN KEY (`lot_id`) REFERENCES `lotdata` (`lottery_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 数据导出被取消选择。

-- 导出  表 dyndetail.bili_atari_info 结构
CREATE TABLE IF NOT EXISTS `bili_atari_info` (
  `pk` bigint NOT NULL AUTO_INCREMENT,
  `mid` bigint DEFAULT NULL,
  `hongbao_money` int DEFAULT NULL,
  `atari_lot_id` bigint DEFAULT NULL,
  `atari_lot_rank` tinyint DEFAULT NULL COMMENT '1：一等奖\r\n2：二等奖\r\n3：三等奖',
  `atari_lot_type` tinyint DEFAULT NULL COMMENT '中奖类型，对应B站business_id',
  `atari_timestamp` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`pk`) USING BTREE,
  UNIQUE KEY `mid` (`mid`,`atari_lot_id`) USING BTREE,
  KEY `FK__lotdata_1` (`atari_lot_id`) USING BTREE,
  KEY `atari_lot_rank` (`atari_lot_rank`) USING BTREE,
  KEY `atari_lot_type` (`atari_lot_type`) USING BTREE,
  KEY `atari_timestamp` (`atari_timestamp`) USING BTREE,
  CONSTRAINT `FK__lotdata_1` FOREIGN KEY (`atari_lot_id`) REFERENCES `lotdata` (`lottery_id`),
  CONSTRAINT `FK_bili_atari_info_bili_user_info` FOREIGN KEY (`mid`) REFERENCES `bili_user_info` (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=14241749 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 数据导出被取消选择。

-- 导出  表 dyndetail.bili_user_info 结构
CREATE TABLE IF NOT EXISTS `bili_user_info` (
  `uid` bigint NOT NULL,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `face` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  PRIMARY KEY (`uid`) USING BTREE,
  KEY `name` (`name`,`uid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
  UNIQUE KEY `UQ_business_id` (`business_id`),
  KEY `business_id` (`business_id`),
  KEY `lottery_time` (`lottery_time`),
  KEY `sender_uid` (`sender_uid`),
  KEY `idx_lottery_id` (`lottery_id`,`business_id`,`lottery_time`,`sender_uid`,`business_type`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=2920829 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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
) ENGINE=InnoDB AUTO_INCREMENT=9042350 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
) ENGINE=InnoDB AUTO_INCREMENT=3703126 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
) ENGINE=InnoDB AUTO_INCREMENT=221 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
) ENGINE=InnoDB AUTO_INCREMENT=25691 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
) ENGINE=InnoDB AUTO_INCREMENT=2495081 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
) ENGINE=InnoDB AUTO_INCREMENT=1389635 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
) ENGINE=InnoDB AUTO_INCREMENT=15975 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
) ENGINE=InnoDB AUTO_INCREMENT=753959 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
) ENGINE=InnoDB AUTO_INCREMENT=1404981 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
