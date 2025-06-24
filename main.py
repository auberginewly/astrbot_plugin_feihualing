import asyncio
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger


@register("feihualing", "auberginewly", "支持限时飞花令记分的 AstrBot 插件", "1.0.0")
class FeiHuaLingPlugin(Star):
    """飞花令插件

    支持多群/用户同时进行飞花令游戏，包含计时、积分、重复检测等功能
    """

    def __init__(self, context: Context):
        super().__init__(context)
        # 存储游戏状态的字典，key为group_id或user_id
        self.games: Dict[str, dict] = {}
        # 数据存储路径
        self.data_dir = os.path.join("data", "feihualing")
        self.scores_file = os.path.join(self.data_dir, "scores.json")
        self.last_game_file = os.path.join(self.data_dir, "last_game.json")

        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)

        # 加载历史数据
        self.load_data()

    async def initialize(self):
        """插件初始化"""
        logger.info("飞花令插件初始化完成")

    def load_data(self):
        """加载持久化数据"""
        try:
            # 加载积分数据
            if os.path.exists(self.scores_file):
                with open(self.scores_file, "r", encoding="utf-8") as f:
                    self.all_scores = json.load(f)
            else:
                self.all_scores = {}

            # 加载最近一局游戏数据
            if os.path.exists(self.last_game_file):
                with open(self.last_game_file, "r", encoding="utf-8") as f:
                    self.last_games = json.load(f)
            else:
                self.last_games = {}

        except Exception as e:
            logger.error(f"加载飞花令数据失败: {e}")
            self.all_scores = {}
            self.last_games = {}

    def save_data(self):
        """保存持久化数据"""
        try:
            with open(self.scores_file, "w", encoding="utf-8") as f:
                json.dump(self.all_scores, f, ensure_ascii=False, indent=2)

            with open(self.last_game_file, "w", encoding="utf-8") as f:
                json.dump(self.last_games, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存飞花令数据失败: {e}")

    def get_session_id(self, event: AstrMessageEvent) -> str:
        """获取会话ID，用于区分不同的聊天环境"""
        if hasattr(event, "group_id") and event.group_id:
            return f"group_{event.group_id}"
        else:
            return f"user_{event.get_sender_id()}"

    def is_valid_poem(self, text: str) -> bool:
        """基础诗句有效性检查"""
        if not text:
            return False

        # 去除标点符号和空格
        cleaned_text = re.sub(r"[^\u4e00-\u9fff]", "", text)

        # 检查长度（一般诗句3-20字）
        if len(cleaned_text) < 3 or len(cleaned_text) > 20:
            return False

        # 检查是否全是汉字
        if not re.match(r"^[\u4e00-\u9fff]+$", cleaned_text):
            return False

        # 排除明显不是诗句的内容
        # 1. 排除纯数字组合
        if re.match(r"^[一二三四五六七八九十百千万零]+$", cleaned_text):
            return False

        # 2. 排除太多重复字符
        if len(set(cleaned_text)) < max(1, len(cleaned_text) // 3):
            return False

        # 3. 排除常见的非诗句短语
        non_poem_phrases = [
            "哈哈哈",
            "呵呵呵",
            "嘿嘿嘿",
            "好的好的",
            "知道了",
            "明白了",
            "收到收到",
            "没问题",
            "可以的",
            "谢谢谢",
            "不客气",
            "再见再见",
        ]
        if cleaned_text in non_poem_phrases:
            return False

        return True

    def contains_target_char(self, text: str, target_char: str) -> bool:
        """检查文本中是否包含指定令字"""
        return target_char in text

    @filter.command("feihualing")
    async def start_feihualing(self, event: AstrMessageEvent):
        """启动飞花令游戏

        指令格式：/feihualing <时间(分钟)> <令字>
        示例：/feihualing 2 月
        """
        try:
            session_id = self.get_session_id(event)

            # 检查是否已有游戏在进行
            if session_id in self.games:
                yield event.plain_result("飞花令游戏正在进行中，请等待本轮结束！")
                return

            # 解析命令参数
            args = event.message_str.strip().split()
            if len(args) != 3:
                yield event.plain_result(
                    "指令格式错误！\n"
                    "正确格式：/feihualing <时间(分钟)> <令字>\n"
                    "示例：/feihualing 2 月"
                )
                return

            try:
                duration = int(args[1])
            except ValueError:
                yield event.plain_result("时间必须是数字！例如：/feihualing 2 月")
                return

            if duration <= 0 or duration > 60:
                yield event.plain_result("时间必须是1-60分钟之间的数字！")
                return

            target_char = args[2]
            if len(target_char) != 1 or not re.match(r"[\u4e00-\u9fff]", target_char):
                yield event.plain_result("令字必须是单个汉字！例如：/feihualing 2 月")
                return

            # 初始化游戏状态
            end_time = datetime.now() + timedelta(minutes=duration)
            self.games[session_id] = {
                "target_char": target_char,
                "duration": duration,
                "start_time": datetime.now(),
                "end_time": end_time,
                "participants": {},  # {user_id: score}
                "used_poems": set(),  # 本轮已使用的诗句
                "is_active": True,
                "end_message": None,  # 游戏结束消息
            }

            # 启动游戏定时器
            asyncio.create_task(self.game_timer(session_id, event))

            yield event.plain_result(
                f"🌸 飞花令游戏开始！🌸\n"
                f"令字：【{target_char}】\n"
                f"时间：{duration} 分钟\n"
                f"请在群内回复包含令字『{target_char}』的诗句！\n"
                f"每人每次只能回答一条诗句，每句得1分！"
            )

        except Exception as e:
            logger.error(f"启动飞花令游戏失败: {e}")
            yield event.plain_result("启动游戏失败，请稍后重试！")

    async def game_timer(self, session_id: str, original_event: AstrMessageEvent):
        """游戏计时器"""
        try:
            game = self.games.get(session_id)
            if not game:
                return

            # 等待游戏结束时间
            while datetime.now() < game["end_time"] and game["is_active"]:
                await asyncio.sleep(5)  # 每5秒检查一次，提高响应速度

            # 游戏结束 - 直接生成并保存结束消息，标记游戏为待结束状态
            if session_id in self.games and self.games[session_id]["is_active"]:
                result_message = await self.end_game(session_id)
                if result_message:
                    # 标记游戏已结束，等待发送消息
                    self.games[session_id] = {
                        "is_active": False,
                        "end_message": result_message,
                        "end_time_reached": True,
                    }

        except Exception as e:
            logger.error(f"游戏计时器异常: {e}")

    async def end_game(self, session_id: str):
        """结束游戏并保存结果"""
        try:
            game = self.games.get(session_id)
            if not game:
                return None

            game["is_active"] = False

            # 保存当局游戏数据到历史记录
            game_record = {
                "target_char": game["target_char"],
                "duration": game["duration"],
                "start_time": game["start_time"].isoformat(),
                "end_time": game["end_time"].isoformat(),
                "participants": game["participants"].copy(),
                "poems_count": len(game["used_poems"]),
            }
            self.last_games[session_id] = game_record

            # 更新总积分
            if session_id not in self.all_scores:
                self.all_scores[session_id] = {}

            for user_id, score in game["participants"].items():
                if user_id not in self.all_scores[session_id]:
                    self.all_scores[session_id][user_id] = 0
                self.all_scores[session_id][user_id] += score

            # 保存已使用的诗句到全局记录 - 移除这部分，改为只在本局内检测
            # if session_id not in self.all_used_poems:
            #     self.all_used_poems[session_id] = []
            # self.all_used_poems[session_id].extend(list(game["used_poems"]))

            # 保存数据
            self.save_data()

            # 生成积分榜
            result_message = "⏰ 时间到！飞花令游戏结束！\n\n"
            result_message += f"本轮令字：【{game['target_char']}】\n"
            result_message += f"游戏时长：{game['duration']} 分钟\n\n"

            if game["participants"]:
                result_message += "🏆 本局积分榜：\n"
                sorted_participants = sorted(
                    game["participants"].items(), key=lambda x: x[1], reverse=True
                )

                for i, (user_id, score) in enumerate(sorted_participants, 1):
                    # 尝试获取用户昵称，如果失败则使用用户ID
                    try:
                        user_name = f"用户{user_id}"  # 这里可以进一步优化获取真实用户名
                    except Exception:
                        user_name = f"用户{user_id}"

                    medal = (
                        "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
                    )
                    result_message += f"{medal} {i}. {user_name}: {score} 分\n"

                result_message += (
                    f"\n📖 总共收集了 {len(game['used_poems'])} 句诗词！\n"
                )
                result_message += "输入 /feihualing_last 可查看本局详细排名"
            else:
                result_message += "😔 本轮无人参与，下次加油！"

            # 不立即清理游戏状态，保留结束消息
            # del self.games[session_id]

            return result_message

        except Exception as e:
            logger.error(f"结束游戏失败: {e}")
            if session_id in self.games:
                del self.games[session_id]
            return None

    @filter.regex(r".*")
    async def handle_poem(self, event: AstrMessageEvent):
        """处理诗句回答"""
        try:
            session_id = self.get_session_id(event)

            # 优先检查是否有待发送的结束消息
            if session_id in self.games:
                game = self.games[session_id]
                if not game.get("is_active", True) and game.get("end_message"):
                    end_message = game["end_message"]
                    del self.games[session_id]  # 清理游戏状态
                    yield event.plain_result(end_message)
                    return

            # 跳过所有命令消息（必须在游戏检查之前）
            message_text = event.message_str.strip()
            if message_text.startswith("/"):
                return

            # 检查是否有正在进行的游戏
            if session_id not in self.games:
                return

            game = self.games[session_id]
            if not game.get("is_active", False):
                return

            # 检查游戏是否超时
            if datetime.now() >= game["end_time"]:
                result_message = await self.end_game(session_id)
                if result_message:
                    del self.games[session_id]  # 清理游戏状态
                    yield event.plain_result(result_message)
                return

            user_id = event.get_sender_id()
            user_name = event.get_sender_name()
            poem_text = message_text

            # 再次检查是否是命令（防止意外处理）
            if (
                poem_text.startswith("/")
                or poem_text.startswith("!")
                or poem_text.startswith("#")
            ):
                return

            # 检查诗句有效性
            if not self.is_valid_poem(poem_text):
                # 静默忽略无效诗句，不给出提示，避免对正常聊天的干扰
                return

            # 检查是否包含令字
            if not self.contains_target_char(poem_text, game["target_char"]):
                yield event.plain_result(
                    f"{user_name}，诗句中不含令字『{game['target_char']}』！"
                )
                return

            # 检查诗句是否重复（仅检查本轮）
            cleaned_poem = re.sub(r"[^\u4e00-\u9fff]", "", poem_text)

            # 检查本轮是否已使用
            if cleaned_poem in game["used_poems"]:
                yield event.plain_result(f"{user_name}，该诗句本轮已被使用过！")
                return

            # 添加诗句到已使用列表
            game["used_poems"].add(cleaned_poem)

            # 更新玩家得分
            if user_id not in game["participants"]:
                game["participants"][user_id] = 0
            game["participants"][user_id] += 1

            # 计算剩余时间
            remaining_time = game["end_time"] - datetime.now()
            remaining_minutes = int(remaining_time.total_seconds() / 60)
            remaining_seconds = int(remaining_time.total_seconds() % 60)

            time_str = (
                f"{remaining_minutes}分{remaining_seconds}秒"
                if remaining_minutes > 0
                else f"{remaining_seconds}秒"
            )

            yield event.plain_result(
                f"✅ {user_name} 得 1 分！\n"
                f"当前得分：{game['participants'][user_id]} 分\n"
                f"剩余时间：{time_str}"
            )

        except Exception as e:
            logger.error(f"处理诗句回答失败: {e}")

    @filter.command("feihualing_score")
    async def show_scores(self, event: AstrMessageEvent):
        """显示总积分榜（当前会话）"""
        try:
            session_id = self.get_session_id(event)

            # 检查是否有待发送的结束消息
            if session_id in self.games:
                game = self.games[session_id]
                if not game.get("is_active", True) and game.get("end_message"):
                    end_message = game["end_message"]
                    del self.games[session_id]  # 清理游戏状态
                    yield event.plain_result(end_message)
                    return

            if session_id not in self.all_scores:
                yield event.plain_result("暂无积分记录！")
                return

            scores = self.all_scores[session_id]
            if not scores:
                yield event.plain_result("暂无积分记录！")
                return

            # 确定是群聊还是私聊
            chat_type = "群聊" if session_id.startswith("group_") else "私聊"

            result = f"🏆 飞花令总积分榜 ({chat_type}) 🏆\n\n"
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

            for i, (user_id, score) in enumerate(sorted_scores, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
                result += f"{medal} {i}. 用户{user_id}: {score} 分\n"

            result += "\n💡 输入 /feihualing_last 查看最近一局排名"

            yield event.plain_result(result)

        except Exception as e:
            logger.error(f"显示积分榜失败: {e}")
            yield event.plain_result("获取积分榜失败！")

    @filter.command("feihualing_stop")
    async def stop_game(self, event: AstrMessageEvent):
        """强制停止当前游戏"""
        try:
            session_id = self.get_session_id(event)

            if session_id not in self.games:
                yield event.plain_result("当前没有进行中的飞花令游戏！")
                return

            result_message = await self.end_game(session_id)
            if result_message:
                del self.games[session_id]  # 清理游戏状态
                yield event.plain_result(result_message)
            else:
                if session_id in self.games:
                    del self.games[session_id]
                yield event.plain_result("飞花令游戏已强制结束！")

        except Exception as e:
            logger.error(f"停止游戏失败: {e}")
            yield event.plain_result("停止游戏失败！")

    @filter.command("feihualing_help")
    async def show_help(self, event: AstrMessageEvent):
        """显示帮助信息"""
        try:
            session_id = self.get_session_id(event)

            # 检查是否有待发送的结束消息
            if session_id in self.games:
                game = self.games[session_id]
                if not game.get("is_active", True) and game.get("end_message"):
                    end_message = game["end_message"]
                    del self.games[session_id]  # 清理游戏状态
                    yield event.plain_result(end_message)
                    return

            help_text = """🌸 飞花令插件帮助 🌸

🎮 游戏指令：
/feihualing <时间> <令字> - 开始游戏
  示例：/feihualing 2 月

📊 查询指令：
/feihualing_score - 查看总积分榜
/feihualing_last - 查看最近一局排名
/feihualing_stop - 强制结束游戏
/feihualing_help - 显示此帮助

🎯 游戏规则：
1. 回复包含令字的诗句即可得分
2. 每人每次只能回答一条诗句
3. 同一局内不能重复使用诗句
4. 每局结束后重新开始，可重复之前用过的诗句
5. 时间结束后自动公布结果

⚠️ 注意事项：
- 诗句长度3-20字
- 必须包含指定令字
- 单局内不能重复使用诗句
- 不同群/用户的积分分别统计
- 游戏进行中，普通聊天不会被识别为诗句
"""
            yield event.plain_result(help_text)

        except Exception as e:
            logger.error(f"显示帮助失败: {e}")
            yield event.plain_result("显示帮助失败！")

    @filter.command("feihualing_last")
    async def show_last_game(self, event: AstrMessageEvent):
        """显示最近一局的详细排名"""
        try:
            session_id = self.get_session_id(event)

            # 检查是否有待发送的结束消息
            if session_id in self.games:
                game = self.games[session_id]
                if not game.get("is_active", True) and game.get("end_message"):
                    end_message = game["end_message"]
                    del self.games[session_id]  # 清理游戏状态
                    yield event.plain_result(end_message)
                    return

            if session_id not in self.last_games:
                yield event.plain_result("暂无最近一局的游戏记录！")
                return

            last_game = self.last_games[session_id]

            # 解析时间
            start_time = datetime.fromisoformat(last_game["start_time"])

            # 确定是群聊还是私聊
            chat_type = "群聊" if session_id.startswith("group_") else "私聊"

            result = f"📋 最近一局飞花令详情 ({chat_type}) 📋\n\n"
            result += f"令字：【{last_game['target_char']}】\n"
            result += f"时长：{last_game['duration']} 分钟\n"
            result += f"开始时间：{start_time.strftime('%m-%d %H:%M')}\n"
            result += f"诗句总数：{last_game['poems_count']} 句\n\n"

            participants = last_game["participants"]
            if participants:
                result += "🏆 本局排名：\n"
                sorted_participants = sorted(
                    participants.items(), key=lambda x: x[1], reverse=True
                )

                for i, (user_id, score) in enumerate(sorted_participants, 1):
                    medal = (
                        "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
                    )
                    result += f"{medal} {i}. 用户{user_id}: {score} 分\n"
            else:
                result += "😔 本局无人参与"

            yield event.plain_result(result)

        except Exception as e:
            logger.error(f"显示最近一局失败: {e}")
            yield event.plain_result("获取最近一局数据失败！")

    async def terminate(self):
        """插件销毁时的清理工作"""
        # 结束所有进行中的游戏
        for session_id in list(self.games.keys()):
            if self.games[session_id]["is_active"]:
                self.games[session_id]["is_active"] = False

        # 保存数据
        self.save_data()
        logger.info("飞花令插件已停止")
