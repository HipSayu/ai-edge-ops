"""Generates the draw.io diagrams in this folder. Usage (from app/): python docs/ppe-vision/diagrams/gen_drawio.py docs/ppe-vision/diagrams

The diagrams are customer-facing: plain Vietnamese, no source-code names. Dashed grey = planned for a later phase.
"""

import sys
from pathlib import Path
from xml.sax.saxutils import quoteattr

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

BOX = "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=12;"
GREEN = "rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=12;"
YELLOW = "rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=12;"
PLANNED = "rounded=1;whiteSpace=wrap;html=1;dashed=1;fillColor=#f5f5f5;strokeColor=#666666;fontColor=#333333;fontSize=12;"
NOTE_BOX = "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#bbbbbb;fontSize=11;align=left;spacingLeft=8;"
USECASE = "ellipse;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=12;"
USECASE_PLANNED = "ellipse;whiteSpace=wrap;html=1;dashed=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=12;"
ACTOR = "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fontSize=12;"
ACTOR_LABEL = "text;html=1;align=right;verticalAlign=middle;fontSize=12;"
DIAMOND = "rhombus;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontSize=12;"
TERMINAL = "ellipse;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=12;"
ERROR = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=12;"
FRAME = "rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#666666;verticalAlign=top;align=left;spacingLeft=10;fontStyle=1;fontSize=12;"
FRAME_DASHED = FRAME + "dashed=1;"
CYLINDER = ("shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=12;"
            "fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=12;")
ARROW = "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;endFill=1;fontSize=11;"
DASHED_ARROW = ARROW + "dashed=1;"
LINE = "html=1;endArrow=none;fontSize=11;"
TEXT = "text;html=1;align=center;verticalAlign=middle;fontSize=11;"


class Page:
    def __init__(self, name: str, width: int = 1600, height: int = 1000) -> None:
        self.name, self.width, self.height = name, width, height
        self.cells: list[str] = []
        self._n = 1

    def _id(self) -> str:
        self._n += 1
        return f"n{self._n}"

    @staticmethod
    def _text(text: str) -> str:
        return quoteattr(text.replace("\n", "<br>"))

    def vertex(self, label, x, y, w, h, style, parent="1") -> str:
        cid = self._id()
        self.cells.append(
            f'<mxCell id="{cid}" value={self._text(label)} style="{style}" vertex="1" parent="{parent}">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
        )
        return cid

    def edge(self, src, dst, label="", style=ARROW, points=()) -> str:
        cid = self._id()
        pts = "".join(f'<mxPoint x="{px}" y="{py}"/>' for px, py in points)
        arr = f'<Array as="points">{pts}</Array>' if points else ""
        self.cells.append(
            f'<mxCell id="{cid}" value={self._text(label)} style="{style}" edge="1" parent="1" source="{src}" target="{dst}">'
            f'<mxGeometry relative="1" as="geometry">{arr}</mxGeometry></mxCell>'
        )
        return cid

    def segment(self, x1, y1, x2, y2, style=ARROW, points=(), label="") -> str:
        cid = self._id()
        pts = "".join(f'<mxPoint x="{px}" y="{py}"/>' for px, py in points)
        arr = f'<Array as="points">{pts}</Array>' if points else ""
        self.cells.append(
            f'<mxCell id="{cid}" value={self._text(label)} style="{style}" edge="1" parent="1">'
            f'<mxGeometry relative="1" as="geometry"><mxPoint x="{x1}" y="{y1}" as="sourcePoint"/>'
            f'<mxPoint x="{x2}" y="{y2}" as="targetPoint"/>{arr}</mxGeometry></mxCell>'
        )
        return cid

    def diagram_xml(self) -> str:
        body = "".join(self.cells)
        return (
            f'<diagram name={quoteattr(self.name)} id="{abs(hash(self.name)) % 10**10}">'
            f'<mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" '
            f'fold="1" page="1" pageScale="1" pageWidth="{self.width}" pageHeight="{self.height}" math="0" shadow="0">'
            f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>{body}</root></mxGraphModel></diagram>'
        )


