"""
Core agent application for Day 03: Chatbot vs ReAct Agent.

Chosen topic: personal schedule management assistant with mock Google Calendar
tools. The original lab shape is preserved: baseline chatbot, ReAct agent,
MCP server, and waterfall trace export.
"""

import json
import os
import sys
import time
from typing import Any, Dict, List

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from mcp_server import MCPAcademicServer
from prompts import CHATBOT_BASELINE_PROMPT, MAX_ITERATIONS, REACT_AGENT_SYSTEM_PROMPT
from providers import get_llm_provider

load_dotenv()


def load_test_cases():
    """Load test cases without modifying config/test_cases.json."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        example_path = os.path.join(base_dir, "config", "test_cases.example.json")
        if os.path.exists(example_path):
            print("⚠️ [CONFIG NOTICE]: Chưa thấy 'config/test_cases.json'. Đang dùng file example.")
            config_path = example_path
        else:
            config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list):
    """Save the Waterfall Trace Log to docs/trace_waterfall.json."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    trace_path = os.path.join(docs_dir, "trace_waterfall.json")
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, ensure_ascii=False, indent=2)
    print(f"📊 [OBSERVABILITY]: Đã lưu {len(trace_data)} sự kiện Waterfall Trace tại '{trace_path}'!")


def run_baseline_chatbot(user_query: str, provider):
    """Run the level-2 chatbot without tools."""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot phản hồi:\n{response}")


def build_react_prompt(user_query: str, tool_history: List[Dict[str, Any]]) -> str:
    """Build the next model input with all previous observations."""
    if not tool_history:
        return user_query

    history_json = json.dumps(tool_history, ensure_ascii=False, indent=2)
    return f"""
Yêu cầu gốc của người dùng:
{user_query}

ReAct context so far:
{history_json}

Hãy tiếp tục theo ReAct:
- Nếu cần thêm dữ liệu hoặc cần thao tác tiếp, hãy gọi đúng tool kế tiếp.
- Nếu đã đủ dữ liệu hoặc thao tác đã hoàn tất, hãy trả lời Final Answer bằng tiếng Việt.
""".strip()


def fallback_final_answer(tool_history: List[Dict[str, Any]]) -> str:
    """Create a safe final response if the loop reaches MAX_ITERATIONS."""
    if not tool_history:
        return "Mình chưa có đủ thông tin để hoàn thành yêu cầu."

    last = tool_history[-1]
    tool_name = last.get("tool_name")
    observation = last.get("observation", {})
    status = observation.get("status")

    if status == "SUCCESS" and observation.get("message"):
        return observation["message"]

    if tool_name == "schedule_fetch" and status == "SUCCESS":
        count = observation.get("count", 0)
        if count == 0:
            return "Mình đã kiểm tra lịch cá nhân mock và không tìm thấy sự kiện nào trong khoảng thời gian đó."
        events = observation.get("events", [])
        titles = ", ".join(event.get("title", "Không có tiêu đề") for event in events)
        return f"Mình đã kiểm tra lịch cá nhân mock và tìm thấy {count} sự kiện: {titles}."

    if tool_name == "academic_query" and status == "SUCCESS":
        data = observation.get("data", {})
        return (
            f"Kết quả tra cứu cho sinh viên {observation.get('student_id', '')}: "
            f"{data.get('full_name', '')}, lớp {data.get('class', '')}, GPA {data.get('gpa', '')}."
        )

    return f"Mình đã dừng sau {MAX_ITERATIONS} vòng ReAct. Observation cuối cùng: {json.dumps(observation, ensure_ascii=False)}"


