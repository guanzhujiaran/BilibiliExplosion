# -*- coding: utf-8 -*-
"""
API路由统一枚举定义模块

本模块集中管理FastAPI应用中的所有API路由配置，包括：
- 路由前缀 (RouterPrefix)
- 路由标签 (RouterTags)
- 具体路由名称 (RouterNames)

使用方式：
    from ApiRoutes import RouterPrefix, RouterTags, RouterNames
    
    # 引用路由前缀
    prefix = RouterPrefix.BILI_LOTTERY
    
    # 引用路由标签
    tags = [RouterTags.V1_BILI]
    
    # 引用路由名称
    name = RouterNames.GET_COMMON_LOTTERY
"""

from enum import StrEnum


class RouterPrefix(StrEnum):
    """API路由前缀枚举"""
    
    # ==================== V1 版本路由前缀 ====================
    # B站抽奖数据库相关前缀
    BILI_LOTTERY = "/api/v1/lottery_database/bili"  # B站抽奖数据主前缀
    BILI_LOTTERY_STATISTIC = "/api/v1/lottery_database/bili/lottery_statistic/rank"  # B站抽奖统计前缀
    BILI_ZHUANLAN = "/api/v1/lottery_database/bili/zhuanlan"  # B站专栏前缀
    
    # IP信息前缀
    IP_INFO = "/api/v1/ip_info"  # IP信息前缀
    
    # 后台服务前缀
    BACKGROUND_SERVICE = "/api/v1/background_service"  # 后台服务前缀
    
    # 验证码前缀
    CAPTCHA = "/api/v1/captcha"  # 验证码前缀
    
    #  Sams Club前缀
    SAMS_CLUB = "/api/v1/samsClub"  # Sams Club前缀
    
    # ChatGPT/LLM前缀
    CHATGPT = "/api/v1/ChatGpt3_5"  # ChatGPT接口前缀
    
    # ==================== 其他路由前缀 ====================
    # 达摩模型前缀
    DAMO = "/damo"  # 达摩机器学习前缀

    # RPC 服务前缀
    RPC = "/api/v1/rpc"  # RPC 服务信息前缀


class RouterTags(StrEnum):
    """API路由标签枚举 - 用于OpenAPI文档分组"""
    
    # ==================== V1 版本路由标签 ====================
    V1_IP = "V1Ip"  # IP信息服务
    V1_BILI = "V1Bili"  # B站抽奖数据服务
    BACKGROUND_SERVICE = "BackgroundService"  # 后台服务
    CAPTCHA = "Captcha"  # 验证码服务
    SAMS_CLUB = "SamsClub"  # Sams Club服务
    V1_CHATGPT = "V1ChatGPT"  # ChatGPT/LLM服务
    
    # ==================== 其他路由标签 ====================
    COMMON = "CommonRouter"  # 公共路由
    MQ_TEST = "MQ测试"  # 消息队列测试
    DAMO = "modelscope达摩机器学习"  # 达摩机器学习服务
    RPC = "RPC服务"  # RPC 服务信息