def write(filename: str, pages: list[Page]) -> None:
    xml = '<mxfile host="app.diagrams.net">' + "".join(p.diagram_xml() for p in pages) + "</mxfile>"
    (OUT / filename).write_text(xml, encoding="utf-8")
    print("wrote", filename)


# ---------------------------------------------------------------- 1. Use case
def use_case() -> Page:
    p = Page("Use case", 1100, 1400)
    step = 84  # room for the «include» arrow between neighbouring ellipses
    cases = [
        ("Đăng nhập / đăng xuất", "V"),
        ("Xem lưới camera\n(ưu tiên camera có vi phạm)", "V"),
        ("Xem chi tiết camera\nvà danh sách vi phạm", "V"),
        ("Chat hỏi đáp với trợ lý", "V"),
        ("Tra cứu quy chuẩn an toàn\n(giai đoạn sau)", "L"),
        ("Xuất báo cáo an toàn", "O"),
        ("Tải video lên camera", "O"),
        ("Đồng bộ thư mục video", "O"),
        ("Lọc theo công trường", "A"),
        ("Quản lý công trường", "A"),
        ("Quản lý node\n(thiết bị biên)", "A"),
        ("Quản lý camera", "A"),
        ("Quản lý người dùng\nvà phân quyền", "A"),
        ("Phát hiện vi phạm,\nghi sự kiện (giai đoạn sau)", "W"),
    ]
    p.vertex("Hệ thống PPE Vision", 260, 30, 420, 80 + len(cases) * step, FRAME)
    ids = [p.vertex(label, 290, 80 + i * step, 360, 60, USECASE_PLANNED if who in ("W", "L") else USECASE)
           for i, (label, who) in enumerate(cases)]

    def actor_at(rows, x):
        mid = 80 + (sum(rows) / len(rows)) * step + 30
        return p.vertex("", x, mid - 35, 40, 70, ACTOR), mid

    # People sit on the left with their name to the left, so inheritance arrows never cross a label
    viewer, y1 = actor_at([0, 1, 2, 3], 150)
    operator, y2 = actor_at([5, 6, 7], 150)
    admin, y3 = actor_at([8, 9, 10, 11, 12], 150)
    for mid, text in ((y1, "Người xem\n(VIEWER)"), (y2, "Vận hành viên\n(OPERATOR)"), (y3, "Quản trị viên\n(ADMIN)")):
        p.vertex(text, 20, mid - 20, 120, 40, ACTOR_LABEL)

    mid_assistant = 80 + 4 * step + 30
    assistant = p.vertex("Trợ lý AI\n(agent + LLM)", 820, mid_assistant - 35, 40, 70, ACTOR)
    mid_worker = 80 + 13 * step + 30
    worker = p.vertex("Bộ phát hiện\n(mô hình YOLO)", 820, mid_worker - 35, 40, 70, ACTOR)

    for i in range(0, 4):
        p.edge(viewer, ids[i], style=LINE)
    for i in range(5, 8):
        p.edge(operator, ids[i], style=LINE)
    for i in range(8, 13):
        p.edge(admin, ids[i], style=LINE)
    for i in (3, 4, 5):
        p.edge(assistant, ids[i], style=LINE)
    p.edge(worker, ids[13], style=LINE)

    inherit = "html=1;endArrow=block;endFill=0;fontSize=11;"
    p.edge(operator, viewer, "kế thừa", inherit)
    p.edge(admin, operator, "kế thừa", inherit)
    p.edge(ids[3], ids[4], "«include»", "html=1;endArrow=open;dashed=1;fontSize=11;")
    return p


