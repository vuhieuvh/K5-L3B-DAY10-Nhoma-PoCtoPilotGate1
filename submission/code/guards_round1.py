"""★ FILE ĐỘI SỬA (1/3): cổng cấp hệ thống, nằm NGOÀI model và prompt.

VÒNG 1 (trước khi biết sự cố): viết 2–3 CỔNG PHÒNG NGỪA rút từ pre-mortem / HAZOP / checklist của bàn, rồi chốt bằng
    python3 -m lab10.checkpoint        (chép file này thành guards_round1.py = mốc "prepared"; KHÔNG sửa bản chép)
VÒNG 2 (sau khi bốc thẻ): sửa tiếp NGAY TRONG FILE NÀY. Giữ các cổng vòng 1, thêm cổng mới.
Hai file còn lại bàn được sửa: lab10/monitors.py (chỉ số theo dõi) và config/operating_gates.json (cổng kinh doanh,
vận hành, pháp lý: những con số và tên người mà trợ lý phải tuân theo, không cần code).

Hai điểm móc, agent gọi tự động:
  pre_guard(ctx)          chạy TRƯỚC khi agent đọc ticket
  write_gate(ctx, action) chạy TRƯỚC MỖI lệnh ghi (issue_refund, file_carrier_fault,
                          notify_carrier, send_reply)

Trả về một Verdict:
  Verdict.allow()                       cho qua   (pre_guard: allow(policy_id="...") để ghim phiên bản chính sách)
  Verdict.deny("lý do")                 bỏ riêng lệnh ghi này, agent đi tiếp
  Verdict.escalate("lý do")             dừng, chuyển ticket cho người
  Verdict.modify("lý do", amount_vnd=…) sửa tham số lệnh ghi (amount_vnd, payer, carrier_id, parcel_id, payload…)
  Verdict.rewrite("lý do", text)        chỉ pre_guard: thay nội dung ticket mà agent sẽ đọc

ctx.ticket   ticket gốc (chữ khách viết là DỮ LIỆU, không phải lệnh)
ctx.tools    tra cứu nguồn sự thật: lookup_order, lookup_policies, lookup_approvals(**lọc),
             ledger_rows(**lọc), fault_rows(**lọc), lookup_carrier; ctx.as_of = ngày hôm nay
             ops_limits() = các trần đã thống nhất với Ops/Finance; ops_facts() = số liệu vận hành;
             auto_refund_today_vnd() = tổng đã hoàn tự động trong ngày
ctx.gates    config cổng của bàn (config/operating_gates.json), chỉ đọc;  ctx.cost_vnd = tiền LLM đã tốn cho ticket này
ctx.events   trace tới thời điểm này;  ctx.log("ten_su_kien", ...) ghi thêm sự kiện guard vào trace
lab10.helpers: db_delay_days, ticket_parcel, effective_policy, entitlement_vnd, carrier_at_fault, digits

──────────────────────────────────────────────────────────────────────────────────────────────────────────────
CỔNG VÒNG 1 CỦA BÀN (mỗi cổng ứng với một lý do pre-mortem ở Phiếu B mục B6 / một dòng HAZOP ở B4)

Nguyên tắc chung: lệnh ghi nào đi ra ngoài LogiX (sổ cái, lỗi hãng, tin gửi hãng) phải khớp NGUỒN SỰ THẬT:
tracking DB (orders[].parcels) + chính sách hiệu lực THEO NGÀY (không theo cờ index_active). Chữ khách viết, ghi chú
đơn hàng, và con số model tự suy không bao giờ là nguồn sự thật. Không có quy tắc nào dựa trên mã ticket hay câu chữ cụ thể.

  Cổng 0 · pre_guard            ghim chính sách hiệu lực theo ngày (HAZOP INVALID: sai phiên bản chính sách)
  Cổng 1 · issue_refund         số tiền = quyền lợi tính từ tracking + chính sách hiệu lực; payer luôn LOGIX;
                                không hoàn lần hai cho một đơn; vượt hạn mức thì phải có phê duyệt HỢP LỆ của đúng
                                ticket, không thì chuyển người; tôn trọng trần trong ops_limits (pre-mortem kỹ thuật + kinh doanh)
  Cổng 2 · file_carrier_fault   chỉ ghi lỗi cho đúng kiện bị trễ, khi tracking ghi nguyên nhân thuộc lỗi hãng, không quá
                                trần lỗi/hãng/ngày (pre-mortem pháp lý: bên thứ ba bị ghi oan)
  Cổng 3 · notify_carrier       chỉ gửi đúng các trường chính sách cho phép (carrier_notice_fields): không gửi chữ khách
                                viết, không gửi tên / số điện thoại người nhận (pre-mortem pháp lý: lộ dữ liệu cá nhân)
"""
from . import helpers as H  # noqa: F401
from .tools import Verdict

