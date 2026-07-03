"""B站动态详情解析模块

从 get_other_lot_main.py 中拆分出来的动态详情解析逻辑。
将原先 __solve_dynamic_item_detail 方法中深度嵌套的 dict.get() 链
优化为一次性提取中间变量，减少重复查找开销。
"""
import datetime
from typing import Any

from log.base_log import get_others_lot_logger as get_others_lot_log
from Service.GetOthersLotDyn.parser.dynamic_detail_parsed import DynamicDetailParsed
from Utils.通用.dynamic_id_caculate import dynamic_id_2_ts


def _safe_get(d: dict | None, *keys, default=None):
    """安全的多层嵌套 dict 取值

    :param d: 起始字典
    :param keys: 逐层键名
    :param default: 取不到时的默认值
    :return: 取到的值或 default
    """
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def _extract_dynamic_content(module_dynamic: dict) -> str:
    """从 module_dynamic 中提取正文文本（desc.text + major 文本）

    优化：一次性取出 module_dynamic 子节点，避免重复 .get() 链
    """
    if not module_dynamic:
        return ''
    parts: list[str] = []

    # desc.text
    desc = module_dynamic.get('desc')
    if desc and desc.get('text'):
        parts.append(desc['text'])

    # major 下的 archive / article / opus 文本
    major = module_dynamic.get('major')
    if major:
        archive = major.get('archive')
        if archive:
            desc_text = archive.get('desc') or ''
            title = archive.get('title') or ''
            parts.append(desc_text + title)

        article = major.get('article')
        if article:
            desc_text = str(article.get('desc') or '')
            title = article.get('title') or ''
            parts.append(desc_text + title)

        opus = major.get('opus')
        if opus:
            summary = opus.get('summary')
            if summary and summary.get('text'):
                parts.append(summary['text'])
            title = opus.get('title')
            if title:
                parts.append(title)

    return ''.join(parts)


def _extract_stats(module_stat: dict) -> tuple[int, int, int]:
    """从 module_stat 中提取评论数、转发数、点赞数

    :return: (comment_count, forward_count, like_count)，失败返回 (-1, -1, -1)
    """
    if not module_stat:
        return -1, -1, -1
    comment_count = _safe_get(module_stat, 'comment', 'count', default=-1)
    forward_count = _safe_get(module_stat, 'forward', 'count', default=-1)
    like_count = _safe_get(module_stat, 'like', 'count', default=-1)
    return comment_count, forward_count, like_count


def _extract_official_verify(module_author: dict) -> int:
    """从 module_author 中提取官方认证类型

    :return: 认证类型 int，失败返回 -1
    """
    try:
        ov = module_author.get('official_verify')
        if ov is None:
            # 部分响应直接在 module_author 下放 type
            return 1 if isinstance(module_author.get('type'), str) else -1
        return ov.get('type')
    except Exception:
        return -1


def _comment_type_to_dynamic_type(comment_type: Any) -> str:
    """将 comment_type 映射为内部动态类型字符串

    '17' -> '4' (转发)
    '1'  -> '8' (视频)
    '11' -> '2' (图片)
    '12' -> '64'(文章)
    """
    ct = str(comment_type)
    return {
        '17': '4',
        '1': '8',
        '11': '2',
        '12': '64',
    }.get(ct, '8')


def _parse_orig_dynamic(orig_item: dict | None) -> dict:
    """解析转发动态的原动态信息

    优化：复用 _extract_dynamic_content 和 _safe_get，减少重复代码

    :return: 包含 orig_* 字段的 dict，非转发动态返回全 None
    """
    if not orig_item:
        return {}

    modules = orig_item.get('modules') or {}
    module_author = modules.get('module_author') or {}
    module_dynamic = modules.get('module_dynamic') or {}
    module_stat = modules.get('module_stat') or {}

    orig_dynamic_content = _extract_dynamic_content(module_dynamic)

    # 原动态互动数据（评论/转发/点赞）
    orig_comment_count, orig_forward_count, orig_like_count = _extract_stats(module_stat)

    orig_official_verify = -1
    ov = module_author.get('official_verify')
    if ov and isinstance(ov, dict):
        orig_official_verify = ov.get('type', -1)
    elif isinstance(module_author.get('type'), str):
        orig_official_verify = 1

    orig_relation = module_author.get('following')
    orig_relation = 1 if orig_relation else 0

    return {
        'orig_dynamic_id': orig_item.get('id_str'),
        'dynamic_orig': orig_item,
        'orig_mid': module_author.get('mid'),
        'orig_name': module_author.get('name'),
        'orig_pub_ts': module_author.get('pub_ts'),
        'orig_official_verify': orig_official_verify,
        'orig_comment_count': orig_comment_count,
        'orig_forward_count': orig_forward_count,
        'orig_like_count': orig_like_count,
        'orig_dynamic_content': orig_dynamic_content,
        'orig_relation': orig_relation,
        'orig_desc': module_dynamic.get('desc'),
    }


