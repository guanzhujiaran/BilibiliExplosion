"""一次性为各语言 .po 填充 msgstr 翻译（仅开发期使用，可删除）。"""
import re
from pathlib import Path

LOCALE_DIR = Path("bili_common/locale")

# 翻译映射：中文原文 -> {语言: 翻译}
TR = {
    "uid 格式非法: {uid}": {
        "en": "Invalid uid format: {uid}",
        "zh_TW": "uid 格式非法: {uid}",
        "ja": "uid の形式が不正です: {uid}",
        "ko": "uid 형식이 잘못되었습니다: {uid}",
    },
    "uid 格式非法": {
        "en": "Invalid uid format",
        "zh_TW": "uid 格式非法",
        "ja": "uid の形式が不正です",
        "ko": "uid 형식이 잘못되었습니다",
    },
    "mid 格式非法: {mid}": {
        "en": "Invalid mid format: {mid}",
        "zh_TW": "mid 格式非法: {mid}",
        "ja": "mid の形式が不正です: {mid}",
        "ko": "mid 형식이 잘못되었습니다: {mid}",
    },
    "mid 格式非法": {
        "en": "Invalid mid format",
        "zh_TW": "mid 格式非法",
        "ja": "mid の形式が不正です",
        "ko": "mid 형식이 잘못되었습니다",
    },
    "请求参数校验失败": {
        "en": "Request parameter validation failed",
        "zh_TW": "請求參數校驗失敗",
        "ja": "リクエストパラメータの検証に失敗しました",
        "ko": "요청 파라미터 검증에 실패했습니다",
    },
    "服务器内部错误 (错误ID: {error_id})": {
        "en": "Internal server error (Error ID: {error_id})",
        "zh_TW": "伺服器內部錯誤 (錯誤ID: {error_id})",
        "ja": "サーバー内部エラー (エラーID: {error_id})",
        "ko": "서버 내부 오류 (오류 ID: {error_id})",
    },
    "仅管理员可执行该操作": {
        "en": "Only administrators can perform this operation",
        "zh_TW": "僅管理員可執行該操作",
        "ja": "管理者のみがこの操作を実行できます",
        "ko": "관리자만 이 작업을 수행할 수 있습니다",
    },
    "仅 root 管理员可执行该操作": {
        "en": "Only root administrators can perform this operation",
        "zh_TW": "僅 root 管理員可執行該操作",
        "ja": "root 管理者のみがこの操作を実行できます",
        "ko": "root 관리자만 이 작업을 수행할 수 있습니다",
    },
    "需要管理员权限": {
        "en": "Administrator permission required",
        "zh_TW": "需要管理員權限",
        "ja": "管理者権限が必要です",
        "ko": "관리자 권한이 필요합니다",
    },
    "权限不足": {
        "en": "Insufficient permissions",
        "zh_TW": "權限不足",
        "ja": "権限が不足しています",
        "ko": "권한이 부족합니다",
    },
    "浏览器通知配置不存在": {
        "en": "Browser notification configuration does not exist",
        "zh_TW": "瀏覽器通知配置不存在",
        "ja": "ブラウザ通知設定が存在しません",
        "ko": "브라우저 알림 설정이 존재하지 않습니다",
    },
    "浏览器ID不能为空~": {
        "en": "Browser ID cannot be empty~",
        "zh_TW": "瀏覽器ID不能為空~",
        "ja": "ブラウザIDは空にできません~",
        "ko": "브라우저 ID는 비워둘 수 없습니다~",
    },
    "浏览器ID {browser_id} 不属于当前用户或不存在": {
        "en": "Browser ID {browser_id} does not belong to the current user or does not exist",
        "zh_TW": "瀏覽器ID {browser_id} 不屬於當前用戶或不存在",
        "ja": "ブラウザID {browser_id} は現在のユーザーに属していないか存在しません",
        "ko": "브라우저 ID {browser_id} 는 현재 사용자에 속하지 않거나 존재하지 않습니다",
    },
    "未登录，请提供有效的x-bili-mid请求头": {
        "en": "Not logged in, please provide a valid x-bili-mid header",
        "zh_TW": "未登入，請提供有效的x-bili-mid請求頭",
        "ja": "未ログインです。有効な x-bili-mid ヘッダーを提供してください",
        "ko": "로그인되지 않았습니다. 유효한 x-bili-mid 헤더를 제공해 주세요",
    },
    "无效的用户ID，请重新登录": {
        "en": "Invalid user ID, please log in again",
        "zh_TW": "無效的用戶ID，請重新登入",
        "ja": "無効なユーザーIDです。再度ログインしてください",
        "ko": "유효하지 않은 사용자 ID입니다. 다시 로그인해 주세요",
    },
    "Invalid mid format in x-bili-mid header": {
        "en": "Invalid mid format in x-bili-mid header",
        "zh_TW": "Invalid mid format in x-bili-mid header",
        "ja": "Invalid mid format in x-bili-mid header",
        "ko": "Invalid mid format in x-bili-mid header",
    },
    "插件ID不能为空": {
        "en": "Plugin ID cannot be empty",
        "zh_TW": "插件ID不能為空",
        "ja": "プラグインIDは空にできません",
        "ko": "플러그인 ID는 비워둘 수 없습니다",
    },
    "插件ID {plugin_id} 不属于当前用户或不存在": {
        "en": "Plugin ID {plugin_id} does not belong to the current user or does not exist",
        "zh_TW": "插件ID {plugin_id} 不屬於當前用戶或不存在",
        "ja": "プラグインID {plugin_id} は現在のユーザーに属していないか存在しません",
        "ko": "플러그인 ID {plugin_id} 는 현재 사용자에 속하지 않거나 존재하지 않습니다",
    },
    "浏览器未启动或已停止": {
        "en": "Browser not started or already stopped",
        "zh_TW": "瀏覽器未啟動或已停止",
        "ja": "ブラウザが起動していないか既に停止しています",
        "ko": "브라우저가 시작되지 않았거나 이미 중지되었습니다",
    },
    "页面索引 {page_index} 无效": {
        "en": "Page index {page_index} is invalid",
        "zh_TW": "頁面索引 {page_index} 無效",
        "ja": "ページインデックス {page_index} が無効です",
        "ko": "페이지 인덱스 {page_index} 가 유효하지 않습니다",
    },
    "视频流初始化失败: {error}": {
        "en": "Video stream initialization failed: {error}",
        "zh_TW": "視頻流初始化失敗: {error}",
        "ja": "ビデオストリームの初期化に失敗しました: {error}",
        "ko": "비디오 스트림 초기화 실패: {error}",
    },
    "获取浏览器会话失败: {error}": {
        "en": "Failed to get browser session: {error}",
        "zh_TW": "獲取瀏覽器會話失敗: {error}",
        "ja": "ブラウザセッションの取得に失敗しました: {error}",
        "ko": "브라우저 세션 가져오기 실패: {error}",
    },
    "获取浏览器信息失败: {error}": {
        "en": "Failed to get browser info: {error}",
        "zh_TW": "獲取瀏覽器資訊失敗: {error}",
        "ja": "ブラウザ情報の取得に失敗しました: {error}",
        "ko": "브라우저 정보 가져오기 실패: {error}",
    },
    "WebRTC 流未激活": {
        "en": "WebRTC stream not active",
        "zh_TW": "WebRTC 流未激活",
        "ja": "WebRTC ストリームがアクティブではありません",
        "ko": "WebRTC 스트림이 활성화되지 않았습니다",
    },
    "B站登录失败": {
        "en": "Bilibili login failed",
        "zh_TW": "B站登入失敗",
        "ja": "Bilibili ログイン失敗",
        "ko": "Bilibili 로그인 실패",
    },
    "浏览器指纹不存在": {
        "en": "Browser fingerprint does not exist",
        "zh_TW": "瀏覽器指紋不存在",
        "ja": "ブラウザフィンガープリントが存在しません",
        "ko": "브라우저 지문이 존재하지 않습니다",
    },
    "已达到最大指纹数量限制，当前等级最多可创建 {max} 个指纹": {
        "en": "Maximum fingerprint limit reached, current level allows at most {max} fingerprints",
        "zh_TW": "已達到最大指紋數量限制，當前等級最多可建立 {max} 個指紋",
        "ja": "最大フィンガープリント数に達しました。現在のレベルでは最大 {max} 個まで作成可能です",
        "ko": "최대 지문 수 제한에 도달했습니다. 현재 등급에서는 최대 {max} 개의 지문을 생성할 수 있습니다",
    },
}


def fill_po(lang: str, path: Path):
    text = path.read_text(encoding="utf-8")
    for src, langs in TR.items():
        tgt = langs.get(lang, "")
        # 转义 po 特殊字符
        tgt_esc = tgt.replace("\\", "\\\\").replace('"', '\\"')
        # 匹配 msgid "...src..." 后紧跟的 msgstr ""
        pattern = re.compile(
            r'(msgid "' + re.escape(src) + r'"\n)msgstr ""',
            re.MULTILINE,
        )
        text, n = pattern.subn(lambda m: m.group(1) + f'msgstr "{tgt_esc}"', text)
        if n == 0:
            print(f"  [WARN] {lang}: 未找到 msgid: {src}")
    path.write_text(text, encoding="utf-8")
    print(f"[OK] {lang} 填充完成")


if __name__ == "__main__":
    for lang in ["en", "zh_TW", "ja", "ko"]:
        p = LOCALE_DIR / lang / "LC_MESSAGES" / "messages.po"
        print(f"填充 {lang} ...")
        fill_po(lang, p)
    print("全部完成（zh_CN 默认留空，回退原文）")
