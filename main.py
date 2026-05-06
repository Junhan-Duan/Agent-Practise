from routers.flow_router import route_flow_type
from branch_flow_extractor import extract_branch_flow, BranchFlowExtractor
from pathlib import Path
import re
from ingest.document_loader import load_document

from models.linear_flow_spec import LinearFlowSpec, StepItem
from processors.role_normalizer import normalize_roles_by_input
from builders.flowchart_builder import build_flowchart_from_linear
from compilers.flowchart_compiler import compile_flowchart
from utils.mermaid_renderer import render_mermaid_to_image

from utils.loop_repairs import repair_loop_edges
from validators.branch_validator import validate_branch_flow, print_validation_result


def extract_linear_flow_by_rule(user_input: str) -> LinearFlowSpec:
    """
    不调用大模型，直接用规则从用户输入中提取线性流程步骤。
    目的：先保证 linear flow 一定可以输出 Mermaid。
    支持：
    1. 单行输入
    2. 多行输入
    3. 空行分隔
    4. 中文句号、分号、逗号
    5. 然后、接着、随后、之后、最后等逻辑连接词
    """

    # 2. 支持更多分隔符
    separators = [
        r"\n+",      # 一个或多个换行
        "然后",
        "接着",
        "随后",
        "之后",
        "最后",
        "最终",
        "并且",
        "，",
        ",",
        "。",
        "；",
        ";",
        r"\.",
        "->",
        "→",
    ]

    pattern = "|".join(map(re.escape, separators))

    raw_steps = re.split(pattern, user_input)

    steps = []
    for step in raw_steps:
        step = step.strip()
        if step:
            steps.append(step)

    if not steps:
        steps = [user_input.strip()]

    step_items = []

    for i, step in enumerate(steps):
        if i == 0:
            role = "start"
        elif i == len(steps) - 1:
            role = "end"
        else:
            role = "process"

        step_items.append(
            StepItem(
                text=step,
                role=role,
            )
        )

    return LinearFlowSpec(steps=step_items)

def read_multiline_input() -> str:
    print("请输入流程描述。")
    print("可以输入多行内容，输入完成后，单独输入 END 结束：")

    lines = [] #存储用户输入

    while True:
        line = input() #一直遍历输入，直到主动BREAK

        if line.strip() == "END":
            break

        lines.append(line) #如果输入不是END，就保存在lines中

    return "\n".join(lines).strip()  # .strip()去掉前后空格; "\n".join(lines)将多行内容重新拼接成完整字符串

def read_user_input() -> str:
    """
    让用户选择输入方式：
    1. 手动输入多行自然语言流程
    2. 从 .txt / .md 文档读取流程描述
    """

    print("请选择输入方式：")
    print("1. 手动输入流程描述")
    print("2. 从 .txt / .md 文档读取")
    
    choice = input("请输入选项 1 或 2：").strip()

    if choice == "2":
        file_path = input("请输入文档路径：").strip().strip('"').strip("'")
        user_input = load_document(file_path)

        print("\n文档读取成功，内容预览如下：")
        print("-" * 50)
        print(user_input[:1000])
        print("-" * 50)

        confirm = input("是否继续生成流程图？[y/n]: ").strip().lower()

        if confirm != "y":
            print("已取消。")
            return ""

        return user_input

    return read_multiline_input()

def main():
    user_input = read_user_input()

    if not user_input:
        print("输入为空，程序结束。")
        return

    flow_type = route_flow_type(user_input)

    print("\nRouter 判断结果：")
    print(flow_type)

    if flow_type == "branch":
    # 1. 用 LLM 抽取 branch JSON
        branch_diagram = extract_branch_flow(user_input)

    # 2. 修复返回 / 重新输入 / 再次输入这种循环边
        branch_diagram = repair_loop_edges(branch_diagram)

    # 3. 校验 branch 结构
        errors, warnings = validate_branch_flow(branch_diagram, user_input)
        print_validation_result(errors, warnings)

        if errors:
            print("\n检测到严重结构错误，建议先修复后再生成 Mermaid。")
            return

    # 4. 生成 Mermaid
        branch_result = BranchFlowExtractor(branch_diagram)
        mermaid_code = branch_result.to_mermaid()

        print("\nBranch Mermaid 结果：")
        print(mermaid_code)

        # 4. 保存文件
        diagram_dir = Path("diagrams")
        diagram_dir.mkdir(exist_ok=True)

        output_path = diagram_dir / "branch_flowchart.mmd"
        output_path.write_text(mermaid_code, encoding="utf-8")

        print(f"\n已保存到：{output_path}")

        image_path = diagram_dir / "branch_flowchart.svg"
        render_mermaid_to_image(output_path, image_path)

    elif flow_type == "linear":
        # 1. 不调用 LLM，直接用规则提取 linear steps
        linear_spec = extract_linear_flow_by_rule(user_input)

        print("\nLinear 规则提取结果：")
        print(linear_spec)

        # 2. 修正 start / process / decision / end
        linear_spec = normalize_roles_by_input(linear_spec, user_input)

        # 3. 转成统一 FlowchartSpec
        flowchart_spec = build_flowchart_from_linear(linear_spec)

        # 4. 编译成 Mermaid
        mermaid_code = compile_flowchart(flowchart_spec)

        print("\nLinear Mermaid 结果：")
        print(mermaid_code)

        # 5. 保存文件
        diagram_dir = Path("diagrams")
        diagram_dir.mkdir(exist_ok=True)

        output_path = diagram_dir / "flowchart.mmd"
        output_path.write_text(mermaid_code, encoding="utf-8")

        print(f"\n已保存到：{output_path}")
        
        image_path = diagram_dir / "branch_flowchart.svg"
        render_mermaid_to_image(output_path, image_path)

    else:
        print("\n暂不支持的流程类型：")
        print(flow_type)


if __name__ == "__main__":
    main()