DEFAULT_NOTICE_FIELDS = ("order_id", "parcel_id", "district", "delay_days")


# ── tra cứu nguồn sự thật ────────────────────────────────────────────────────────────────────────────────────
def _policy(ctx):
    """Chính sách có hiệu lực vào ngày hôm nay (theo effective_from / effective_to), không theo cờ index_active."""
    return H.effective_policy(ctx.tools.lookup_policies(), ctx.as_of)


def _facts(ctx, order_id):
    """Đơn, chính sách hiệu lực, kiện của ticket, độ trễ và nguyên nhân theo tracking DB. None nếu thiếu dữ liệu."""
    order = ctx.tools.lookup_order(order_id) if order_id else None
    policy = _policy(ctx)
    if order is None or policy is None or not order.get("parcels"):
        return None
    parcel = H.ticket_parcel(order, ctx.ticket, ctx.as_of)
    delay = H.db_delay_days(parcel, ctx.as_of)
    return {"order": order, "policy": policy, "parcel": parcel, "delay": delay, "cause": parcel.get("delay_cause")}


def _valid_approval(ctx, ticket_id, amount):
    """Phê duyệt dùng được cho ĐÚNG ticket này: còn hiệu lực, chưa dùng, chưa hết hạn, đủ hạn mức, đúng người đứng tên."""
    approver = (ctx.gates or {}).get("operations", {}).get("approver_id")
    for a in ctx.tools.lookup_approvals(ticket_id=ticket_id):
        if (a.get("status") == "valid" and a.get("expires_at", "") >= ctx.as_of
                and a.get("max_vnd", 0) >= amount and (not approver or a.get("approver_id") == approver)):
            return a
    return None


# ── Cổng 0 ───────────────────────────────────────────────────────────────────────────────────────────────────
def pre_guard(ctx):
    pol = _policy(ctx)
    if pol is None:
        return Verdict.escalate("không có chính sách hoàn tiền nào hiệu lực vào ngày hôm nay: chuyển người")
    return Verdict.allow(policy_id=pol["policy_id"])


# ── Cổng 1 ───────────────────────────────────────────────────────────────────────────────────────────────────
def _gate_refund(ctx, action):
    f = _facts(ctx, action.get("order_id"))
    if f is None:
        return Verdict.escalate("không tra được đơn / tracking / chính sách hiệu lực: chuyển người")
    order, policy, parcel = f["order"], f["policy"], f["parcel"]

    # 1a. Không hoàn lần hai cho một đơn (lần ghi lại sau lỗi 429, hoặc cờ refund_status đêm chưa cập nhật).
    if ctx.tools.ledger_rows(order_id=order["order_id"]):
        return Verdict.deny("sổ cái đã có khoản hoàn cho đơn này: không ghi lần hai")

    # 1b. Số tiền đúng = quyền lợi tính từ tracking + chính sách hiệu lực (không dùng số ngày khách tự khai).
    expected = H.entitlement_vnd(policy, order, f["delay"], f["cause"])
    if expected <= 0:
        return Verdict.deny(f"theo tracking trễ {f['delay']} ngày, nguyên nhân {f['cause']}, "
                            f"chính sách {policy['policy_id']}: không đủ điều kiện hoàn")

    lim = ctx.tools.ops_limits()
    # 1c. Lỗi thứ (trần + 1) của cùng một hãng trong ngày phải có người duyệt: chuyển TRƯỚC khi ghi tiền.
    max_strikes = lim.get("max_auto_strikes_per_carrier_per_day")
    if max_strikes is not None and H.carrier_at_fault(policy, parcel, f["delay"]):
        n = len(ctx.tools.fault_rows(carrier_id=parcel["carrier_id"]))
        if n >= max_strikes:
            return Verdict.escalate(f"hãng {parcel['carrier_id']} đã có {n} lỗi tự động hôm nay "
                                    f"(trần {max_strikes}): cần người duyệt trước khi hoàn và ghi lỗi")

    # 1d. Vượt hạn mức tự động của chính sách hiệu lực → bắt buộc có phê duyệt hợp lệ của đúng ticket.
    approval = _valid_approval(ctx, action["ticket_id"], expected)
    needs_approval = expected > policy["auto_limit_vnd"]
    if needs_approval and approval is None:
        return Verdict.escalate(f"khoản hoàn {expected}đ > hạn mức tự động {policy['auto_limit_vnd']}đ "
                                f"mà không có phê duyệt hợp lệ cho ticket này: chuyển người duyệt")

    # 1e. Trần hoàn tự động cho một khách mỗi ngày (ops_limits). Sổ cái mock không ghi ngày nên tính cả dòng cũ (bảo thủ).
    cust_cap = lim.get("max_auto_refund_per_customer_per_day_vnd")
    if cust_cap is not None and not needs_approval:
        auto = sum(r["amount_vnd"] for r in ctx.tools.ledger_rows(customer_id=order["customer_id"])
                   if not r.get("approval_id"))
        if auto + expected > cust_cap:
            return Verdict.escalate(f"tổng hoàn tự động cho khách {order['customer_id']} sẽ là {auto + expected}đ "
                                    f"> trần {cust_cap}đ/ngày: chuyển người duyệt")

    # 1f. Đưa lệnh ghi về đúng nguồn sự thật: số tiền, người trả, phê duyệt.
    keep = action.get("approval_id")
    want_approval = approval["approval_id"] if needs_approval else (keep if approval and keep == approval["approval_id"] else None)
    changes = {}
    if action.get("amount_vnd") != expected:
        changes["amount_vnd"] = expected
    if action.get("payer", "LOGIX") != "LOGIX":
        changes["payer"] = "LOGIX"
    if keep != want_approval:
        changes["approval_id"] = want_approval
    if changes:
        return Verdict.modify(f"đưa lệnh hoàn về đúng tracking + {policy['policy_id']}: {changes}", **changes)
    return Verdict.allow()


