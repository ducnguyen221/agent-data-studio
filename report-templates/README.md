# report-templates/ — Kit VISUAL trang báo cáo (PBIR) cho tool `apply_template`

Mỗi thư mục con = 1 **template kit**: một **trang báo cáo (report page, PBIR)** đẹp đã "chưng cất"
thành text (`kit.json` + `blueprint.md` + `blocks/*.json` verbatim + `_page.json`) để agent tái tạo
bằng clone-and-rebind — style giữ nguyên 100%, chỉ đổi binding field.

- Tool liên quan: `list_templates` (liệt kê kit ở đây + env `POWERBI_TEMPLATES_DIR`) ·
  `apply_template` (kit → trang mới) · `distill_template` (trang đẹp → kit mới).
- Kit đi kèm: [`kpim-business-light/`](kpim-business-light/README.md) (12 block, đã sanitize).
- Kit chứa binding nghiệp vụ THẬT → để NGOÀI repo (env `POWERBI_TEMPLATES_DIR`);
  muốn chia sẻ → distill với `sanitize=True`.