# ---------------------------------------------------------------- 2. User flow
def user_flow() -> Page:
    p = Page("User flow", 1700, 1250)
    start = p.vertex("Bắt đầu", 560, 20, 100, 40, TERMINAL)
    open_ = p.vertex("Mở hệ thống", 500, 100, 220, 50, BOX)
    creds = p.vertex("Nhập tên đăng nhập và mật khẩu", 480, 190, 260, 50, BOX)
    valid = p.vertex("Hợp lệ?", 520, 280, 180, 90, DIAMOND)
    err = p.vertex("Báo lỗi\n'Sai tên đăng nhập hoặc mật khẩu'", 840, 295, 280, 60, ERROR)
    token = p.vertex("Xác thực thành công,\ntải thông tin và công trường được gán", 470, 410, 280, 60, BOX)
    grid = p.vertex("Hiển thị lưới camera\n(camera có vi phạm / có người lên đầu)", 460, 510, 300, 60, GREEN)
    action = p.vertex("Chọn hành động", 520, 620, 180, 90, DIAMOND)

    p.edge(start, open_)
    p.edge(open_, creds)
    p.edge(creds, valid)
    p.edge(valid, err, "Không")
    p.edge(err, creds, points=[(980, 215)])
    p.edge(valid, token, "Có")
    p.edge(token, grid)
    p.edge(grid, action)

    note = p.vertex("Ở mọi bước:\nbấm Đăng xuất trên thanh trên cùng", 880, 410, 280, 60, YELLOW)
    end = p.vertex("Kết thúc", 1240, 420, 120, 40, TERMINAL)
    p.edge(note, end)

    view = p.vertex("Bấm vào một camera", 120, 635, 220, 60, BOX)
    modal = p.vertex("Cửa sổ chi tiết:\nluồng video + vi phạm gần đây", 100, 735, 260, 70, GREEN)
    p.edge(action, view, "Xem camera")
    p.edge(view, modal)
    p.edge(modal, grid, points=[(80, 770), (80, 540)])

    chat = p.vertex("Chat với trợ lý", 840, 635, 200, 60, BOX)
    wants = p.vertex("Yêu cầu\nxuất báo cáo?", 840, 735, 200, 90, DIAMOND)
    answer = p.vertex("Nhận câu trả lời\n(kèm số liệu từ hệ thống)", 1160, 750, 220, 60, GREEN)
    role_ok = p.vertex("Vai trò ≥\nOPERATOR?", 840, 880, 200, 90, DIAMOND)
    deny = p.vertex("Từ chối:\nkhông đủ quyền xuất báo cáo", 1160, 895, 240, 60, ERROR)
    report = p.vertex("Trợ lý lập báo cáo,\nmở HTML / in PDF", 840, 1020, 200, 60, GREEN)
    p.edge(action, chat, "Chat")
    p.edge(chat, wants)
    p.edge(wants, answer, "Không")
    p.edge(wants, role_ok, "Có")
    p.edge(role_ok, deny, "Không")
    p.edge(role_ok, report, "Có")
    p.edge(answer, grid, points=[(1270, 540)])
    p.edge(report, grid, points=[(1500, 1050), (1500, 540)])
    p.edge(deny, grid, points=[(1560, 925), (1560, 540)])

    admin = p.vertex("Vào trang Quản trị", 520, 760, 180, 50, BOX)
    role = p.vertex("Vai trò?", 520, 850, 180, 90, DIAMOND)
    op_tasks = p.vertex("OPERATOR:\ntải video lên camera,\nđồng bộ thư mục video", 150, 865, 240, 70, GREEN)
    ad_tasks = p.vertex("ADMIN: thêm / sửa / xóa\ncông trường, node, camera, người dùng\n(và cả thao tác của OPERATOR)", 150, 985, 300, 80, GREEN)
    p.edge(action, admin, "Quản trị", points=[(610, 740)])
    p.edge(admin, role)
    p.edge(role, op_tasks, "OPERATOR")
    p.edge(role, ad_tasks, "ADMIN", points=[(610, 1025)])
    p.edge(op_tasks, grid, points=[(60, 900), (60, 540)])
    p.edge(ad_tasks, grid, points=[(40, 1025), (40, 540)])
    return p


