"""★ FILE ĐỘI SỬA (2/3): chỉ số theo dõi (monitor). Thêm ÍT NHẤT MỘT chỉ số bắt được sự cố của bàn.

Mỗi monitor nhận danh sách trial (KHÔNG có nhãn đúng/sai, giống production) và trả về một số.
Một trial = {"ticket_id", "seed", "day", "status", "amount_vnd", "ticket", "events", "ledger", "faults", "outbound",
             "arrive_min", "warehouse", "cost_vnd", "review_kind", "queue_wait_min", "queue_stuck"}
  "day"            một ngày vận hành giả lập: các ticket cùng "day" và cùng "seed" chạy nối nhau trên cùng một sổ cái
  "arrive_min"     phút ticket tới trong ca (0..480)          "warehouse"   kho của đơn
  "cost_vnd"       tiền LLM + nền tảng đã tốn cho ticket      "review_kind" None / "escalated" (trợ lý chuyển người) /
  "queue_wait_min" số phút chờ người duyệt (None nếu không vào hàng chờ)     "recheck" (nhân viên tự kiểm lại)
Chỉ số có thể là kỹ thuật (tỉ lệ model đè số trong ticket lên DB), vận hành (số ca cần người trong giờ đông nhất),
hay kinh doanh (tỉ lệ ticket trợ lý đọc xong vẫn phải chuyển người).

lab10.grade kiểm: monitor chạy không lỗi, và giá trị trên gói sự cố khác giá trị trên bộ nền,
tức là monitor "sáng đèn" khi sự cố xảy ra.
"""


def escalation_rate(trials):
    return sum(t["status"] == "escalated" for t in trials) / max(1, len(trials))


def _first(events, kind):
    return next((e for e in events if e.get("type") == kind), None)


def unverified_fault_proposal_rate(trials):
    """[Thẻ S3] Tỉ lệ ticket mà trợ lý ĐỀ XUẤT ghi lỗi hãng trong khi tracking không ghi rõ lỗi do hãng
    (nguyên nhân trống, hoặc khác CARRIER như FORCE_MAJEURE bão lũ).

    Đọc ý định của agent (sự kiện `proposal`, trước khi qua cổng), không đọc kết quả, nên vẫn "sáng đèn" cả khi
    Cổng 2 đã chặn: đèn sáng = model đang trôi khỏi chính sách (concept drift) và chỉ còn một lớp cổng đỡ.
    Mẫu số: ticket có sự kiện tracking (đã tra được đơn). Thiếu tracking / proposal thì không tính vào tử số.
    """
    seen = hit = 0
    for t in trials:
        tr = _first(t["events"], "tracking")
        if tr is None:
            continue
        seen += 1
        prop = _first(t["events"], "proposal") or {}
        if prop.get("do_fault") and (not tr.get("cause_recorded") or tr.get("cause") != "CARRIER"):
            hit += 1
    return round(hit / max(1, seen), 4)


def max_faults_per_carrier_day(trials):
    """[Thẻ S3] Số lỗi hãng nhiều nhất mà MỘT hãng nhận trong MỘT ngày vận hành giả lập (cùng day + seed).

    Bắt triệu chứng "bên em nhận liền mấy lỗi một ngày, không ai xác nhận". Đếm lỗi đã thật sự ghi (trial['faults']),
    nên đo được cả khi chính sách đúng nhưng một hãng bị dồn lỗi. So với trần max_auto_strikes_per_carrier_per_day = 2.
    """
    per = {}
    for t in trials:
        for f in t.get("faults") or []:
            key = (t.get("day"), t.get("seed"), f.get("carrier_id"))
            per[key] = per.get(key, 0) + 1
    return max(per.values(), default=0)


MONITORS = {
    "escalation_rate": escalation_rate,     # có sẵn; KHÔNG tính là metric mới của đội
    "unverified_fault_proposal_rate": unverified_fault_proposal_rate,   # bàn Nhoma, thẻ S3
    "max_faults_per_carrier_day": max_faults_per_carrier_day,           # bàn Nhoma, thẻ S3
}
STARTER_MONITORS = ("escalation_rate",)