class RouterPaths(StrEnum):
    """
    API路由路径枚举 - 用于定义具体的路由路径
    
    命名规范:
    - 使用PascalCase格式，与路由路径保持一致
    - 示例: GET_IP = "/get", GET_COMMON_LOTTERY = "/GetCommonLottery"
    """
    
    # ==================== Damo 达摩路由 ====================
    DAMO_SEMANTIC = "/semantic"  # 情感分析
    
    # ==================== ChatGPT/LLM 路由 ====================
    CHATGPT_REPLY_SINGLE = "/ReplySingle"  # 单轮回复
    CHATGPT_LLM_STATUS = "/LLMStatus"  # LLM状态
    CHATGPT_RESET_LLM_STATUS = "/ResetLLMStatus"  # 重置LLM状态
    CHATGPT_HELLO_WORLD = "/helloWorld"  # 健康检查
    
    # ==================== B站抽奖数据路由 ====================
    # --- 获取类路由 ---
    GET_RESERVE_LOTTERY = "/GetReserveLottery"  # 获取预约抽奖
    GET_OFFICIAL_LOTTERY = "/GetOfficialLottery"  # 获取官方抽奖
    GET_CHARGE_LOTTERY = "/GetChargeLottery"  # 获取充电抽奖
    GET_LIVE_LOTTERY = "/GetLiveLottery"  # 获取直播抽奖
    GET_TOPIC_LOTTERY = "/GetTopicLottery"  # 获取话题抽奖
    GET_ALL_LOTTERY = "/GetAllLottery"  # 获取所有抽奖
    GET_ALL_LOT_SCRAPY_STATUS = "/GetAllLotScrapyStatus"  # 获取所有爬虫状态
    GET_OTHERS_LOT_DYN_LIST = "/GetOthersLotDynList"  # 获取第三方抽奖动态列表（分页+排序）
    GET_LOTTERY_FILTER_PARAMS = "/GetLotteryFilterParams"  # 获取抽奖查询筛选参数元数据
    
    # --- 提交类路由 ---
    ADD_DYNAMIC_LOTTERY = "/AddDynamicLottery"  # 提交抽奖动态
    BULK_ADD_DYNAMIC_LOTTERY = "/BulkAddDynamicLottery"  # 批量提交抽奖动态
    ADD_TOPIC_LOTTERY = "/AddTopicLottery"  # 提交话题抽奖
    BULK_ADD_TOPIC_LOTTERY = "/BulkAddTopicLottery"  # 批量提交话题抽奖
    ADD_OTHERS_LOT_DYN = "/AddOthersLotDyn"  # 提交第三方抽奖动态
    BULK_ADD_OTHERS_LOT_DYN = "/BulkAddOthersLotDyn"  # 批量提交第三方抽奖动态
    SUBMIT_FEEDBACK = "/SubmitFeedback"  # 提交反馈
    SEARCH_LOTTERY_BY_KEYWORD = "/SearchLotteryByKeyword"  # 关键词搜索
    
    # ==================== B站抽奖统计路由 ====================
    GET_LOTTERY_HOF = "/lottery_hof/{lot_type}"  # 获取官方抽奖统计
    GET_LOTTERY_RESULT = "/lottery_result"  # 获取uid中奖数据
    
    # ==================== B站专栏路由 ====================
    GET_LOTTERY_ARTICLE = "/lotteryArticle"  # 获取专栏文章
    
    # ==================== IP信息路由 ====================
    GET_IP = "/get"  # 获取IPv6地址信息
    
    # ==================== 后台服务路由 ====================
    # --- 爬虫状态获取 ---
    GET_DYNAMIC_SCRAPY_STATUS = "/GetDynamicScrapyStatus"  # 动态爬虫状态
    GET_TOPIC_SCRAPY_STATUS = "/GetTopicScrapyStatus"  # 话题爬虫状态
    GET_RESERVE_SCRAPY_STATUS = "/GetReserveScrapyStatus"  # 预约爬虫状态
    GET_ALL_SCRAPY_STATUS = "/GetAllLotScrapyStatus"  # 所有爬虫状态
    GET_OTHERS_LOT_SPACE_STATUS = "/GetOthersLotSpaceStatus"  # 他人空间爬虫状态
    GET_OTHERS_LOT_DYN_STATUS = "/GetOthersLotDynStatus"  # 他人动态爬虫状态
    GET_REFRESH_BILI_OFFICIAL_STATUS = "/GetRefreshBiliOfficialStatus"  # 刷新官方抽奖状态
    GET_REFRESH_BILI_RESERVE_STATUS = "/GetRefreshBiliReserveStatus"  # 刷新预约抽奖状态
    GET_PROXY_STATUS = "/GetProxyStatus"  # 代理状态
    
    # --- 定时任务 ---
    GET_GLOBAL_JOBS = "/GlobalSchedule/GetJobs"  # 全局定时任务
    GET_GLOBAL_SCHEDULER_STATUS = "/GlobalScheduler/Status"  # 全局定时任务详细状态
    
    # --- 服务控制 ---
    GET_ALL_STAT = "/BackgroundService/AllStat"  # 后台服务状态
    START_SERVICE = "/BackgroundService/Start"  # 启动服务
    STOP_SERVICE = "/BackgroundService/Stop"  # 停止服务
    RESTART_SERVICE = "/BackgroundService/Restart"  # 重启服务
    
    # ==================== 验证码路由 ====================
    GEN_CAPTCHA = "/gen"  # 生成验证码
    VERIFY_CAPTCHA = "/verify"  # 验证验证码
    
    # ==================== Sams Club路由 ====================
    SET_NEW_AUTH_TOKEN = "/set_new_auth_token"  # 更新auth_token
    SAMSCLUB_GRAPHQL = "/graphql"  # GraphQL接口
    SAMSCLUB_API_STATUS = "/samsclub_api_status"  # API状态
    
    # ==================== MQ测试路由 ====================
    RABBITMQ_TEST_PUBLISH = "/rabbitmq_test_publish"  # RabbitMQ测试消息发布

    # ==================== RPC 服务路由 ====================
    GET_RPC_METHODS = "/methods"  # 获取所有 RPC 方法信息
    
    # ==================== 公共路由 ====================
    GET_LIVE_LOTS = "/v1/get/live_lots"  # 获取直播抽奖
    TEST = "/test"  # 服务可用性测试
    GC = "/gc"  # 垃圾回收
    POST_RM_FOLLOWING_LIST = "/v1/post/RmFollowingList"  # 取关列表
    UPSERT_LOT_DETAIL = "/lot/upsert_lot_detail"  # 插入/更新抽奖详情
    GET_OTHERS_LOT_DYN = "/get_others_lot_dyn"  # 获取他人动态抽奖
    GET_OTHERS_OFFICIAL_LOT_DYN = "/get_others_official_lot_dyn"  # 获取他人官方动态抽奖
    GET_OTHERS_BIG_LOT = "/get_others_big_lot"  # 获取他人大奖
    GET_OTHERS_BIG_RESERVE = "/get_others_big_reserve"  # 获取重要预约抽奖
    ZHIHU_GET_OTHERS_LOT_PINS = "/zhihu/get_others_lot_pins"  # 获取知乎抽奖
    TOUTIAO_GET_OTHERS_LOT_IDS = "/toutiao/get_others_lot_ids"  # 获取头条抽奖