# ---------------------------------------------------------------- 3. System architecture
def architecture() -> Page:
    """How the web talks to the backend, and how the backend talks to its infrastructure."""
    p = Page("Kiến trúc hệ thống", 1500, 900)
    users = p.vertex("Người dùng\nNgười xem · Vận hành viên\nQuản trị viên\n(trình duyệt web)", 20, 395, 200, 110, BOX)
    web = p.vertex("Máy chủ web (Nginx)\nphục vụ giao diện,\nchuyển tiếp yêu cầu /api", 340, 400, 190, 100, YELLOW)
    p.vertex("Giao thức giữa web và dịch vụ:\n• REST / JSON: dữ liệu\n• SSE: trả lời chat từng phần\n• MJPEG: luồng video camera",
             340, 530, 190, 90, NOTE_BOX)

    service = p.vertex("Dịch vụ ứng dụng (FastAPI · cổng 8200)", 640, 215, 360, 470, FRAME)
    p.vertex("Lõi nghiệp vụ\nĐăng nhập · phân quyền theo công trường\nQuản lý công trường / node / camera\nLưới camera ưu tiên · thống kê · tải video",
             660, 250, 320, 130, BOX)
    p.vertex("Bộ phát hiện vi phạm (giai đoạn sau)\nMô hình YOLO · đọc video · ghi sự kiện", 660, 410, 320, 110, PLANNED)
    p.vertex("Trợ lý AI (giai đoạn sau)\nĐiều phối · Phân tích · Quy chuẩn · Báo cáo", 660, 550, 320, 110, PLANNED)

    db = p.vertex("Cơ sở dữ liệu\nPostgreSQL\n(tài khoản, công trường, node,\ncamera, sự kiện vi phạm)", 1130, 220, 220, 110, CYLINDER)
    files = p.vertex("Kho lưu trữ tệp (volume)\nvideo camera · ảnh vi phạm\nbáo cáo · quy chuẩn · mô hình AI", 1130, 400, 230, 120, YELLOW)
    llm = p.vertex("Dịch vụ LLM bên ngoài\n(Anthropic, qua Internet)\ngiai đoạn sau", 1130, 590, 230, 130, PLANNED)
    source = p.vertex("Nguồn video\nHiện tại: tệp video mô phỏng camera\nSau này: camera RTSP tại công trường", 640, 740, 360, 80, YELLOW)

    p.edge(users, web, "HTTPS")
    p.edge(web, service, "HTTP /api")
    p.edge(service, db, "Truy vấn dữ liệu")
    p.edge(service, files)
    p.edge(service, llm, "HTTPS", DASHED_ARROW)
    p.edge(source, service, "Video", DASHED_ARROW)

    p.vertex("Chú thích: nét liền = đã có · nét đứt, màu xám = giai đoạn sau.\n"
             "Web, dịch vụ ứng dụng, cơ sở dữ liệu và kho tệp chạy bằng Docker Compose trên một máy chủ.",
             20, 760, 520, 60, NOTE_BOX)
    return p


# ---------------------------------------------------------------- 4. ERD
ENTITY = ("swimlane;fontStyle=1;childLayout=stackLayout;horizontal=1;startSize=30;horizontalStack=0;resizeParent=1;"
          "resizeParentMax=0;resizeLast=0;collapsible=0;marginBottom=0;whiteSpace=wrap;html=1;fontSize=13;")
ROW = ("text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=8;spacingRight=4;"
       "overflow=hidden;rotatable=0;whiteSpace=wrap;html=1;fontSize=12;")