def run_react_agent(user_query: str, provider, mcp_server: MCPAcademicServer) -> list:
    """
    Run the ReAct loop: Thought -> Action -> Observation -> Thought ...

    Returns trace logs for the session.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    trace_logs = []
    tool_history: List[Dict[str, Any]] = []
    tools_list = mcp_server.list_tools()

    for step in range(1, MAX_ITERATIONS + 1):
        step_start_time = time.time()
        print(f"\n--- 🔄 ReAct Loop (Step {step}/{MAX_ITERATIONS}) ---")

        model_prompt = build_react_prompt(user_query, tool_history)
        llm_response = provider.generate_with_tools(
            model_prompt,
            tools_list,
            system_prompt=REACT_AGENT_SYSTEM_PROMPT,
        )
        latency_ms = round((time.time() - step_start_time) * 1000, 2)

        thought = llm_response.get("thought", "Đang suy luận bước tiếp theo.")
        print(f"🧠 [Thought]: {thought}")

        if llm_response.get("type") == "text":
            final_content = llm_response.get("content", "")
            print(f"🏁 [Final Answer]: {final_content}")
            trace_logs.append(
                {
                    "step": step,
                    "query": user_query,
                    "action_type": "FINAL_ANSWER",
                    "thought": thought,
                    "output": final_content,
                    "latency_ms": latency_ms,
                }
            )
            return trace_logs

        if llm_response.get("type") != "tool_call":
            final_content = "Provider trả về định dạng không hợp lệ, nên agent dừng để tránh thao tác sai."
            print(f"🏁 [Final Answer]: {final_content}")
            trace_logs.append(
                {
                    "step": step,
                    "query": user_query,
                    "action_type": "FINAL_ANSWER",
                    "thought": thought,
                    "output": final_content,
                    "latency_ms": latency_ms,
                }
            )
            return trace_logs

        tool_name = llm_response.get("tool_name")
        arguments = llm_response.get("arguments", {})
        print(f"🛠️ [Action Proposed]: {tool_name}({arguments})")

        mcp_result = mcp_server.call_tool(tool_name, arguments)
        obs_data = mcp_result.get("result", {})
        obs_str = json.dumps(obs_data, ensure_ascii=False)
        print(f"👁️ [Observation từ MCP Server]: {obs_str}")

        trace_logs.append(
            {
                "step": step,
                "query": user_query,
                "action_type": "TOOL_EXECUTION",
                "thought": thought,
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data,
                "latency_ms": latency_ms,
            }
        )

        tool_history.append(
            {
                "step": step,
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data,
            }
        )

    final_answer = fallback_final_answer(tool_history)
    print(f"🏁 [Final Answer]: {final_answer}")
    trace_logs.append(
        {
            "step": MAX_ITERATIONS + 1,
            "query": user_query,
            "action_type": "FINAL_ANSWER",
            "thought": "Đã đạt giới hạn số vòng ReAct, tổng hợp từ Observation cuối cùng.",
            "output": final_answer,
            "latency_ms": 0.0,
        }
    )
    return trace_logs


if __name__ == "__main__":
    print("==========================================================")
    print("📅 DAY 03 LAB: PERSONAL SCHEDULE CHATBOT VS REACT AGENT")
    print("==========================================================")

    provider = get_llm_provider()
    mcp_server = MCPAcademicServer()

    print(f"🔌 LLM Provider: {provider.__class__.__name__}")
    print(f"🌐 MCP Server: {mcp_server.server_name}\n")

    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases thử nghiệm.\n")

    if "--interactive" in sys.argv:
        print("🎮 [INTERACTIVE MODE] Trò chuyện trực tiếp với ReAct Agent:")
        print("💡 Gợi ý câu hỏi thử nghiệm:")
        print("   - Kiểm tra lịch: 'Hãy kiểm tra xem tối thứ 7 tuần này tôi có lịch gì không?'")
        print("   - Multi-step: 'Kiểm tra tối thứ 7 tuần này, nếu rảnh thì đặt lịch đi chơi lúc 19h.'")
        print("   - Xóa lịch: 'Xóa lịch hẹn đi chơi vào tối Chủ Nhật của tôi.'")
        print("   - Gõ 'exit' hoặc 'quit' để kết thúc phiên trò chuyện.\n")
        while True:
            try:
                user_input = input("👤 Bạn hỏi: ").strip()
                if not user_input or user_input.lower() in ["exit", "quit"]:
                    print("👋 Tạm biệt! Kết thúc phiên trò chuyện.")
                    break
                logs = run_react_agent(user_input, provider, mcp_server)
                save_waterfall_trace(logs)
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Đã thoát phiên tương tác.")
                break
    elif "--all" in sys.argv:
        print("🚀 [TEST SUITE MODE] Kiểm tra 5 Test Cases:")
        completed_count = 0
        todo_count = 0
        all_traces = []

        for tc in tests:
            print("\n==================================================")
            print(f"🧪 [{tc['id']}] Loại test: {tc['type']} (Độ phức tạp: {tc['complexity']})")
            print(f"📌 Kỳ vọng: {tc['expected_behavior']}")

            if tc["question"].strip().startswith("TODO"):
                print("⏸️ [CHƯA KÍCH HOẠT - ĐANG LÀ TODO]:")
                print(f"   {tc['question']}")
                todo_count += 1
            else:
                logs = run_react_agent(tc["question"], provider, mcp_server)
                all_traces.extend(logs)
                completed_count += 1

        print("\n==================================================")
        print(
            f"📊 [KẾT QUẢ TEST SUITE]: Đã thực thi {completed_count}/{len(tests)} Test Cases | "
            f"{todo_count} Test Cases đang chờ điền câu hỏi (TODO)"
        )
        if all_traces:
            save_waterfall_trace(all_traces)
        print("💡 Để trò chuyện trực tiếp từng câu: chạy 'python src/app.py --interactive'")
    else:
        print("ℹ️ HƯỚNG DẪN SỬ DỤNG CHƯƠNG TRÌNH:")
        print("  1. Chat trực tiếp liên tục:   python src/app.py --interactive")
        print("  2. Chạy toàn bộ Test Cases:    python src/app.py --all\n")

        sample_query = tests[2]["question"] if len(tests) > 2 else tests[0]["question"]
        print("--- 🏁 DEMO CHẠY THỬ 1 TEST CASE MẪU VỀ LỊCH CÁ NHÂN ---")
        logs = run_react_agent(sample_query, provider, mcp_server)
        save_waterfall_trace(logs)
        print("\n💡 Hãy thử lệnh: python src/app.py --interactive để chat trực tiếp!")