class RouterNames(StrEnum):
    """
    API路由名称枚举 - 用于reverse生成URL或标识路由
    
    命名规范:
    - 使用全大写+下划线格式
    - 格式: {HTTP_METHOD}_{RESOURCE}_{ACTION}
    - 示例: GET_LOTTERY_HOF, POST_ADD_DYNAMIC_LOTTERY
    """
    
    # ==================== Damo 达摩路由 ====================
    DAMO_SEMANTIC = "damo_semantic"  # 情感分析
    
    # ==================== ChatGPT/LLM 路由 ====================
    CHATGPT_REPLY_SINGLE = "reply_single"  # 单轮回复
    CHATGPT_LLM_STATUS = "llm_status"  # LLM状态
    CHATGPT_RESET_LLM_STATUS = "reset_llm_status"  # 重置LLM状态
    CHATGPT_HELLO_WORLD = "hello_world"  # 健康检查
    
    # ==================== B站抽奖数据路由 ====================
    # --- 获取类路由 ---
    GET_RESERVE_LOTTERY = "get_reserve_lottery"  # 获取预约抽奖
    GET_OFFICIAL_LOTTERY = "get_official_lottery"  # 获取官方抽奖
    GET_CHARGE_LOTTERY = "get_charge_lottery"  # 获取充电抽奖
    GET_LIVE_LOTTERY = "get_live_lottery"  # 获取直播抽奖
    GET_TOPIC_LOTTERY = "get_topic_lottery"  # 获取话题抽奖
    GET_ALL_LOTTERY = "get_all_lottery"  # 获取所有抽奖
    GET_ALL_LOT_SCRAPY_STATUS = "get_all_lot_scrapy_status"  # 获取所有爬虫状态
    GET_OTHERS_LOT_DYN_LIST = "get_others_lot_dyn_list"  # 获取第三方抽奖动态列表
    GET_LOTTERY_FILTER_PARAMS = "get_lottery_filter_params"  # 获取抽奖查询筛选参数元数据
    
    # --- 提交类路由 ---
    ADD_DYNAMIC_LOTTERY = "add_dynamic_lottery"  # 提交抽奖动态
    BULK_ADD_DYNAMIC_LOTTERY = "bulk_add_dynamic_lottery"  # 批量提交抽奖动态
    ADD_TOPIC_LOTTERY = "add_topic_lottery"  # 提交话题抽奖
    BULK_ADD_TOPIC_LOTTERY = "bulk_add_topic_lottery"  # 批量提交话题抽奖
    ADD_OTHERS_LOT_DYN = "add_others_lot_dyn"  # 提交第三方抽奖动态
    BULK_ADD_OTHERS_LOT_DYN = "bulk_add_others_lot_dyn"  # 批量提交第三方抽奖动态
    SUBMIT_FEEDBACK = "submit_feedback"  # 提交反馈
    SEARCH_LOTTERY_BY_KEYWORD = "search_lottery_by_keyword"  # 关键词搜索
    
    # ==================== B站抽奖统计路由 ====================
    GET_LOTTERY_HOF = "lottery_hof"  # 获取官方抽奖统计
    GET_LOTTERY_RESULT = "lottery_result"  # 获取uid中奖数据
    
    # ==================== B站专栏路由 ====================
    GET_LOTTERY_ARTICLE = "lottery_article"  # 获取专栏文章
    
    # ==================== IP信息路由 ====================
    GET_IP = "get_ip"  # 获取IPv6地址信息
    
    # ==================== 后台服务路由 ====================
    # --- 爬虫状态获取 ---
    GET_DYNAMIC_SCRAPY_STATUS = "get_dynamic_scrapy_status"  # 动态爬虫状态
    GET_TOPIC_SCRAPY_STATUS = "get_topic_scrapy_status"  # 话题爬虫状态
    GET_RESERVE_SCRAPY_STATUS = "get_reserve_scrapy_status"  # 预约爬虫状态
    GET_ALL_SCRAPY_STATUS = "get_all_scrapy_status"  # 所有爬虫状态
    GET_OTHERS_LOT_SPACE_STATUS = "get_others_lot_space_status"  # 他人空间爬虫状态
    GET_OTHERS_LOT_DYN_STATUS = "get_others_lot_dyn_status"  # 他人动态爬虫状态
    GET_REFRESH_BILI_OFFICIAL_STATUS = "get_refresh_bili_official_status"  # 刷新官方抽奖状态
    GET_REFRESH_BILI_RESERVE_STATUS = "get_refresh_bili_reserve_status"  # 刷新预约抽奖状态
    GET_PROXY_STATUS = "get_proxy_status"  # 代理状态
    
    # --- 定时任务 ---
    GET_GLOBAL_JOBS = "get_global_jobs"  # 全局定时任务
    GET_GLOBAL_SCHEDULER_STATUS = "get_global_scheduler_status"  # 全局定时任务详细状态
    
    # --- 服务控制 ---
    GET_ALL_STAT = "all_stat"  # 后台服务状态
    START_SERVICE = "start_service"  # 启动服务
    STOP_SERVICE = "stop_service"  # 停止服务
    RESTART_SERVICE = "restart_service"  # 重启服务
    
    # ==================== 验证码路由 ====================
    GEN_CAPTCHA = "gen_captcha"  # 生成验证码
    VERIFY_CAPTCHA = "verify_captcha"  # 验证验证码
    
    # ==================== Sams Club路由 ====================
    SET_NEW_AUTH_TOKEN = "set_new_auth_token"  # 更新auth_token
    GRAPHQL = "graphql"  # GraphQL接口
    SAMSCLUB_API_STATUS = "samsclub_api_status"  # API状态
    
    # ==================== MQ测试路由 ====================
    RABBITMQ_TEST_PUBLISH = "rabbitmq_test_publish"  # RabbitMQ测试消息发布
    
    # ==================== 公共路由 ====================
    GET_LIVE_LOTS = "v1_get_live_lots"  # 获取直播抽奖
    TEST = "test"  # 服务可用性测试
    GC = "gc"  # 垃圾回收
    POST_RM_FOLLOWING_LIST = "v1_post_rm_following_list"  # 取关列表
    UPSERT_LOT_DETAIL = "upsert_lot_detail"  # 插入/更新抽奖详情
    GET_OTHERS_LOT_DYN = "get_others_lot_dyn"  # 获取他人动态抽奖
    GET_OTHERS_OFFICIAL_LOT_DYN = "get_others_official_lot_dyn"  # 获取他人官方动态抽奖
    GET_OTHERS_BIG_LOT = "get_others_big_lot"  # 获取他人大奖
    GET_OTHERS_BIG_RESERVE = "get_others_big_reserve"  # 获取重要预约抽奖
    ZHIHU_GET_OTHERS_LOT_PINS = "zhihu_get_others_lot_pins"  # 获取知乎抽奖
    TOUTIAO_GET_OTHERS_LOT_IDS = "toutiao_get_others_lot_ids"  # 获取头条抽奖


class RouterModule(StrEnum):
    """API路由模块枚举 - 用于标识路由所属的控制器模块"""
    
    DAMO = "controller.damo.DamoML"  # 达摩模块
    CHATGPT = "controller.v1.ChatGpt3_5.ReplySingle"  # ChatGPT模块
    LOTTERY_DATA = "controller.v1.lotttery_database.bili.LotteryData"  # 抽奖数据模块
    LOTTERY_STATISTIC = "controller.v1.lotttery_database.bili.lottery_statistic.LotteryStatistic"  # 抽奖统计模块
    ZHUILAN = "controller.v1.lotttery_database.bili.zhuanlan.zhuanlanController"  # 专栏模块
    IP_INFO = "controller.v1.ip_info.get_ip_info"  # IP信息模块
    BACKGROUND_SERVICE = "controller.v1.background_service.BackgroundServiceController"  # 后台服务模块
    MQ_CONTROLLER = "controller.v1.mq.mq_controller"  # MQ控制器模块
    COMMON = "controller.common.CommonRouter"  # 公共路由模块
    CAPTCHA = "controller.v1.captcha.captchaController"  # 验证码模块
    SAMS_CLUB = "controller.v1.samsClub.samsClubController"  # Sams Club模块