def erd() -> Page:
    p = Page("ERD", 1500, 1000)

    def entity(title, rows, x, y, planned=False):
        w, rh = 290, 26
        style = ENTITY + ("fillColor=#f5f5f5;strokeColor=#666666;dashed=1;" if planned else "fillColor=#dae8fc;strokeColor=#6c8ebf;")
        eid = p.vertex(title, x, y, w, 30 + rh * len(rows), style)
        for i, text in enumerate(rows):
            p.vertex(text, 0, 30 + rh * i, w, rh, ROW, parent=eid)
        return eid

    users = entity("users  (người dùng)", ["PK  id : int", "username : varchar(50)  UQ", "password_hash : varchar(255)",
                                           "full_name : varchar(100)", "role : VIEWER | OPERATOR | ADMIN", "is_active : bool"], 40, 40)
    link = entity("user_clusters  (quyền xem)", ["PK, FK  user_id → users.id", "PK, FK  cluster_id → clusters.id"], 420, 80)
    clusters = entity("clusters  (công trường)", ["PK  id", "name : varchar(100)  UQ", "description : varchar(500)"], 800, 40)
    nodes = entity("nodes  (thiết bị biên)", ["PK  id", "FK  cluster_id → clusters.id", "name : varchar(100)",
                                              "max_cameras : int = 16"], 800, 270)
    cameras = entity("cameras", ["PK  id", "FK  node_id → nodes.id", "name : varchar(100)",
                                 "zone : varchar(100)  null", "enabled : bool"], 800, 510)
    events = entity("violation_events  (vi phạm)", ["PK  id : int", "FK  camera_id → cameras.id", "violation_type : varchar(40)",
                                                    "confidence : float", "video_ts_sec : float", "created_at : timestamptz",
                                                    "snapshot_path : varchar(255)  null"], 800, 760)
    reports = entity("reports  (giai đoạn sau)", ["PK  id : uuid", "FK  user_id → users.id", "title : varchar",
                                                   "html_path : varchar", "created_at : timestamptz"], 40, 420, planned=True)

    rel = "fontSize=12;html=1;endArrow=ERmany;startArrow=ERmandOne;endFill=0;startFill=0;"
    p.edge(users, link, "1 — N", "edgeStyle=entityRelationEdgeStyle;" + rel)
    p.edge(clusters, link, "1 — N", "edgeStyle=entityRelationEdgeStyle;" + rel)
    p.edge(clusters, nodes, "1 — N", "edgeStyle=orthogonalEdgeStyle;" + rel)
    p.edge(nodes, cameras, "1 — N", "edgeStyle=orthogonalEdgeStyle;" + rel)
    p.edge(cameras, events, "1 — N", "edgeStyle=orthogonalEdgeStyle;" + rel)
    p.edge(users, reports, "1 — N", "edgeStyle=orthogonalEdgeStyle;dashed=1;" + rel)

    p.vertex("Quy tắc dữ liệu:\n• Công trường → node → camera: một công trường có nhiều node, một node có nhiều camera\n"
             "• Người dùng chỉ thấy camera thuộc công trường được gán (Quản trị viên thấy tất cả)\n"
             "• Video của camera lưu theo thư mục video/{công trường}/{node}/{camera}/\n"
             "• Mã công trường, node, camera không bao giờ được tái sử dụng\n"
             "• Xóa công trường kéo theo xóa node, camera và sự kiện của nó (tệp video được giữ lại)",
             40, 700, 600, 150, "rounded=1;whiteSpace=wrap;html=1;align=left;spacingLeft=10;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=12;")
    return p