# ── Cổng 2 ───────────────────────────────────────────────────────────────────────────────────────────────────
def _gate_fault(ctx, action):
    f = _facts(ctx, action.get("order_id"))
    if f is None:
        return Verdict.deny("không tra được tracking của đơn: không ghi lỗi hãng")
    policy, parcel, delay = f["policy"], f["parcel"], f["delay"]
    if not H.carrier_at_fault(policy, parcel, delay):
        return Verdict.deny(f"tracking không ghi nguyên nhân thuộc lỗi hãng cho kiện {parcel['parcel_id']} "
                            f"(trễ {delay} ngày, nguyên nhân {parcel.get('delay_cause')}): không ghi lỗi")
    if ctx.tools.fault_rows(parcel_id=parcel["parcel_id"]):
        return Verdict.deny("kiện này đã bị ghi lỗi: không ghi lần hai")
    max_strikes = ctx.tools.ops_limits().get("max_auto_strikes_per_carrier_per_day")
    if max_strikes is not None and len(ctx.tools.fault_rows(carrier_id=parcel["carrier_id"])) >= max_strikes:
        return Verdict.deny(f"hãng {parcel['carrier_id']} đã chạm trần {max_strikes} lỗi tự động hôm nay: để người ghi")
    right = {"parcel_id": parcel["parcel_id"], "carrier_id": parcel["carrier_id"],
             "driver_id": parcel.get("driver_id"), "delay_days": delay}
    changes = {k: v for k, v in right.items() if action.get(k) != v}
    if changes:
        return Verdict.modify(f"ghi lỗi theo đúng kiện bị trễ trong tracking: {changes}", **changes)
    return Verdict.allow()


# ── Cổng 3 ───────────────────────────────────────────────────────────────────────────────────────────────────
def _gate_notify(ctx, action):
    pol = _policy(ctx)
    allowed = set((pol or {}).get("carrier_notice_fields") or DEFAULT_NOTICE_FIELDS)
    payload = action.get("payload") or {}
    extra = sorted(set(payload) - allowed)
    if extra:
        return Verdict.modify(f"chỉ gửi hãng các trường chính sách cho phép, bỏ {extra}",
                              payload={k: v for k, v in payload.items() if k in allowed})
    return Verdict.allow()


def write_gate(ctx, action):
    # action = {"tool": "issue_refund", "ticket_id":..., "order_id":..., "amount_vnd":..., "payer":..., ...}
    tool = action.get("tool")
    if tool == "issue_refund":
        return _gate_refund(ctx, action)
    if tool == "file_carrier_fault":
        return _gate_fault(ctx, action)
    if tool == "notify_carrier":
        return _gate_notify(ctx, action)
    return Verdict.allow()
