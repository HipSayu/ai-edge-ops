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


CREATE TABLE clusters (
	id SERIAL NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	description VARCHAR(500), 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE users (
	id SERIAL NOT NULL, 
	username VARCHAR(50) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	full_name VARCHAR(100) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (username)
);

CREATE TABLE nodes (
	id SERIAL NOT NULL, 
	cluster_id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	max_cameras INTEGER NOT NULL, 
	description VARCHAR(500), 
	ip_address VARCHAR(64), 
	PRIMARY KEY (id), 
	FOREIGN KEY(cluster_id) REFERENCES clusters (id) ON DELETE CASCADE
);

CREATE INDEX ix_nodes_cluster_id ON nodes (cluster_id);

CREATE TABLE user_clusters (
	user_id INTEGER NOT NULL, 
	cluster_id INTEGER NOT NULL, 
	PRIMARY KEY (user_id, cluster_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(cluster_id) REFERENCES clusters (id) ON DELETE CASCADE
);

CREATE TABLE cameras (
	id SERIAL NOT NULL, 
	node_id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	zone VARCHAR(100), 
	enabled BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(node_id) REFERENCES nodes (id) ON DELETE CASCADE
);

CREATE INDEX ix_cameras_node_id ON cameras (node_id);

CREATE TABLE violation_events (
	id SERIAL NOT NULL, 
	camera_id INTEGER NOT NULL, 
	violation_type VARCHAR(40) NOT NULL, 
	confidence FLOAT NOT NULL, 
	video_ts_sec FLOAT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	snapshot_path VARCHAR(255), 
	PRIMARY KEY (id), 
	FOREIGN KEY(camera_id) REFERENCES cameras (id) ON DELETE CASCADE
);

CREATE INDEX ix_violation_events_camera_id ON violation_events (camera_id);

CREATE INDEX ix_violation_events_created_at ON violation_events (created_at);

CREATE INDEX ix_violation_events_violation_type ON violation_events (violation_type);

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
