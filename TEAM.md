# Team

## Thông tin nhóm

- Tên nhóm (`TenNhom`, không dấu, không khoảng trắng): Nhoma
- Lớp: `L3B`
- Repo của bàn: `K5_L3B_Day10_Nhoma_PoC-to-Pilot_Gate1_student` (https://github.com/vuhieuvh/K5_L3B_Day10_Nhoma_PoC-to-Pilot_Gate1_student). Bàn giữ tên repo đã tạo từ đầu buổi; giá trị `team` trong Bản tiêu chí đã ký và `submission/submission.json` giống hệt tên này.
- Thẻ sự cố đã bốc (S1–S8): S3 · Hãng miền Tây bị phạt vì bão

## Thành viên

Họ tên đầy đủ và MSSV của **mọi** thành viên; bàn 3 người thì để trống dòng 4. Vai: Kỹ sư cổng · Sản phẩm và kinh doanh · Vận hành và pháp lý (README mục 3, phút 0–15).

| STT | Họ và tên | MSSV | Vai | Trưởng nhóm |
| --: | --------- | ---- | --- | :---------: |
|   1 | Vũ Xuân Hiếu | 2A202603860 | Sản phẩm và kinh doanh (Người 1) · GitHub `vuhieuvh` | ✓ |
|   2 | Nguyễn Thế Bảo | 2A202603825 | Kỹ sư cổng: viết và sửa cổng (Người 2) · GitHub `NTheBao` | |
|   3 | Nguyễn Thanh Tùng | 2A202603808 | Vận hành và pháp lý (Người 3) · GitHub `thanhtung578804` | |
|   4 | Vũ Duy Khánh | 2A202603865 | Kỹ sư cổng: đo lường và giám sát (Người 4) · GitHub `khanhduyvu1` | |

Ghi `members` trong `submission/submission.json` theo dạng `"HoVaTen-MSSV"`, khớp bảng trên. *(Bàn ghi theo quy ước lớp: `"<MSHV>-<Họ_và_tên>-<github_account_name>"`.)*

## Cá nhân

Mỗi thành viên tự viết một mục bên dưới (chép mẫu, đổi tiêu đề thành họ tên không dấu và MSSV, ví dụ `## NguyenVanAn-20241234`).

## VuXuanHieu-2A202603860

### Phần việc phụ trách

Trưởng nhóm, vai Sản phẩm và kinh doanh. Câu 1.x (Phiếu A: A1–A5, đặt và ký Bản tiêu chí chấp nhận `config/acceptance_criteria.json`), câu 2.3 (Phiếu B mục B3, bản đồ dữ liệu), cổng kinh doanh trong `config/operating_gates.json` mục `business`, quyết định Gate 1 v1 (B8) và v2 (Phiếu C mục C12), điều phối repo.

### Đóng góp cụ thể

- Đặt 5 ngưỡng bắt buộc, 3 ngưỡng `business_ops`, điều kiện dừng và `decision_rule` bốn dòng, ký trước lần đo đầu tiên.
- Chọn trần tiền hoàn ngày `daily_refund_cap_vnd = 1.600.000` và ngân sách LLM 1.500đ/ticket.
- Đọc bảng `policies` cho thẻ S3 (C3.5): `index_active` là bản sao không chủ, `fault_causes` đổi theo phiên bản.
- Viết quyết định v1 "Tiếp tục có điều kiện" và v2 "Tiếp tục" dựa trên report ba mốc.

### Bằng chứng

Commit ký `d6a3d28` (hash tiêu chí `6830c237`); commit `f40430a` (chốt vòng 1, quyết định v1); lần chạy `R-base-prepared-20261119-152604-2dbccd`, `R-S3-grade-20261119-170341-d3e3f6`; Phiếu A A1–A5, Phiếu B B3, B8, Phiếu C C3.5, C12.

### Exit ticket

Học được: quyết định Gate 1 "đạt" là quyết định khớp với số liệu và tiêu chí đã ký trước, không phải quyết định "đi tiếp"; ký trước khi đo để không dời cột gôn. Còn chưa chắc: ngưỡng 0 lỗi oan cho hãng có quá chặt khi chạy thật ở quy mô lớn hay không, và làm sao định lượng chi phí của việc chậm hoàn cho khách.

## NguyenTheBao-2A202603825

### Phần việc phụ trách

Kỹ sư cổng, viết và sửa cổng. Câu 2.4–2.6 (Phiếu B mục B4 HAZOP, B7), câu 3.5 (Phiếu C mục C7). File `lab10/guards.py` (vòng 1 và vòng 2).

### Đóng góp cụ thể

- Vòng 1: Cổng 0 `pre_guard` ghim chính sách theo ngày; Cổng 1 `issue_refund` (không hoàn lần hai, số tiền theo tracking và chính sách, payer LOGIX, phê duyệt hợp lệ, trần khách và hãng); Cổng 2 `file_carrier_fault` (chỉ ghi lỗi khi có nguyên nhân thuộc `fault_causes`, đúng kiện, trần 2 lỗi/hãng/ngày); Cổng 3 `notify_carrier` (chỉ gửi trường được phép).
- Vòng 2 (thẻ S3): Cổng 1c tách "hoàn cho khách" khỏi "trần lỗi hãng", nên khách đủ điều kiện không bị chuyển người; Cổng 3a không gửi tin báo lỗi khi kiện không có lỗi được ghi.

### Bằng chứng

`lab10/guards_round1.py` (chốt `c12cb9f1`); lần chạy `R-S3-after-20261119-164759-89d45e` (tỉ lệ chuyển người 0,25 → 0,083, chi phí 6.038đ → 4.405đ, an toàn giữ 0); Phiếu B B4, Phiếu C C7.

### Exit ticket

Học được: cổng chặn đúng tác hại vẫn có thể gây hại phụ (chặn luôn khoản hoàn của khách); phải đọc cả khối kinh doanh và vận hành chứ không chỉ chỉ số an toàn. Còn chưa chắc: cổng tin tracking DB, nên khi chính `delay_cause` bị nhập sai thì chưa có cách chặn.

## NguyenThanhTung-2A202603808

### Phần việc phụ trách

Vận hành và pháp lý. Câu 2.10 (Phiếu B mục B5 checklist, B7.5–B7.6 runbook 1–3, giờ cao điểm), câu 3.7 (Phiếu C mục C10 risk register, C11 checklist và runbook 4–5). File `config/operating_gates.json` mục `operations`, `legal`; `submission/submission.json`.

### Đóng góp cụ thể

- Điền PIC (NV-TUNG), người duyệt (NV-HANH), người nhận khiếu nại (NV-OANH), số người trực, thời gian chờ tối đa 45 phút, kiểm mẫu 10%, kênh báo tin, điều kiện dừng.
- Cổng pháp lý: không gửi `recipient_contact`, `customer_note` cho hãng; ghi lỗi hãng phải có nguyên nhân trong tracking.
- Vòng 2 (thẻ S3): thêm hai điều kiện dừng (đối chiếu chính sách với phụ lục ngày đổi phiên bản; ngưỡng của hai monitor mới), runbook 4–5, risk register về `delay_cause` mùa bão.

### Bằng chứng

Lần chạy `R-S3-after-20261119-164843-d3e3f6` (config vòng 2); Phiếu B B5, B7.5, B7.6; Phiếu C C10, C11; `config/operating_gates.json` `stop_conditions` câu 5–6.

### Exit ticket

Học được: sự cố S3 lộ ra qua khiếu nại của hãng chứ không qua số máy đo; runbook cần tín hiệu không cần nhãn. Còn chưa chắc: quy trình nhận phụ lục hợp đồng từ phòng kinh doanh sang người giữ cấu hình trợ lý sẽ chạy thế nào ngoài thực tế.

## VuDuyKhanh-2A202603865

### Phần việc phụ trách

Kỹ sư cổng, đo lường và giám sát. Chạy `lab10.eval`, `lab10.trace`, `lab10.grade`; Phiếu B mục B0, B1, B2 (soát lỗi), B7.1–B7.3 (thử tình huống); Phiếu C mục C0, C1, C2, C4–C6, C8, C9. File `lab10/monitors.py`.

### Đóng góp cụ thể

- Chạy đánh giá ba mốc, dò trace `T-002@55` (vòng 1) và `S3-01@11`, `S3-20@11`, `S3-42@11` (thẻ S3); xếp loại lỗi (lỗi chìm, lỗi ngữ cảnh, giới hạn hệ thống).
- Thử giờ cao điểm (1 người duyệt: 11 ca ùn; 2 người: 0 ca ùn) và 7 tình huống tự dựng.
- Vòng 2: viết hai monitor `unverified_fault_proposal_rate` và `max_faults_per_carrier_day`, cả hai sáng đèn trên thẻ S3; vẽ fault tree trước và sau khi sửa.

### Bằng chứng

Lần chạy `R-base-before-20261119-152104-b45eeb`, `R-S3-prepared-20261119-164522-2dbccd`, `R-S3-after-20261119-164817-19bda3`, grade `R-S3-grade-20261119-170341-d3e3f6` (ô 6 monitor); Phiếu C C0, C2, C6, C8, C9.

### Exit ticket

Học được: monitor tốt đọc ý định của agent (trước cổng) nên vẫn báo khi cổng đã chặn hết tác hại; pass_rate 1,0 trên bộ thử không có nghĩa là hết rủi ro. Còn chưa chắc: ngưỡng báo động 0,10 của `unverified_fault_proposal_rate` đặt từ mock, cần đo lại trên dữ liệu thật.
