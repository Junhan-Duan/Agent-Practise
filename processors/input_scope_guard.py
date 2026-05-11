from dataclasses import dataclass


@dataclass
class InputScopeResult:
    """
    Store the result of input scope checking.

    is_supported:
        True means the input is suitable for flowchart generation.
        False means the input may not be suitable.

    scope_type:
        Detected input type.

    reason:
        Explanation shown to the user.
    """

    is_supported: bool
    scope_type: str
    reason: str


SEQUENCE_KEYWORDS = [
    "首先",
    "然后",
    "接着",
    "随后",
    "之后",
    "最后",
    "最终",
    "第一步",
    "第二步",
    "step",
    "Step",
]


DECISION_KEYWORDS = [
    "如果",
    "若",
    "是否",
    "判断",
    "检查",
    "满足",
    "符合",
    "成功",
    "失败",
    "否则",
    "不通过",
    "if",
    "else",
]


ACTION_KEYWORDS = [
    "提交",
    "上传",
    "下载",
    "发送",
    "接收",
    "读取",
    "解析",
    "处理",
    "执行",
    "生成",
    "输出",
    "返回",
    "提示",
    "通知",
    "验证",
    "审核",
    "审批",
    "登录",
]


CONNECTION_VERBS = [
    "连接",
    "接入",
    "连到",
    "连至",
    "相连",
]


INTERFACE_KEYWORDS = [
    "I2C",
    "SPI",
    "USART",
    "UART",
    "PWM",
    "GPIO",
    "USB",
    "CAN",
]


HARDWARE_KEYWORDS = [
    "STM32",
    "树莓派",
    "MPU6050",
    "HC05",
    "TB6612",
    "传感器",
    "电机",
    "雷达",
    "摄像头",
    "上位机",
    "下位机",
]


QUESTION_KEYWORDS = [
    "什么是",
    "为什么",
    "怎么",
    "如何",
    "能不能",
    "是否可以",
    "区别是什么",
]


CONCEPT_KEYWORDS = [
    "是一种",
    "指的是",
    "定义",
    "概念",
    "特点",
    "优势",
    "缺点",
    "背景",
    "意义",
]


def count_keyword_hits(text: str, keywords: list[str]) -> int:
    """
    Count how many keywords appear in the input text.
    """

    return sum(1 for keyword in keywords if keyword in text)


def check_input_scope(user_input: str) -> InputScopeResult:
    """
    Check whether the user input is suitable for flowchart generation.

    Main principle:
    - Workflow signals have higher priority.
    - Hardware or module words alone should not block generation.
    - Only static connection descriptions with weak workflow signals should trigger a warning.
    """

    normalized_input = user_input.strip()

    # Empty input should not continue.
    if not normalized_input:
        return InputScopeResult(
            is_supported=False,
            scope_type="too_short",
            reason="当前输入为空，缺少可转换为流程图的步骤内容。",
        )

    # Very short input usually lacks enough process information.
    if len(normalized_input) < 10:
        return InputScopeResult(
            is_supported=False,
            scope_type="too_short",
            reason="当前输入过短，缺少足够的流程步骤，不建议直接生成流程图。",
        )

    # Count workflow signals.
    sequence_hits = count_keyword_hits(normalized_input, SEQUENCE_KEYWORDS)
    decision_hits = count_keyword_hits(normalized_input, DECISION_KEYWORDS)
    action_hits = count_keyword_hits(normalized_input, ACTION_KEYWORDS)

    # Count non-workflow signals.
    connection_hits = count_keyword_hits(normalized_input, CONNECTION_VERBS)
    interface_hits = count_keyword_hits(normalized_input, INTERFACE_KEYWORDS)
    hardware_hits = count_keyword_hits(normalized_input, HARDWARE_KEYWORDS)
    question_hits = count_keyword_hits(normalized_input, QUESTION_KEYWORDS)
    concept_hits = count_keyword_hits(normalized_input, CONCEPT_KEYWORDS)

    # Workflow score has higher priority.
    workflow_score = sequence_hits * 2 + decision_hits * 3 + action_hits

    # Topology score is only strong when connection/interface/hardware signals appear together.
    topology_score = connection_hits * 2 + interface_hits * 2 + hardware_hits

    # 1. Strong workflow input: allow directly.
    if workflow_score >= 3:
        return InputScopeResult(
            is_supported=True,
            scope_type="workflow",
            reason="当前输入包含明显的流程动作、判断条件或执行顺序，可以继续生成流程图。",
        )

    # 2. Question-like input without workflow signal.
    if question_hits >= 1 and workflow_score == 0:
        return InputScopeResult(
            is_supported=False,
            scope_type="question",
            reason="当前输入更像问题咨询，而不是流程描述。流程图生成通常需要包含步骤、动作、判断或执行顺序。",
        )

    # 3. Concept explanation without workflow signal.
    if concept_hits >= 2 and workflow_score <= 1:
        return InputScopeResult(
            is_supported=False,
            scope_type="concept_explanation",
            reason="当前输入更像概念解释或背景说明，缺少明确的执行步骤、判断条件或流程顺序。",
        )

    # 4. Static topology-like input.
    # Important:
    # It should only warn when topology signals are strong and workflow signals are weak.
    if topology_score >= 6 and workflow_score <= 1 and decision_hits == 0:
        return InputScopeResult(
            is_supported=False,
            scope_type="topology",
            reason=(
                "当前输入包含较多硬件组件、通信接口或连接关系，"
                "但缺少明显的动作顺序或判断逻辑，更像系统拓扑 / 模块连接描述。"
            ),
        )

    # 5. Weak but possible workflow input: allow.
    if action_hits >= 1 or decision_hits >= 1:
        return InputScopeResult(
            is_supported=True,
            scope_type="workflow",
            reason="当前输入包含一定流程特征，可以尝试生成流程图。",
        )

    # 6. Unknown input: warn.
    return InputScopeResult(
        is_supported=False,
        scope_type="unknown",
        reason=(
            "当前输入缺少明显的流程特征，例如步骤顺序、动作执行、判断条件或返回关系，"
            "不建议直接转换为流程图。"
        ),
    )