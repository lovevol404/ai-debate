"""Debate engine using LangChain for AI Debate platform."""
import asyncio
import logging
import json
from datetime import datetime
from typing import Callable, Optional, AsyncGenerator, Awaitable, List, Dict
from sqlalchemy.orm import Session

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from .. import models, crud

# Configure logger - inherit from root logger
logger = logging.getLogger("debate.engine")


# Default debate phases (used when topic has no round_config)
DEFAULT_DEBATE_PHASES = [
    {"name": "立论", "rounds": 1, "description": "开篇立论，阐述己方观点"},
    {"name": "驳论", "rounds": 1, "description": "反驳对方观点，指出对方漏洞"},
    {"name": "自由辩论", "rounds": 2, "description": "自由交锋，深入辩论"},
    {"name": "总结", "rounds": 1, "description": "总结陈词，强调己方优势"},
]

# Default task configuration
DEFAULT_TASK_CONFIG = {
    "pro_system_prompt": """你是一位专业的辩论选手，代表正方（支持方）参与辩论。
你的任务是：
1. 清晰、有力地阐述正方观点
2. 用逻辑和事实支持你的论点
3. 指出反方观点的漏洞和矛盾
4. 保持礼貌但坚定的语气
5. 每轮发言控制在 200-300 字之间

请记住，你代表正方，需要始终支持辩题的正面立场。""",
    "con_system_prompt": """你是一位专业的辩论选手，代表反方（反对方）参与辩论。
你的任务是：
1. 清晰、有力地阐述反方观点
2. 用逻辑和事实支持你的论点
3. 指出正方观点的漏洞和矛盾
4. 保持礼貌但坚定的语气
5. 每轮发言控制在 200-300 字之间

请记住，你代表反方，需要始终反对辩题的正面立场。""",
    "max_words_per_round": 300,
    "temperature": 0.7,
}


