# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Đỗ Trọng Bình
> **Mã Sinh Viên / Mã Học viên:** 2A202602855
> **Chủ đề Lựa chọn:** Trợ lý Quản lý lịch trình cá nhân

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 3 / 5 | Có câu hỏi suy luận nhiều bước (kiểm tra lịch -> đặt lịch mới nếu trống) nhưng thường chỉ là từng câu hỏi đơn lẻ |
| **2. Tool Interaction** | 4 / 5 | Hệ thống cần kết nối đến Google Calendar của người dùng để có thể truy xuất, thao tác theo yêu cầu của người dùng |
| **3. Dynamic Decision** | 3 / 5 | Sẽ cần Agent kiểm tra lịch của người dùng trước khi có thể trả lời câu hỏi hoặc thực hiện các thao tác tiếp theo của người dùng |
| **4. Long Horizon Goal** | 3 / 5 | Chủ yếu là để hỗ trợ người dùng kiểm tra lịch, sau đó thao tác, thường là những câu hỏi đơn lẻ chứ không phải cuộc hội thoại dài nhiều lượt |
| **TỔNG ĐIỂM AGENTIC FIT** | **13 / 20** | Agent đáng thử

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

```json
[
  {
    "step": 1,
    "query": "Kiểm tra tối thứ 7 tuần này, nếu rảnh thì đặt lịch đi chơi lúc 19h.",
    "action_type": "TOOL_EXECUTION",
    "thought": "OpenAI đề xuất gọi tool 'schedule_fetch' với tham số: {\"start_datetime\": \"2026-09-17T19:00:00+07:00\", \"end_datetime\": \"2026-09-17T22:00:00+07:00\"}",
    "tool_name": "schedule_fetch",
    "arguments": {
      "start_datetime": "2026-09-17T19:00:00+07:00",
      "end_datetime": "2026-09-17T22:00:00+07:00"
    },
    "observation": {
      "status": "SUCCESS",
      "start_datetime": "2026-09-17T19:00:00+07:00",
      "end_datetime": "2026-09-17T22:00:00+07:00",
      "query": "",
      "count": 1,
      "events": [
        {
          "event_id": "EVT-1004",
          "title": "Đi chơi",
          "start_datetime": "2026-09-17T19:00:00+07:00",
          "end_datetime": "2026-09-17T22:00:00+07:00",
          "location": "",
          "notes": ""
        }
      ]
    },
    "latency_ms": 3760.09
  },
  {
    "step": 2,
    "query": "Kiểm tra tối thứ 7 tuần này, nếu rảnh thì đặt lịch đi chơi lúc 19h.",
    "action_type": "FINAL_ANSWER",
    "thought": "OpenAI trả lời trực tiếp sau khi xem context/Observation hiện có.",
    "output": "Thought: Tôi đã kiểm tra lịch vào tối thứ 7 tuần này và thấy có một sự kiện \"Đi chơi\" từ 19:00 đến 22:00. Do đó, không thể đặt lịch đi chơi lúc 19:00 vì đã có sự kiện trùng thời gian.\n\nFinal Answer: Tối thứ 7 tuần này đã có lịch \"Đi chơi\" từ 19:00 đến 22:00, nên không thể đặt lịch đi chơi lúc 19:00.",
    "latency_ms": 2241.26
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [ ] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 1 lượt.
- **Kết quả đẩy Repo nộp bài:** [x] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
