"""Writes docs/db/schema.sql (PostgreSQL) from the SQLAlchemy models, so the file never drifts from the code.

Run from app/:  python docs/db/generate_schema.py
"""

import sys
from pathlib import Path

sys.path.insert(0, ".")

from sqlalchemy.dialects import postgresql  # noqa: E402
from sqlalchemy.schema import CreateIndex, CreateTable  # noqa: E402

from src.ppe.infrastructure.persistence.models import Base  # noqa: E402

HEADER = """\
-- PPE Vision: cấu trúc cơ sở dữ liệu (PostgreSQL 16)
--
-- File này được sinh tự động từ mô hình dữ liệu của ứng dụng, đừng sửa tay.
-- Sinh lại:  python docs/db/generate_schema.py   (chạy từ thư mục app/)
--
-- Ứng dụng tự tạo bảng khi khởi động và nạp dữ liệu mẫu (tài khoản demo, 1 công trường, 1 node).
-- File này dùng để cấp cho khách, hoặc để dựng cơ sở dữ liệu thủ công:
--   psql -U ppe -d ppe -f docs/db/schema.sql
--
-- Quan hệ:  clusters 1—N nodes 1—N cameras 1—N violation_events
--           users N—M clusters (qua user_clusters)
"""

COMMENTS = """\
COMMENT ON TABLE clusters IS 'Công trường. Cấp cao nhất; người dùng được gán theo công trường.';
COMMENT ON TABLE nodes IS 'Thiết bị biên trong một công trường; một node phục vụ nhiều camera.';
COMMENT ON TABLE cameras IS 'Nguồn video gắn vào một node. Video lưu ở video/{cluster_id}/{node_id}/{camera_id}/.';
COMMENT ON TABLE users IS 'Tài khoản đăng nhập. Mật khẩu chỉ lưu dạng băm.';
COMMENT ON TABLE user_clusters IS 'Công trường mà mỗi người dùng được xem. ADMIN xem tất cả nên không cần dòng ở đây.';
COMMENT ON TABLE violation_events IS 'Mỗi vi phạm PPE phát hiện được, kèm độ tin cậy và ảnh chụp.';

COMMENT ON COLUMN users.role IS 'VIEWER, OPERATOR hoặc ADMIN.';
COMMENT ON COLUMN nodes.max_cameras IS 'Số camera tối đa một node phục vụ; vượt quá thì từ chối tạo camera mới.';
COMMENT ON COLUMN cameras.zone IS 'Vị trí tự do (tầng, cổng...) dùng để mô tả, không dùng để phân quyền.';
COMMENT ON COLUMN violation_events.violation_type IS 'no_helmet, no_vest, no_gloves hoặc no_safety_boots.';
COMMENT ON COLUMN violation_events.video_ts_sec IS 'Thời điểm trong video (giây) nơi phát hiện vi phạm.';
COMMENT ON COLUMN violation_events.snapshot_path IS 'Đường dẫn ảnh chụp, tương đối so với thư mục dữ liệu.';
"""


def main() -> None:
    dialect = postgresql.dialect()
    parts = [HEADER]
    for table in Base.metadata.sorted_tables:  # dependency order: parents before children
        parts.append(str(CreateTable(table).compile(dialect=dialect)).strip() + ";")
        for index in sorted(table.indexes, key=lambda i: i.name):
            parts.append(str(CreateIndex(index).compile(dialect=dialect)).strip() + ";")
    parts.append(COMMENTS)
    target = Path(__file__).with_name("schema.sql")
    target.write_text("\n\n".join(parts).rstrip() + "\n", encoding="utf-8")
    print("wrote", target)


if __name__ == "__main__":
    main()