class DebateEngine:
    """Debate engine that manages LLM-based debates."""

    def __init__(self, db: Session):
        self.db = db
        self._abort_flags: dict[int, bool] = {}

    def get_debate_phases(self, record: models.DebateRecord) -> List[Dict]:
        """Get debate phases from topic round_config or use default."""
        if record.topic and record.topic.round_config:
            try:
                phases = json.loads(record.topic.round_config)
                if isinstance(phases, list) and len(phases) > 0:
                    logger.debug(f"使用辩题自定义轮次配置：{phases}")
                    return phases
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"解析 round_config 失败，使用默认配置：{e}")
        logger.debug("使用默认轮次配置")
        return DEFAULT_DEBATE_PHASES

    def get_task_config(self, record: models.DebateRecord) -> Dict:
        """Get task config from topic or use default."""
        config = DEFAULT_TASK_CONFIG.copy()

        if record.topic and record.topic.task_config:
            try:
                topic_config = json.loads(record.topic.task_config)
                if isinstance(topic_config, dict):
                    # Merge topic config with default config
                    config.update(topic_config)
                    logger.debug(f"使用辩题自定义任务配置：{config}")
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"解析 task_config 失败，使用默认配置：{e}")
        else:
            logger.debug("使用默认任务配置")

        return config

    def abort_debate(self, record_id: int) -> None:
        """Signal to abort a debate."""
        self._abort_flags[record_id] = True

    def is_aborted(self, record_id: int) -> bool:
        """Check if a debate has been aborted."""
        return self._abort_flags.get(record_id, False)

    def _create_llm(self, config: models.LLMConfig) -> ChatOpenAI:
        """Create a ChatOpenAI instance from config."""
        logger.debug(f"创建 LLM 实例: model={config.model_name}, base_url={config.base_url}, temperature={config.temperature}, max_tokens={config.max_tokens}")
        return ChatOpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

    async def run_debate(
        self,
        record_id: int,
        stream_callback: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> None:
        """Run a complete debate session.

        Args:
            record_id: The debate record ID
            stream_callback: Optional callback for streaming events
        """
        logger.info(f"========== 辩论开始 [record_id={record_id}] ==========")
        start_time = datetime.now()

        # Get debate record
        logger.debug(f"[{record_id}] 获取辩论记录...")
        record = crud.get_debate_record(self.db, record_id)
        if not record:
            logger.error(f"[{record_id}] 辩论记录不存在")
            raise ValueError(f"Debate record {record_id} not found")

        logger.info(f"[{record_id}] 辩题: {record.topic.title}")
        if record.topic.description:
            logger.info(f"[{record_id}] 辩题描述: {record.topic.description}")

        # Get LLM configs
        logger.debug(f"[{record_id}] 获取LLM配置...")
        pro_config = crud.get_llm_config(self.db, record.pro_config_id)
        con_config = crud.get_llm_config(self.db, record.con_config_id)

        if not pro_config or not con_config:
            logger.error(f"[{record_id}] LLM配置无效: pro_config_id={record.pro_config_id}, con_config_id={record.con_config_id}")
            raise ValueError("Invalid LLM configuration")

        logger.info(f"[{record_id}] 正方配置: {pro_config.name} (model={pro_config.model_name}, base_url={pro_config.base_url})")
        logger.info(f"[{record_id}] 反方配置: {con_config.name} (model={con_config.model_name}, base_url={con_config.base_url})")

        # Create LLM instances
        logger.debug(f"[{record_id}] 创建LLM实例...")
        pro_llm = self._create_llm(pro_config)
        con_llm = self._create_llm(con_config)
        logger.debug(f"[{record_id}] LLM实例创建完成")

        # Update status
        logger.info(f"[{record_id}] 状态更新: PENDING -> IN_PROGRESS")
        crud.update_debate_record_status(self.db, record_id, models.DebateStatus.IN_PROGRESS)

        if stream_callback:
            await stream_callback({
                "event_type": "start",
                "data": {"topic": record.topic.title}
            })

        # Get task config from topic or use default
        task_config = self.get_task_config(record)
        logger.debug(f"[{record_id}] 任务配置：{task_config}")

        # Initialize conversation history with system prompts from task config
        pro_history = [SystemMessage(content=task_config["pro_system_prompt"])]
        con_history = [SystemMessage(content=task_config["con_system_prompt"])]

        # Add topic to history
        topic_instruction = f"辩论题目：{record.topic.title}"
        if record.topic.description:
            topic_instruction += f"\n题目说明：{record.topic.description}"

        pro_history.append(HumanMessage(content=topic_instruction))
        con_history.append(HumanMessage(content=topic_instruction))
        logger.debug(f"[{record_id}] 初始化对话历史完成，辩题指令已添加")

        round_num = 0

        try:
            # Get debate phases from topic config
            debate_phases = self.get_debate_phases(record)

            # Run through each phase
            for phase in debate_phases:
                if self.is_aborted(record_id):
                    logger.warning(f"[{record_id}] 辩论被中止")
                    break

                phase_name = phase["name"]
                num_rounds = phase["rounds"]

                logger.info(f"[{record_id}] ---------- 阶段开始: {phase_name} ({phase['description']}) ----------")

                if stream_callback:
                    await stream_callback({
                        "event_type": "phase_start",
                        "data": {"phase": phase_name, "description": phase["description"]}
                    })

                for r in range(num_rounds):
                    if self.is_aborted(record_id):
                        logger.warning(f"[{record_id}] 辩论被中止")
                        break

                    round_num += 1
                    logger.info(f"[{record_id}] --- 第 {round_num} 轮 (阶段: {phase_name}) ---")

                    # Pro's turn
                    logger.debug(f"[{record_id}] 正方准备发言...")
                    pro_context = self._build_context(
                        history=pro_history,
                        opponent_history=con_history,
                        phase=phase_name,
                        is_pro=True,
                        round_num=round_num
                    )
                    logger.debug(f"[{record_id}] 正方上下文构建完成")

                    pro_response = await self._generate_response(
                        llm=pro_llm,
                        context=pro_context,
                        history=pro_history
                    )

                    if pro_response:
                        logger.info(f"[{record_id}] 正方发言完成 ({len(pro_response)} 字符)")
                        logger.debug(f"[{record_id}] 正方内容: {pro_response[:100]}...")

                        # Save message
                        crud.create_debate_message(
                            db=self.db,
                            record_id=record_id,
                            side=models.MessageSide.PRO,
                            content=pro_response,
                            round=round_num,
                            phase=phase_name
                        )
                        logger.debug(f"[{record_id}] 正方消息已保存到数据库")

                        # Update pro history
                        pro_history.append(AIMessage(content=pro_response))
                        con_history.append(HumanMessage(content=pro_response))

                        if stream_callback:
                            await stream_callback({
                                "event_type": "message",
                                "data": {
                                    "side": "pro",
                                    "content": pro_response,
                                    "round": round_num,
                                    "phase": phase_name
                                }
                            })

                    # Con's turn
                    logger.debug(f"[{record_id}] 反方准备发言...")
                    con_context = self._build_context(
                        history=con_history,
                        opponent_history=pro_history,
                        phase=phase_name,
                        is_pro=False,
                        round_num=round_num
                    )
                    logger.debug(f"[{record_id}] 反方上下文构建完成")

                    con_response = await self._generate_response(
                        llm=con_llm,
                        context=con_context,
                        history=con_history
                    )

                    if con_response:
                        logger.info(f"[{record_id}] 反方发言完成 ({len(con_response)} 字符)")
                        logger.debug(f"[{record_id}] 反方内容: {con_response[:100]}...")

                        # Save message
                        crud.create_debate_message(
                            db=self.db,
                            record_id=record_id,
                            side=models.MessageSide.CON,
                            content=con_response,
                            round=round_num,
                            phase=phase_name
                        )
                        logger.debug(f"[{record_id}] 反方消息已保存到数据库")

                        # Update con history
                        con_history.append(AIMessage(content=con_response))
                        pro_history.append(HumanMessage(content=con_response))

                        if stream_callback:
                            await stream_callback({
                                "event_type": "message",
                                "data": {
                                    "side": "con",
                                    "content": con_response,
                                    "round": round_num,
                                    "phase": phase_name
                                }
                            })

                logger.info(f"[{record_id}] ---------- 阶段结束: {phase_name} ----------")

        except Exception as e:
            error_msg = str(e)
            # Provide more helpful error messages
            if "404" in error_msg:
                error_msg = f"API 调用失败(404)：请检查 LLM 配置。\n" \
                           f"1. base_url 是否正确（OpenAI 兼容 API 通常需要以 /v1 结尾）\n" \
                           f"2. model_name 是否存在\n" \
                           f"原始错误: {error_msg}"
            elif "401" in error_msg or "Unauthorized" in error_msg:
                error_msg = f"API 认证失败(401)：请检查 API Key 是否正确。\n原始错误: {error_msg}"
            elif "403" in error_msg:
                error_msg = f"API 访问被拒绝(403)：请检查 API Key 权限。\n原始错误: {error_msg}"

            logger.error(f"[{record_id}] 辩论发生错误: {error_msg}", exc_info=True)

            if stream_callback:
                await stream_callback({
                    "event_type": "error",
                    "data": {"error": error_msg}
                })
            crud.update_debate_record_status(self.db, record_id, models.DebateStatus.ERROR)
            raise

        # Complete debate
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"[{record_id}] 状态更新: IN_PROGRESS -> COMPLETED")
        crud.update_debate_record_status(self.db, record_id, models.DebateStatus.COMPLETED)

        if stream_callback:
            await stream_callback({
                "event_type": "complete",
                "data": {"message": "辩论结束"}
            })

        # Clean up abort flag
        self._abort_flags.pop(record_id, None)

        logger.info(f"========== 辩论结束 [record_id={record_id}, 总轮数={round_num}, 耗时={duration:.2f}秒] ==========")

    def _build_context(
        self,
        history: list,
        opponent_history: list,
        phase: str,
        is_pro: bool,
        round_num: int
    ) -> str:
        """Build context for the current turn."""
        side = "正方" if is_pro else "反方"

        context = f"""当前辩论阶段：{phase}
当前轮次：{round_num}
你是：{side}

请根据你的立场和之前的辩论内容，发表你的观点。"""

        return context

    async def _generate_response(
        self,
        llm: ChatOpenAI,
        context: str,
        history: list
    ) -> str:
        """Generate a response from the LLM."""
        # Add current context
        messages = history + [HumanMessage(content=context)]

        logger.debug(f"调用 LLM API, 消息数量: {len(messages)}")
        api_start = datetime.now()

        try:
            # Invoke LLM
            response = await llm.ainvoke(messages)
            api_duration = (datetime.now() - api_start).total_seconds()

            logger.debug(f"LLM API 调用成功, 耗时: {api_duration:.2f}秒, 响应长度: {len(response.content)} 字符")

            return response.content

        except Exception as e:
            api_duration = (datetime.now() - api_start).total_seconds()
            logger.error(f"LLM API 调用失败, 耗时: {api_duration:.2f}秒, 错误: {str(e)}")
            raise

    async def run_debate_sync(
        self,
        record_id: int,
        stream_callback: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> None:
        """Run debate synchronously (for backward compatibility)."""
        await self.run_debate(record_id, stream_callback)


# Global engine registry
_engines: dict[int, DebateEngine] = {}


def get_or_create_engine(db: Session, record_id: int) -> DebateEngine:
    """Get or create a debate engine for a record."""
    if record_id not in _engines:
        _engines[record_id] = DebateEngine(db)
    return _engines[record_id]


def remove_engine(record_id: int) -> None:
    """Remove an engine from the registry."""
    _engines.pop(record_id, None)
