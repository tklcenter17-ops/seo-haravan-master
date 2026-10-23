"""Máy chủ HTTP siêu nhẹ phục vụ Telegram WebApp Dashboard và REST API."""
from __future__ import annotations

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from config import AppConfig
from db import get_db_connection
from repository import get_exchange_rate

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"


class DashboardHTTPHandler(BaseHTTPRequestHandler):
    """Handler phục vụ API JSON và giao diện HTML của Telegram WebApp Dashboard."""

    config: AppConfig | None = None

    def _send_json(self, data: Any, status: int = 200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def _send_html(self, html_content: str, status: int = 200) -> None:
        raw = html_content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        path = self.path.split("?")[0]

        if path in ("/", "/dashboard", "/webapp"):
            html_file = STATIC_DIR / "dashboard.html"
            if html_file.exists():
                content = html_file.read_text(encoding="utf-8")
                self._send_html(content)
            else:
                self._send_html("<h1>Dashboard file not found</h1>", status=404)
            return

        if path == "/api/stats":
            if not self.config:
                self._send_json({"error": "Config not loaded"}, status=500)
                return

            conn = get_db_connection(self.config.db_path)
            try:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) as cnt, COALESCE(SUM(amount_jpy), 0) as tot_jpy FROM records WHERE deleted_at IS NULL;")
                row = cur.fetchone()
                tot_records = row["cnt"]
                tot_jpy = row["tot_jpy"]

                cur.execute("SELECT COUNT(*) as cnt FROM bid_caps WHERE is_active = 1;")
                tot_caps = cur.fetchone()["cnt"]

                rate = get_exchange_rate(conn)
                tot_vnd = round(tot_jpy * rate)

                cur.execute(
                    """
                    SELECT brand, COUNT(*) as cnt
                    FROM records
                    WHERE deleted_at IS NULL
                    GROUP BY brand
                    ORDER BY cnt DESC;
                    """
                )
                brand_rows = cur.fetchall()
                brands = [
                    {"name": r["brand"].capitalize() if r["brand"] != "unknown" else "Chưa rõ", "count": r["cnt"]}
                    for r in brand_rows
                ]

                self._send_json({
                    "total_records": tot_records,
                    "total_caps": tot_caps,
                    "total_jpy": tot_jpy,
                    "total_vnd": tot_vnd,
                    "rate": rate,
                    "brands": brands,
                })
            except Exception as e:
                logger.error(f"Lỗi khi xử lý /api/stats: {e}")
                self._send_json({"error": "Không thể lấy dữ liệu thống kê"}, status=500)
            finally:
                conn.close()
            return

        if path == "/api/records":
            if not self.config:
                self._send_json([], status=500)
                return

            conn = get_db_connection(self.config.db_path)
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT id, display_name, brand, line, amount_jpy, currency, box, cosmetic_condition, material, color, auction_date, created_at
                    FROM records
                    WHERE deleted_at IS NULL
                    ORDER BY created_at DESC
                    LIMIT 100;
                    """
                )
                rows = cur.fetchall()
                records = [dict(r) for r in rows]
                self._send_json(records)
            except Exception as e:
                logger.error(f"Lỗi khi xử lý /api/records: {e}")
                self._send_json([], status=500)
            finally:
                conn.close()
            return

        if path == "/api/radars":
            # Lấy danh sách lô bật lửa đã xác minh từ cache radar
            from handlers.radar_handlers import _RADAR_CACHE
            lots = _RADAR_CACHE.get("lots") or []
            # Chỉ trả về các lot đã xác minh (is_verified_lot == True)
            verified_lots = [lot for lot in lots if lot.get("is_verified_lot", True)]
            self._send_json(verified_lots[:50])
            return

        if path == "/api/radar/audit":
            # Lấy danh sách các ca bị loại hoặc chưa rõ để quản trị viên kiểm tra
            if not self.config:
                self._send_json([], status=500)
                return

            query_params = {}
            if "?" in self.path:
                import urllib.parse
                query_params = urllib.parse.parse_qs(self.path.split("?", 1)[1])

            dec_code = query_params.get("decision_code", [None])[0]
            limit_val = 100
            try:
                if "limit" in query_params:
                    limit_val = int(query_params["limit"][0])
            except (ValueError, TypeError):
                limit_val = 100

            from repository import get_lot_audit_logs
            conn = get_db_connection(self.config.db_path)
            try:
                audit_logs = get_lot_audit_logs(conn, decision_code=dec_code, limit=limit_val)
                self._send_json(audit_logs)
            finally:
                conn.close()
            return

        if path == "/api/radar/audit_stats":
            if not self.config:
                self._send_json({}, status=500)
                return

            from repository import get_lot_audit_stats
            conn = get_db_connection(self.config.db_path)
            try:
                stats = get_lot_audit_stats(conn)
                self._send_json(stats)
            finally:
                conn.close()
            return

        if path == "/api/kanban":
            if not self.config:
                self._send_json({"items": [], "pnl": {}}, status=500)
                return

            conn = get_db_connection(self.config.db_path)
            try:
                from repository import get_kanban_items, get_kanban_pnl_summary
                items = get_kanban_items(conn)
                pnl = get_kanban_pnl_summary(conn)
                self._send_json({"items": items, "pnl": pnl})
            except Exception as e:
                logger.error(f"Lỗi khi xử lý /api/kanban: {e}")
                self._send_json({"items": [], "pnl": {}, "error": str(e)}, status=500)
            finally:
                conn.close()
            return

        # Health check endpoint
        if path == "/healthz":
            self._send_html("OK")
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
        path = self.path.split("?")[0]
        if path == "/api/radar/report_mistake":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
                data = json.loads(body)
                aid = data.get("auction_id", "")
                note = data.get("note", "")
                logger.info(f"📝 [AUDIT FEEDBACK] Báo nhầm phân loại phiên {aid}: {note}")
                self._send_json({"success": True, "message": f"Đã ghi nhận báo nhầm cho phiên {aid}"})
            except Exception as e:
                logger.warning(f"Lỗi khi nhận báo nhầm: {e}")
                self._send_json({"success": False, "error": str(e)}, status=400)
            return

        if path == "/api/kanban/move":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
                data = json.loads(body)
                item_id = int(data.get("item_id", 0))
                stage = str(data.get("stage", ""))
                from repository import update_kanban_stage
                conn = get_db_connection(self.config.db_path)
                try:
                    ok = update_kanban_stage(conn, item_id, stage)
                    self._send_json({"success": ok})
                finally:
                    conn.close()
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=400)
            return

        if path == "/api/kanban/add":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
                data = json.loads(body)
                from repository import create_kanban_item
                conn = get_db_connection(self.config.db_path)
                try:
                    item = create_kanban_item(
                        conn,
                        title=data.get("title", "Lô bật lửa"),
                        brand=data.get("brand", "unknown"),
                        auction_id=data.get("auction_id", ""),
                        stage=data.get("stage", "bidding"),
                        buy_price_jpy=int(data.get("buy_price_jpy", 0)),
                        buy_price_vnd=int(data.get("buy_price_vnd", 0)),
                        shipping_cost_vnd=int(data.get("shipping_cost_vnd", 0)),
                        repair_cost_vnd=int(data.get("repair_cost_vnd", 0)),
                        sale_price_vnd=int(data.get("sale_price_vnd", 0)),
                        image_url=data.get("image_url", ""),
                        source_url=data.get("source_url", ""),
                        notes=data.get("notes", ""),
                    )
                    self._send_json({"success": True, "item": item})
                finally:
                    conn.close()
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=400)
            return

        if path == "/api/kanban/update":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
                data = json.loads(body)
                item_id = int(data.get("item_id", 0))
                from repository import update_kanban_item
                conn = get_db_connection(self.config.db_path)
                try:
                    ok = update_kanban_item(conn, item_id, data)
                    self._send_json({"success": ok})
                finally:
                    conn.close()
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=400)
            return

        if path == "/api/kanban/delete":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
                data = json.loads(body)
                item_id = int(data.get("item_id", 0))
                from repository import delete_kanban_item
                conn = get_db_connection(self.config.db_path)
                try:
                    ok = delete_kanban_item(conn, item_id)
                    self._send_json({"success": ok})
                finally:
                    conn.close()
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=400)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        pass  # Không ghi log rác vào console


def start_dashboard_server(config: AppConfig, port: int = 8080) -> HTTPServer | None:
    """Khởi động máy chủ HTTP Dashboard trên cổng chỉ định (chạy daemon thread, tự fallback cổng nếu bận)."""
    class BoundHandler(DashboardHTTPHandler):
        pass

    BoundHandler.config = config

    target_ports = [port]
    for fallback_p in [8989, 8990, 8085, 8088, 9099]:
        if fallback_p not in target_ports:
            target_ports.append(fallback_p)

    for p in target_ports:
        try:
            server = HTTPServer(("0.0.0.0", p), BoundHandler)
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            logger.info(f"🚀 Telegram WebApp Dashboard Server đang chạy tại: http://0.0.0.0:{p}/dashboard")
            return server
        except OSError as oe:
            if oe.errno == 98 or "Address already in use" in str(oe) or getattr(oe, "winerror", None) == 10048:
                logger.info(f"Cổng {p} đang bận, tự động thử cổng tiếp theo...")
                continue
            logger.warning(f"Lỗi cổng {p}: {oe}")
        except Exception as e:
            logger.warning(f"Không thể khởi động Dashboard server trên cổng {p}: {e}")
            break
    return None
