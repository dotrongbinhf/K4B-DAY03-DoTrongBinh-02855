"""
Tool schemas and execution backend.

The two original academic tools are intentionally kept for the lab template.
Personal schedule tools are added below them and use mock in-memory data so the
ReAct loop can be tested without a real Google Calendar connection.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


# ==============================================================================
# 1. TOOL SCHEMAS
# ==============================================================================

TOOLS_SCHEMA = [
    {
        "name": "academic_query",
        "description": "Tra cứu hồ sơ và thông tin học vụ của sinh viên VinUni bằng mã sinh viên.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần tra cứu (ví dụ: 'SV2026001')",
                }
            },
            "required": ["student_id"],
        },
    },
    {
        "name": "schedule_appointment",
        "description": "Đặt lịch hẹn tư vấn học vụ với Cố vấn học tập VinUni.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần đặt lịch (ví dụ: 'SV2026001')",
                },
                "datetime_str": {
                    "type": "string",
                    "description": "Thời gian hẹn (ví dụ: '14:00 15/09/2026')",
                },
                "advisor_name": {
                    "type": "string",
                    "description": "Tên cố vấn học tập",
                },
            },
            "required": ["student_id", "datetime_str", "advisor_name"],
        },
    },
    {
        "name": "schedule_fetch",
        "description": "Kiểm tra các sự kiện trong lịch cá nhân theo khoảng thời gian.",
        "parameters": {
            "type": "object",
            "properties": {
                "start_datetime": {
                    "type": "string",
                    "description": "Thời điểm bắt đầu theo ISO 8601, ví dụ: '2026-09-19T18:00:00+07:00'.",
                },
                "end_datetime": {
                    "type": "string",
                    "description": "Thời điểm kết thúc theo ISO 8601, ví dụ: '2026-09-19T22:00:00+07:00'.",
                },
                "query": {
                    "type": "string",
                    "description": "Từ khóa lọc theo tiêu đề hoặc ghi chú sự kiện. Bỏ trống nếu muốn lấy tất cả.",
                },
            },
            "required": ["start_datetime", "end_datetime"],
        },
    },
    {
        "name": "schedule_create_event",
        "description": "Thêm một sự kiện mới vào lịch cá nhân mock.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Tiêu đề sự kiện.",
                },
                "start_datetime": {
                    "type": "string",
                    "description": "Thời điểm bắt đầu theo ISO 8601.",
                },
                "end_datetime": {
                    "type": "string",
                    "description": "Thời điểm kết thúc theo ISO 8601.",
                },
                "location": {
                    "type": "string",
                    "description": "Địa điểm, có thể để trống.",
                },
                "notes": {
                    "type": "string",
                    "description": "Ghi chú thêm, có thể để trống.",
                },
            },
            "required": ["title", "start_datetime", "end_datetime"],
        },
    },
    {
        "name": "schedule_update_event",
        "description": "Cập nhật một sự kiện trong lịch cá nhân mock bằng event_id.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Mã sự kiện cần cập nhật, lấy từ schedule_fetch.",
                },
                "title": {
                    "type": "string",
                    "description": "Tiêu đề mới nếu cần đổi.",
                },
                "start_datetime": {
                    "type": "string",
                    "description": "Thời điểm bắt đầu mới theo ISO 8601 nếu cần đổi.",
                },
                "end_datetime": {
                    "type": "string",
                    "description": "Thời điểm kết thúc mới theo ISO 8601 nếu cần đổi.",
                },
                "location": {
                    "type": "string",
                    "description": "Địa điểm mới nếu cần đổi.",
                },
                "notes": {
                    "type": "string",
                    "description": "Ghi chú mới nếu cần đổi.",
                },
            },
            "required": ["event_id"],
        },
    },
    {
        "name": "schedule_delete_event",
        "description": "Xóa một sự kiện trong lịch cá nhân mock bằng event_id.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Mã sự kiện cần xóa, lấy từ schedule_fetch.",
                }
            },
            "required": ["event_id"],
        },
    },
]


# ==============================================================================
# 2. MOCK DATA AND TOOL EXECUTION
# ==============================================================================

MOCK_DATABASE = {
    "SV2026001": {
        "full_name": "Nguyễn Văn An",
        "class": "AI-K4",
        "gpa": 3.85,
        "email": "an.nv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A",
    },
    "SV2026002": {
        "full_name": "Trần Thị Bình",
        "class": "AI-K4",
        "gpa": 3.60,
        "email": "binh.tt@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "TS. Lê Thị B",
    },
}

MOCK_CALENDAR_EVENTS: List[Dict[str, str]] = [
    {
        "event_id": "EVT-1001",
        "title": "Họp dự án AI",
        "start_datetime": "2026-09-14T09:00:00+07:00",
        "end_datetime": "2026-09-14T10:00:00+07:00",
        "location": "Online",
        "notes": "Trao đổi tiến độ tuần.",
    },
    {
        "event_id": "EVT-1002",
        "title": "Tập gym",
        "start_datetime": "2026-09-16T18:30:00+07:00",
        "end_datetime": "2026-09-16T19:30:00+07:00",
        "location": "Gym gần nhà",
        "notes": "Buổi tập cá nhân.",
    },
    {
        "event_id": "EVT-1003",
        "title": "Ăn tối với gia đình",
        "start_datetime": "2026-09-18T19:00:00+07:00",
        "end_datetime": "2026-09-18T20:30:00+07:00",
        "location": "Nhà",
        "notes": "Lịch cá nhân cố định.",
    },
]

DEFAULT_TIMEZONE = timezone(timedelta(hours=7))


def _parse_datetime(value: str) -> Optional[datetime]:
    value = (value or "").strip()
    if not value:
        return None

    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=DEFAULT_TIMEZONE)
    except ValueError:
        pass

    for fmt in ("%H:%M %d/%m/%Y", "%Hh %d/%m/%Y", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=DEFAULT_TIMEZONE)
        except ValueError:
            continue
    return None


def _event_overlaps(event: Dict[str, str], start_dt: datetime, end_dt: datetime) -> bool:
    event_start = _parse_datetime(event["start_datetime"])
    event_end = _parse_datetime(event["end_datetime"])
    if not event_start or not event_end:
        return False
    return event_start < end_dt and start_dt < event_end


def _filter_events(start_datetime: str, end_datetime: str, query: str = "") -> Dict[str, Any]:
    start_dt = _parse_datetime(start_datetime)
    end_dt = _parse_datetime(end_datetime)

    if not start_dt or not end_dt:
        return {
            "status": "INVALID_ARGUMENT",
            "message": "start_datetime và end_datetime phải là thời gian hợp lệ.",
        }
    if start_dt >= end_dt:
        return {
            "status": "INVALID_ARGUMENT",
            "message": "start_datetime phải nhỏ hơn end_datetime.",
        }

    query_norm = (query or "").strip().lower()
    events = []
    for event in MOCK_CALENDAR_EVENTS:
        haystack = f"{event.get('title', '')} {event.get('notes', '')}".lower()
        if query_norm and query_norm not in haystack:
            continue
        if _event_overlaps(event, start_dt, end_dt):
            events.append(event.copy())

    return {
        "status": "SUCCESS",
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "query": query,
        "count": len(events),
        "events": events,
    }


def execute_academic_query(student_id: str) -> str:
    """Execute the original academic lookup tool."""
    student = MOCK_DATABASE.get(student_id.strip().upper())
    if student:
        return json.dumps(
            {
                "status": "SUCCESS",
                "student_id": student_id,
                "data": student,
            },
            ensure_ascii=False,
        )
    return json.dumps(
        {
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy dữ liệu sinh viên có mã '{student_id}'",
        },
        ensure_ascii=False,
    )


def execute_schedule_appointment(
    student_id: str,
    datetime_str: str,
    advisor_name: str = "PGS.TS Nguyễn Văn A",
) -> str:
    """Execute the original academic appointment booking tool."""
    return json.dumps(
        {
            "status": "SUCCESS",
            "booking_id": f"BK-{student_id}-99",
            "student_id": student_id,
            "datetime": datetime_str,
            "advisor": advisor_name,
            "message": f"Đặt lịch thành công cho sinh viên {student_id} với {advisor_name} vào lúc {datetime_str}.",
        },
        ensure_ascii=False,
    )


def execute_schedule_fetch(start_datetime: str, end_datetime: str, query: str = "") -> str:
    """Fetch personal calendar events from the mock calendar."""
    return json.dumps(
        _filter_events(start_datetime, end_datetime, query),
        ensure_ascii=False,
    )


def execute_schedule_create_event(
    title: str,
    start_datetime: str,
    end_datetime: str,
    location: str = "",
    notes: str = "",
) -> str:
    """Create a mock calendar event if the time range is valid and free."""
    validation = _filter_events(start_datetime, end_datetime)
    if validation.get("status") != "SUCCESS":
        return json.dumps(validation, ensure_ascii=False)

    if validation["count"] > 0:
        return json.dumps(
            {
                "status": "CONFLICT",
                "message": "Không thể tạo sự kiện vì khoảng thời gian này đã có lịch.",
                "conflicting_events": validation["events"],
            },
            ensure_ascii=False,
        )

    event = {
        "event_id": f"EVT-{1001 + len(MOCK_CALENDAR_EVENTS)}",
        "title": title,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "location": location,
        "notes": notes,
    }
    MOCK_CALENDAR_EVENTS.append(event)
    return json.dumps(
        {
            "status": "SUCCESS",
            "event": event,
            "message": f"Đã thêm sự kiện '{title}' vào lịch cá nhân mock.",
        },
        ensure_ascii=False,
    )


def execute_schedule_update_event(event_id: str, **updates: str) -> str:
    """Update a mock calendar event by id."""
    event = next((item for item in MOCK_CALENDAR_EVENTS if item["event_id"] == event_id), None)
    if not event:
        return json.dumps(
            {
                "status": "NOT_FOUND",
                "message": f"Không tìm thấy sự kiện có event_id '{event_id}'.",
            },
            ensure_ascii=False,
        )

    allowed_fields = {"title", "start_datetime", "end_datetime", "location", "notes"}
    clean_updates = {
        key: value
        for key, value in updates.items()
        if key in allowed_fields and value not in (None, "")
    }

    candidate = event.copy()
    candidate.update(clean_updates)
    start_dt = _parse_datetime(candidate["start_datetime"])
    end_dt = _parse_datetime(candidate["end_datetime"])
    if not start_dt or not end_dt or start_dt >= end_dt:
        return json.dumps(
            {
                "status": "INVALID_ARGUMENT",
                "message": "Thời gian cập nhật không hợp lệ.",
            },
            ensure_ascii=False,
        )

    for other in MOCK_CALENDAR_EVENTS:
        if other["event_id"] == event_id:
            continue
        if _event_overlaps(other, start_dt, end_dt):
            return json.dumps(
                {
                    "status": "CONFLICT",
                    "message": "Không thể cập nhật vì thời gian mới trùng với sự kiện khác.",
                    "conflicting_event": other,
                },
                ensure_ascii=False,
            )

    event.update(clean_updates)
    return json.dumps(
        {
            "status": "SUCCESS",
            "event": event.copy(),
            "message": f"Đã cập nhật sự kiện '{event['title']}'.",
        },
        ensure_ascii=False,
    )


def execute_schedule_delete_event(event_id: str) -> str:
    """Delete a mock calendar event by id."""
    for index, event in enumerate(MOCK_CALENDAR_EVENTS):
        if event["event_id"] == event_id:
            deleted = MOCK_CALENDAR_EVENTS.pop(index)
            return json.dumps(
                {
                    "status": "SUCCESS",
                    "deleted_event": deleted,
                    "message": f"Đã xóa sự kiện '{deleted['title']}' khỏi lịch cá nhân mock.",
                },
                ensure_ascii=False,
            )

    return json.dumps(
        {
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy sự kiện có event_id '{event_id}', nên không có gì bị xóa.",
        },
        ensure_ascii=False,
    )


TOOL_ROUTER = {
    "academic_query": execute_academic_query,
    "schedule_appointment": execute_schedule_appointment,
    "schedule_fetch": execute_schedule_fetch,
    "schedule_create_event": execute_schedule_create_event,
    "schedule_update_event": execute_schedule_update_event,
    "schedule_delete_event": execute_schedule_delete_event,
}


def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Dispatch a tool call to the execution layer."""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps(
        {"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"},
        ensure_ascii=False,
    )