def parse_dynamic_item(dynamic_id: str | int, dynamic_detail_resp: dict) -> DynamicDetailParsed:
    """解析单个动态详情响应，提取所有字段

    从 __solve_dynamic_item_detail 中提取的核心解析逻辑。
    不包含网络重试逻辑（412/None 等），仅做纯数据解析。

    :param dynamic_id: 期望的动态 ID（用于校验）
    :param dynamic_detail_resp: 动态详情 API 响应 dict
    :return: DynamicDetailParsed 解析结果
    """
    # 动态不存在
    if dynamic_detail_resp.get('code') == 4101131 or dynamic_detail_resp.get('data') is None:
        get_others_lot_log.info(f'动态已被删除或不存在，dynamic_id={dynamic_id}，code={dynamic_detail_resp.get("code")}')
        return DynamicDetailParsed()

    dynamic_data = dynamic_detail_resp.get('data') or {}
    dynamic_item = dynamic_data.get('item')
    if not dynamic_item:
        return DynamicDetailParsed()

    # ---- 一次性提取 modules 及其子模块，避免后续重复 .get('modules') ----
    modules = dynamic_item.get('modules') or {}
    module_author = modules.get('module_author') or {}
    module_dynamic = modules.get('module_dynamic') or {}
    module_stat = modules.get('module_stat') or {}
    module_tag = modules.get('module_tag')

    basic = dynamic_item.get('basic') or {}
    comment_type = basic.get('comment_type')
    dynamic_type = _comment_type_to_dynamic_type(comment_type)
    card_stype = dynamic_item.get('type')
    dynamic_data_dynamic_id = dynamic_item.get('id_str')

    # 动态 ID 不匹配校验（仅图片类型需要严格校验）
    if (str(dynamic_type) == '2'
            and str(dynamic_data_dynamic_id) != str(dynamic_id)):
        get_others_lot_log.critical(
            f"API返回的动态ID({dynamic_data_dynamic_id})与期望的动态ID({dynamic_id})不匹配，图片类型动态需要严格校验，将重新获取\ndata={dynamic_data}")
        return DynamicDetailParsed()  # 调用方负责重新获取

    dynamic_rid = basic.get('comment_id_str')

    # ---- 作者信息 ----
    relation = module_author.get('following')
    relation = 1 if relation else 0
    author_uid = module_author.get('mid')
    author_name = module_author.get('name')
    pub_ts = module_author.get('pub_ts')

    # 发布时间字符串：优先用 dynamic_id 推算（避免番剧等特殊响应取不到）
    if dynamic_data_dynamic_id:
        pub_time = datetime.datetime.fromtimestamp(
            dynamic_id_2_ts(dynamic_data_dynamic_id)).strftime('%Y年%m月%d日 %H:%M')
    else:
        pub_time = datetime.datetime.fromtimestamp(100000).strftime('%Y年%m月%d日 %H:%M')

    official_verify_type = _extract_official_verify(module_author)

    # ---- 互动数据 ----
    comment_count, forward_count, like_count = _extract_stats(module_stat)

    # ---- 正文内容 ----
    dynamic_content = _extract_dynamic_content(module_dynamic)
    desc = module_dynamic.get('desc')
    # ---- 置顶判断 ----
    top_dynamic = None
    if module_tag:
        module_tag_text = module_tag.get('text')
        if module_tag_text == "置顶":
            top_dynamic = True
        else:
            get_others_lot_log.critical(f'遇到未知的动态标签(module_tag)，当前仅支持"置顶"，tag内容={module_tag}')
    else:
        top_dynamic = False

    # ---- 转发动态的原动态 ----
    dynamic_orig = dynamic_item.get('orig')
    orig_fields = _parse_orig_dynamic(dynamic_orig)
    if not orig_fields:
        get_others_lot_log.debug('当前动态非转发动态，无原动态信息')

    return DynamicDetailParsed(
        rawJSON=dynamic_item,
        dynamic_id=dynamic_data_dynamic_id,
        dynamic_item=dynamic_item,
        desc=desc,
        type=dynamic_type,
        rid=dynamic_rid,
        relation=relation,
        is_liked=0,
        author_uid=author_uid,
        author_name=author_name,
        comment_count=comment_count,
        forward_count=forward_count,
        like_count=like_count,
        dynamic_content=dynamic_content,
        pub_time=pub_time,
        pub_ts=pub_ts,
        official_verify_type=official_verify_type,
        module_dynamic=module_dynamic,
        card_stype=card_stype,
        top_dynamic=top_dynamic,
        **orig_fields,
    )
