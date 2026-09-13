# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Đỗ Trọng Bình
> **Mã Sinh Viên / Mã Học viên:** 2A202602855
> **Chủ đề Lựa chọn:** Trợ lý Quản lý lịch trình cá nhân

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 2 / 5 | Có câu hỏi suy luận nhiều bước (kiểm tra lịch -> đặt lịch mới nếu trống) nhưng thường chỉ là từng câu hỏi đơn lẻ |
| **2. Tool Interaction** | 3 / 5 | Hệ thống cần kết nối đến Google Calendar của người dùng để có thể truy xuất, thao tác theo yêu cầu của người dùng |
| **3. Dynamic Decision** | 3 / 5 | Sẽ cần Agent kiểm tra lịch của người dùng trước khi có thể trả lời câu hỏi hoặc thực hiện các thao tác tiếp theo của người dùng |
| **4. Long Horizon Goal** | 2 / 5 | Chủ yếu là để hỗ trợ người dùng kiểm tra lịch, sau đó thao tác, thường là những câu hỏi đơn lẻ chứ không phải cuộc hội thoại dài nhiều lượt |
| **TỔNG ĐIỂM AGENTIC FIT** | **10 / 20** | Augmented Chatbot

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

```json
[
  {
    "step": 1,
    "query": "Mã sinh viên của tôi là 22021196",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "academic_query",
    "arguments": {
      "student_id": "22021196"
    },
    "observation": {
      "status": "NOT_FOUND",
      "message": "Không tìm thấy dữ liệu sinh viên có mã '22021196'"
    },
    "latency_ms": 1662.68
  },
  {
    "step": 2,
    "query": "Mã sinh viên của tôi là 22021196",
    "action_type": "FINAL_ANSWER",
    "thought": "Tổng hợp kết quả từ MCP Server thành công.",
    "output": "Không tìm thấy dữ liệu sinh viên có mã '22021196'",
    "latency_ms": 10.0
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