# ---------------------------------------------------------------- 5. Sequence diagrams
def sequence(name, actors, steps) -> Page:
    gap, x0, top = 240, 130, 30
    xs = [x0 + i * gap for i in range(len(actors))]
    p = Page(name, x0 + gap * len(actors) + 100, 1400)

    # pass 1: assign a y to every step
    y = top + 44 + 50
    layout, frames, open_frames = [], [], []
    for step in steps:
        kind = step[0]
        if kind == "begin":
            open_frames.append((step[1], step[2], step[3], y - 20, len(open_frames)))
            y += 38
        elif kind == "end":
            label, a, b, y0, depth = open_frames.pop()
            frames.append((label, a, b, y0, y + 4, depth))
            y += 36
        elif kind == "else":
            _, a, b, _, depth = open_frames[-1]
            layout.append(("else", step[1], y, a, b, depth))
            y += 46
        elif kind == "self":
            layout.append(("self", step[1], step[2], y))
            y += 60
        elif kind == "note":
            layout.append(("note", step[1], step[2], y))
            y += 62
        else:
            layout.append((kind, step[1], step[2], step[3], y))
            y += 52 + 12 * step[3].count("\n")
    y_end = y + 10

    for i, (label, is_planned) in enumerate(actors):
        p.vertex(label, xs[i] - 85, top, 170, 44, PLANNED if is_planned else BOX)
        p.segment(xs[i], top + 44, xs[i], y_end, "html=1;endArrow=none;dashed=1;strokeColor=#999999;")
    def tag(label, x, y, bold):
        # white background so a lifeline never strikes through the text
        width = int(len(label) * (7.4 if bold else 6.6)) + 14
        style = f"text;html=1;align=left;verticalAlign=middle;fontSize=12;fillColor=#ffffff;fontStyle={1 if bold else 2};"
        p.vertex(label, x, y, width, 20, style)

    for label, a, b, y0, y1, depth in frames:
        inset = depth * 14  # a nested frame sits inside its parent instead of on top of its border
        p.vertex("", xs[a] - 110 + inset, y0, xs[b] - xs[a] + 220 - 2 * inset, y1 - y0, FRAME_DASHED)
        tag(label, xs[a] - 104 + inset, y0 + 3, True)

    for item in layout:
        kind = item[0]
        if kind in ("msg", "ret"):
            _, a, b, label, yy = item
            style = "html=1;endArrow=block;endFill=1;" if kind == "msg" else "html=1;endArrow=open;dashed=1;"
            p.segment(xs[a], yy, xs[b], yy, style)
            left, right = min(xs[a], xs[b]), max(xs[a], xs[b])
            height = 15 * (label.count("\n") + 1) + 6
            text_w = int(max(len(line) for line in label.split("\n")) * 6.4) + 14  # just wide enough for the text
            p.vertex(label, (left + right) // 2 - text_w // 2, yy - height - 2, text_w, height, TEXT + "fillColor=#ffffff;")
        elif kind == "self":
            _, a, label, yy = item
            p.segment(xs[a], yy, xs[a], yy + 30, "html=1;endArrow=block;endFill=1;", points=[(xs[a] + 60, yy), (xs[a] + 60, yy + 30)])
            p.vertex(label, xs[a] + 66, yy - 4, 200, 38, "text;html=1;align=left;verticalAlign=middle;fontSize=11;whiteSpace=wrap;")
        elif kind == "note":
            _, a, text, yy = item
            p.vertex(text, xs[a] - 90, yy - 6, 220, 46, "shape=note;whiteSpace=wrap;html=1;size=10;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=11;")
        elif kind == "else":
            _, label, yy, a, b, depth = item
            inset = depth * 14
            p.segment(xs[a] - 110 + inset, yy, xs[b] + 110 - inset, yy, "html=1;endArrow=none;dashed=1;strokeColor=#666666;")
            tag(label, xs[a] - 104 + inset, yy + 4, False)
    p.height = y_end + 60
    return p


def sequences() -> list[Page]:
    s1 = sequence(
        "S1 Đăng nhập và xem lưới camera",
        [("Trình duyệt", False), ("Máy chủ API", False), ("Cơ sở dữ liệu", False)],
        [
            ("msg", 0, 1, "Đăng nhập: tên đăng nhập + mật khẩu"),
            ("msg", 1, 2, "tra cứu tài khoản"),
            ("ret", 2, 1, "thông tin tài khoản"),
            ("self", 1, "kiểm tra mật khẩu;\ncấp phiên đăng nhập"),
            ("ret", 1, 0, "phiên đăng nhập + hồ sơ người dùng"),
            ("begin", "lặp lại mỗi 3 giây", 0, 2),
            ("msg", 0, 1, "Xin lưới camera"),
            ("msg", 1, 2, "lấy camera và số vi phạm\n60 giây gần nhất"),
            ("ret", 2, 1, "dữ liệu camera"),
            ("self", 1, "lọc theo công trường được gán;\nxếp hạng ưu tiên"),
            ("ret", 1, 0, "danh sách camera đã sắp ưu tiên"),
            ("end",),
            ("note", 1, "Công trường hoặc camera ngoài\nphạm vi quyền: bị từ chối"),
        ],
    )
    s2 = sequence(
        "S2 Tải video và đồng bộ thư mục (Operator)",
        [("Trình duyệt", False), ("Máy chủ API", False), ("Cơ sở dữ liệu", False), ("Kho video", False)],
        [
            ("msg", 0, 1, "Tải video lên một camera"),
            ("msg", 1, 2, "camera có trong phạm vi quyền?"),
            ("ret", 2, 1, "camera, node, công trường"),
            ("begin", "nếu không hợp lệ", 0, 3),
            ("ret", 1, 0, "từ chối: ngoài phạm vi / không phải video"),
            ("else", "nếu hợp lệ"),
            ("msg", 1, 3, "lưu video vào thư mục\ncủa camera"),
            ("ret", 1, 0, "đã lưu video"),
            ("end",),
            ("msg", 0, 1, "Đồng bộ thư mục video"),
            ("msg", 1, 2, "lấy danh sách camera"),
            ("ret", 2, 1, "danh sách camera"),
            ("msg", 1, 3, "tạo thư mục còn thiếu;\nquét thư mục video"),
            ("ret", 3, 1, "thư mục hiện có"),
            ("ret", 1, 0, "báo cáo: số camera, số video,\nthư mục không khớp camera nào"),
            ("note", 1, "Thư mục không khớp camera nào\nchỉ được báo cáo, không tự tạo camera"),
        ],
    )
    s3 = sequence(
        "S3 Phát hiện vi phạm (giai đoạn sau)",
        [("Bộ phát hiện", True), ("Kho video", False), ("Mô hình YOLO", True), ("Cơ sở dữ liệu", False), ("Máy chủ API", False), ("Trình duyệt", False)],
        [
            ("begin", "lặp lại liên tục", 0, 1),
            ("msg", 0, 1, "đọc khung hình (hết video thì phát lại)"),
            ("ret", 1, 0, "khung hình"),
            ("end",),
            ("begin", "cứ vài khung hình", 0, 3),
            ("msg", 0, 2, "nhận diện khung hình"),
            ("ret", 2, 0, "các đối tượng: người, mũ, thiếu mũ…"),
            ("self", 0, "vẽ khung nhận diện;\ngiữ khung hình mới nhất"),
            ("begin", "nếu có vi phạm và đã qua thời gian chờ", 0, 3),
            ("msg", 0, 3, "ghi sự kiện vi phạm"),
            ("msg", 0, 1, "lưu ảnh chụp vi phạm"),
            ("end",),
            ("end",),
            ("msg", 5, 4, "Xem luồng video camera"),
            ("ret", 4, 5, "video liên tục (khung hình mới nhất)"),
        ],
    )
    s4 = sequence(
        "S4 Chat và xuất báo cáo (giai đoạn sau)",
        [("Trình duyệt", False), ("Máy chủ API", False), ("Agent điều phối", True), ("Agent phân tích", True),
         ("Agent quy chuẩn", True), ("Agent báo cáo", True), ("Mô hình LLM", True)],
        [
            ("msg", 0, 1, "Gửi yêu cầu: \"Xuất báo cáo\""),
            ("msg", 1, 2, "chuyển yêu cầu + quyền\ncủa người dùng"),
            ("msg", 2, 6, "chọn công cụ cần dùng"),
            ("msg", 2, 3, "giao việc: phân tích"),
            ("self", 3, "tra cứu vi phạm\n(chỉ trong phạm vi quyền)"),
            ("ret", 3, 2, "kết quả phân tích + bằng chứng"),
            ("msg", 2, 4, "giao việc: tra quy chuẩn"),
            ("self", 4, "tra cứu quy chuẩn\n(trích dẫn kèm nguồn)"),
            ("ret", 4, 2, "điều khoản + nguồn"),
            ("begin", "nếu vai trò từ OPERATOR trở lên", 1, 6),
            ("msg", 2, 5, "giao việc: lập báo cáo"),
            ("self", 5, "lập báo cáo\n(tài liệu HTML)"),
            ("ret", 5, 2, "đường dẫn báo cáo"),
            ("else", "nếu là VIEWER"),
            ("ret", 2, 1, "từ chối: không đủ quyền"),
            ("end",),
            ("ret", 1, 0, "tiến độ xử lý + câu trả lời (từng phần)"),
            ("ret", 1, 0, "liên kết báo cáo · hoàn tất"),
        ],
    )
    return [s1, s2, s3, s4]


write("01-use-case.drawio", [use_case()])
write("02-user-flow.drawio", [user_flow()])
write("03-architecture.drawio", [architecture()])
write("04-erd.drawio", [erd()])
write("05-sequence.drawio", sequences())
