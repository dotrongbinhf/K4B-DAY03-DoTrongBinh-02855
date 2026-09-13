"""
Multi-provider LLM adapter: Google Gemini, OpenAI, and Offline Mock.

The offline mock is intentionally deterministic so the lab can demonstrate a
multi-step ReAct loop without depending on live API access.
"""

import json
import os
import re
import sys
from typing import Any, Dict, List

from dotenv import load_dotenv

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()


class BaseLLMProvider:
    """Base interface for LLM providers that support native tool calling."""

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = "",
    ) -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Offline mock provider used for repeatable local testing."""

    def __init__(self):
        self.model_name = "Offline-Mock-Schedule-Agent-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return (
            "[Mock Chatbot Response]: Tôi là trợ lý quản lý lịch trình cá nhân. "
            "Ở chế độ Chatbot Baseline, tôi có thể tư vấn cách sắp xếp thời gian "
            "nhưng không thể kiểm tra hoặc chỉnh sửa lịch thật."
        )

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = "",
    ) -> Dict[str, Any]:
        del tools_schema, system_prompt
        prompt_lower = prompt.lower()

        if "schedule_create_event" in prompt_lower:
            return {
                "type": "text",
                "content": "Mình đã thêm lịch đi chơi với người yêu vào tối thứ 7 tuần này lúc 19:00 trong lịch cá nhân mock.",
                "thought": "Tool tạo sự kiện đã trả về SUCCESS, nên có thể tổng hợp kết quả cuối cùng.",
            }

        if "schedule_delete_event" in prompt_lower:
            return {
                "type": "text",
                "content": "Mình đã xóa sự kiện phù hợp khỏi lịch cá nhân mock.",
                "thought": "Tool xóa sự kiện đã hoàn tất, nên có thể trả lời cuối cùng.",
            }

        if "schedule_update_event" in prompt_lower:
            return {
                "type": "text",
                "content": "Mình đã cập nhật sự kiện phù hợp trong lịch cá nhân mock.",
                "thought": "Tool cập nhật sự kiện đã hoàn tất, nên có thể trả lời cuối cùng.",
            }

        if "academic_query" in prompt_lower:
            return {
                "type": "text",
                "content": "Kết quả mock từ academic_query: SV2026001 là Nguyễn Văn An, lớp AI-K4, GPA 3.85, email an.nv@vinuni.edu.vn, trạng thái Đang học.",
                "thought": "Observation từ academic_query đã đủ để trả lời, không cần gọi lại tool.",
            }

        if "schedule_appointment" in prompt_lower:
            return {
                "type": "text",
                "content": "Mình đã đặt lịch tư vấn học vụ bằng tool mặc định của lab.",
                "thought": "Observation từ schedule_appointment đã đủ để trả lời cuối cùng.",
            }

        if self._is_delete_sunday_request(prompt_lower):
            return self._handle_delete_sunday_flow(prompt, prompt_lower)

        if self._is_update_request(prompt_lower):
            return self._handle_update_flow(prompt, prompt_lower)

        if self._mentions_saturday_evening(prompt_lower):
            return self._handle_saturday_evening_flow(prompt_lower)

        if self._is_academic_appointment_request(prompt_lower):
            return {
                "type": "tool_call",
                "tool_name": "schedule_appointment",
                "arguments": {
                    "student_id": "SV2026001",
                    "datetime_str": "14:00 15/09/2026",
                    "advisor_name": "PGS.TS Nguyễn Văn A",
                },
                "thought": "Người dùng yêu cầu đặt lịch tư vấn học vụ cho SV2026001, nên gọi tool học vụ mặc định của lab.",
            }

        if "sv2026001" in prompt_lower or "tra cứu học vụ" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "academic_query",
                "arguments": {"student_id": "SV2026001"},
                "thought": "Người dùng muốn tra cứu thông tin học vụ của sinh viên SV2026001, nên gọi academic_query.",
            }

        if self._is_general_create_request(prompt_lower):
            return {
                "type": "tool_call",
                "tool_name": "schedule_create_event",
                "arguments": {
                    "title": "Sự kiện cá nhân",
                    "start_datetime": "2026-09-19T19:00:00+07:00",
                    "end_datetime": "2026-09-19T20:00:00+07:00",
                    "location": "",
                    "notes": "Được tạo từ yêu cầu mock.",
                },
                "thought": "Người dùng muốn thêm một lịch cá nhân; với mock data, tôi tạo event mẫu ở khung giờ rõ nhất.",
            }

        return {
            "type": "text",
            "content": (
                "[Mock Agent Response]: Tôi có thể giúp bạn kiểm tra lịch tuần này, "
                "thêm lịch mới, sửa lịch, hoặc xóa lịch bằng các tool lịch cá nhân mock."
            ),
            "thought": "Yêu cầu hiện tại là trao đổi chung, chưa cần gọi tool.",
        }

    @staticmethod
    def _mentions_saturday_evening(prompt_lower: str) -> bool:
        return (
            ("thứ 7" in prompt_lower or "thứ bảy" in prompt_lower or "thu 7" in prompt_lower)
            and ("tối" in prompt_lower or "18" in prompt_lower or "19" in prompt_lower)
        )

    @staticmethod
    def _is_delete_sunday_request(prompt_lower: str) -> bool:
        return (
            ("xóa" in prompt_lower or "xoa" in prompt_lower)
            and ("chủ nhật" in prompt_lower or "chu nhat" in prompt_lower)
        )

    @staticmethod
    def _is_academic_appointment_request(prompt_lower: str) -> bool:
        return (
            "sv2026001" in prompt_lower
            and ("tư vấn" in prompt_lower or "cố vấn" in prompt_lower or "hoc vu" in prompt_lower)
            and ("đặt lịch" in prompt_lower or "dat lich" in prompt_lower)
        )

    @staticmethod
    def _is_general_create_request(prompt_lower: str) -> bool:
        return (
            "schedule_fetch" not in prompt_lower
            and any(keyword in prompt_lower for keyword in ["thêm lịch", "tạo lịch", "đặt lịch"])
        )

    @staticmethod
    def _is_update_request(prompt_lower: str) -> bool:
        return any(keyword in prompt_lower for keyword in ["sửa lịch", "đổi lịch", "cập nhật lịch", "chỉnh lịch"])

    def _handle_saturday_evening_flow(self, prompt_lower: str) -> Dict[str, Any]:
        if "schedule_fetch" not in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "schedule_fetch",
                "arguments": {
                    "start_datetime": "2026-09-19T18:00:00+07:00",
                    "end_datetime": "2026-09-19T22:00:00+07:00",
                    "query": "",
                },
                "thought": "Cần kiểm tra lịch tối thứ 7 tuần này trước khi trả lời hoặc tạo sự kiện.",
            }

        wants_create = any(keyword in prompt_lower for keyword in ["đặt", "dat", "thêm", "them", "tạo", "tao"])
        if wants_create:
            if '"count": 0' in prompt_lower:
                return {
                    "type": "tool_call",
                    "tool_name": "schedule_create_event",
                    "arguments": {
                        "title": "Đi chơi với người yêu",
                        "start_datetime": "2026-09-19T19:00:00+07:00",
                        "end_datetime": "2026-09-19T21:00:00+07:00",
                        "location": "",
                        "notes": "Tạo theo yêu cầu: nếu tối thứ 7 rảnh thì đặt lúc 19h.",
                    },
                    "thought": "Observation cho thấy tối thứ 7 đang rảnh, nên đặt lịch đúng khung giờ người dùng yêu cầu.",
                }

            return {
                "type": "tool_call",
                "tool_name": "schedule_create_event",
                "arguments": {
                    "title": "Đi chơi với người yêu",
                    "start_datetime": "2026-09-20T19:00:00+07:00",
                    "end_datetime": "2026-09-20T21:00:00+07:00",
                    "location": "",
                    "notes": "Tạo theo yêu cầu: nếu tối thứ 7 bận thì chuyển sang Chủ Nhật cùng giờ.",
                },
                "thought": "Observation cho thấy tối thứ 7 có lịch, nên thử đặt sang Chủ Nhật cùng giờ.",
            }

        if '"count": 0' in prompt_lower:
            return {
                "type": "text",
                "content": "Tối thứ 7 tuần này, từ 18:00 đến 22:00, bạn chưa có lịch nào trong lịch cá nhân mock.",
                "thought": "Đã có Observation từ schedule_fetch và không có event trùng khung giờ.",
            }

        return {
            "type": "text",
            "content": "Tối thứ 7 tuần này bạn đang có ít nhất một sự kiện trong lịch cá nhân mock. Mình đã dựa trên kết quả schedule_fetch để trả lời.",
            "thought": "Đã có Observation từ schedule_fetch và có event trùng khung giờ.",
        }

    def _handle_delete_sunday_flow(self, prompt: str, prompt_lower: str) -> Dict[str, Any]:
        if "schedule_fetch" not in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "schedule_fetch",
                "arguments": {
                    "start_datetime": "2026-09-20T18:00:00+07:00",
                    "end_datetime": "2026-09-20T22:00:00+07:00",
                    "query": "đi chơi",
                },
                "thought": "Cần tìm event đi chơi vào tối Chủ Nhật trước; chỉ được xóa nếu tìm thấy event_id.",
            }

        if '"count": 0' in prompt_lower:
            return {
                "type": "text",
                "content": "Mình đã kiểm tra lịch tối Chủ Nhật và không tìm thấy sự kiện đi chơi nào, nên không có lịch nào bị xóa.",
                "thought": "Observation cho thấy không có event phù hợp, nên không gọi tool xóa.",
            }

        event_id_match = re.search(r'"event_id"\s*:\s*"([^"]+)"', prompt)
        if event_id_match:
            return {
                "type": "tool_call",
                "tool_name": "schedule_delete_event",
                "arguments": {"event_id": event_id_match.group(1)},
                "thought": "Đã tìm thấy event_id phù hợp trong Observation, nên có thể gọi tool xóa.",
            }

        return {
            "type": "text",
            "content": "Mình thấy có lịch vào tối Chủ Nhật nhưng chưa lấy được event_id rõ ràng, nên chưa xóa để tránh thao tác nhầm.",
            "thought": "Không đủ dữ liệu định danh event để xóa an toàn.",
        }

    def _handle_update_flow(self, prompt: str, prompt_lower: str) -> Dict[str, Any]:
        query = "tập gym" if "gym" in prompt_lower else ""
        if "schedule_fetch" not in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "schedule_fetch",
                "arguments": {
                    "start_datetime": "2026-09-14T00:00:00+07:00",
                    "end_datetime": "2026-09-21T00:00:00+07:00",
                    "query": query,
                },
                "thought": "Cần tìm event hiện có trong tuần này trước khi cập nhật.",
            }

        if '"count": 0' in prompt_lower:
            return {
                "type": "text",
                "content": "Mình đã kiểm tra lịch cá nhân mock nhưng không tìm thấy sự kiện phù hợp để cập nhật.",
                "thought": "Không có event phù hợp trong Observation, nên không gọi update.",
            }

        event_id_match = re.search(r'"event_id"\s*:\s*"([^"]+)"', prompt)
        if event_id_match:
            return {
                "type": "tool_call",
                "tool_name": "schedule_update_event",
                "arguments": {
                    "event_id": event_id_match.group(1),
                    "start_datetime": "2026-09-16T20:00:00+07:00",
                    "end_datetime": "2026-09-16T21:00:00+07:00",
                    "notes": "Được cập nhật từ yêu cầu mock.",
                },
                "thought": "Đã tìm thấy event_id trong Observation, nên gọi tool cập nhật.",
            }

        return {
            "type": "text",
            "content": "Mình thấy có sự kiện phù hợp nhưng chưa lấy được event_id rõ ràng, nên chưa cập nhật để tránh sửa nhầm.",
            "thought": "Không đủ dữ liệu định danh event để cập nhật an toàn.",
        }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider using native function declarations."""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return MockOfflineProvider().generate(prompt, system_prompt)
        try:
            from google import genai

            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = "",
    ) -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            function_declarations = []
            for tool in tools_schema:
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append(
                    {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {}),
                    }
                )

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2,
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )

            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, "args") and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini đề xuất gọi tool '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}",
                }

            return {
                "type": "text",
                "content": response.text or "",
                "thought": "Gemini trả lời trực tiếp sau khi xem context/Observation hiện có.",
            }

        except Exception as e:
            print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider using native tool calling."""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return MockOfflineProvider().generate(prompt, system_prompt)
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = "",
    ) -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool["name"],
                            "description": tool.get("description", ""),
                            "parameters": tool.get("parameters", {}),
                        },
                    }
                )

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None,
                temperature=0.2,
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI đề xuất gọi tool '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}",
                }

            return {
                "type": "text",
                "content": msg.content or "",
                "thought": "OpenAI trả lời trực tiếp sau khi xem context/Observation hiện có.",
            }
        except Exception as e:
            print(f"⚠️ [OpenAI API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


def get_llm_provider() -> BaseLLMProvider:
    """Create a provider based on the LLM_PROVIDER environment variable."""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        return GeminiProvider() if key and key != "your_gemini_api_key_here" else MockOfflineProvider()
    if provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        return OpenAIProvider() if key and key != "your_openai_api_key_here" else MockOfflineProvider()
    return MockOfflineProvider()
