"""
HTTP routes: auth (register, login, logout), chat page, and health check.
"""
import json
import re
import uuid
from pathlib import Path
from urllib.parse import urlparse

import requests
from flask import Response, jsonify, make_response, redirect, render_template, request, send_from_directory, session, stream_with_context, url_for
from markupsafe import escape
from werkzeug.utils import secure_filename

from app.auth import (
    REMEMBER_COOKIE_NAME as _REMEMBER_COOKIE_NAME,
    clear_remember_token_from_disk,
    create_remember_token,
    get_user_by_credentials,
    get_user_by_id,
    load_remember_token,
    load_remember_token_from_disk,
    register_user,
    reset_password,
    save_remember_token_to_disk,
)
from sqlalchemy.exc import OperationalError

from app.config import Config
from app.models import AcroScore, AuditLog, IgnoreList, Message, MessageReport, RolePermission, Room, RoomMute, User, db


def _can_export_all(user):
    """True if user can export all rooms (Surfer Girl or has export_all permission)."""
    if getattr(user, "is_super_admin", False):
        return True
    rank = (getattr(user, "rank", None) or "rookie").lower()
    if rank == "super_admin":
        return True
    rp = RolePermission.query.filter_by(role=rank, permission="export_all").first()
    return rp and rp.allowed


def _user_permissions(user):
    """Return dict of permission -> bool for user. Surfer Girl has all True."""
    perms = ("create_room", "update_room", "delete_room", "kick_user", "set_user_rank", "acrobot_control", "homer_control", "frink_control", "reset_stats", "export_all")
    if getattr(user, "is_super_admin", False):
        return {p: True for p in perms}
    rank = (getattr(user, "rank", None) or "rookie").lower()
    if rank == "super_admin":
        return {p: True for p in perms}
    result = {}
    for p in perms:
        rp = RolePermission.query.filter_by(role=rank, permission=p).first()
        result[p] = rp and rp.allowed
    return result


def _is_schema_out_of_date_error(exc: BaseException) -> bool:
    """True if the exception looks like a missing DB column (e.g. rank) — run migrations."""
    msg = str(exc).lower()
    return "rank" in msg or "attachment" in msg or "room_mute" in msg or "user_status" in msg or "acro_score" in msg or "no such column" in msg or "unknown column" in msg


def _schema_error_response():
    """Return 500 response asking user to run migrations."""
    body = (
        "<!DOCTYPE html><html><head><meta charset='UTF-8'><title>No Homers Club — Schema update required</title></head><body>"
        "<h1>Database schema is out of date</h1>"
        "<p>The server could not load your data because the database is missing a required column.</p>"
        "<p><strong>Fix:</strong> Run migrations, then restart the app.</p>"
        "<pre>flask db upgrade</pre>"
        "<p>If you start the app with <code>python run.py</code>, migrations run on startup — ensure you have the latest code and restart.</p>"
        "</body></html>"
    )
    return make_response(body, 500, {"Content-Type": "text/html; charset=utf-8"})


def register_routes(app):
    """Register auth and page routes on the Flask app."""

    def _is_localhost_request():
        """True if request is to localhost (local dev or standalone). Disk token is only safe for single-user localhost."""
        host = (request.host or "").split(":")[0].lower()
        return host in ("127.0.0.1", "localhost", "")

    @app.before_request
    def restore_session_from_remember():
        """If session is empty, restore from remember-me cookie or disk (standalone only; disk is localhost-only for security)."""
        if session.get("user_id"):
            return
        token = request.cookies.get(_REMEMBER_COOKIE_NAME)
        if not token and _is_localhost_request():
            token = load_remember_token_from_disk()
        if not token:
            return
        result = load_remember_token(token)
        if not result:
            return
        user_id, username = result
        user = get_user_by_id(user_id)
        if not user or user.username != username:
            return
        session.permanent = True
        session["user_id"] = user.id
        session["username"] = user.username

    def _login_success_response(user, remember: bool):
        session.permanent = remember
        session["user_id"] = user.id
        session["username"] = user.username
        resp = make_response(redirect(url_for("chat")))
        if remember:
            token = create_remember_token(user.id, user.username)
            max_age = int(Config.REMEMBER_COOKIE_DURATION.total_seconds())
            resp.set_cookie(
                _REMEMBER_COOKIE_NAME,
                token,
                max_age=max_age,
                httponly=True,
                samesite="Lax",
                path="/",
                secure=not _is_localhost_request(),
            )
            if _is_localhost_request():
                save_remember_token_to_disk(token)
        return resp

    @app.route("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("chat"))
        return redirect(url_for("login_page"))

    def _allowed_file(filename: str) -> bool:
        if not filename or "." not in filename:
            return False
        ext = filename.rsplit(".", 1)[-1].lower()
        return ext in getattr(Config, "ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "gif", "webp", "svg", "pdf", "txt", "zip"})

    @app.route("/upload", methods=["POST"])
    def upload_file():
        """Upload a file/image. Returns {url, filename} for use in send_message."""
        if not session.get("user_id"):
            return jsonify({"error": "Not authenticated"}), 401
        file = request.files.get("file") or (list(request.files.values())[0] if request.files else None)
        if not file or not getattr(file, "filename", None):
            return jsonify({"error": "No file selected"}), 400
        if not _allowed_file(file.filename):
            return jsonify({"error": "File type not allowed"}), 400
        upload_dir = Path(Config.UPLOAD_FOLDER)
        upload_dir.mkdir(parents=True, exist_ok=True)
        ext = file.filename.rsplit(".", 1)[-1].lower()
        safe_name = f"{uuid.uuid4().hex}.{ext}"
        filepath = upload_dir / safe_name
        try:
            file.save(str(filepath))
        except OSError as e:
            return jsonify({"error": f"Failed to save file: {e}"}), 500
        url = f"/uploads/{safe_name}"
        return jsonify({"url": url, "filename": file.filename})

    @app.route("/uploads/<path:filename>")
    def serve_upload(filename):
        """Serve uploaded files from instance/uploads/."""
        upload_dir = Path(Config.UPLOAD_FOLDER)
        return send_from_directory(upload_dir, filename, as_attachment=False)

    def _is_allowed_media_host(host: str) -> bool:
        """Allow listed hosts or any *.tenor.com / *.giphy.com subdomain."""
        if not host:
            return False
        h = host.lower()
        if h in ("tenor.com", "giphy.com", "www.giphy.com", "i.giphy.com", "media.giphy.com",
                 "media.tenor.com", "media1.tenor.com", "media2.tenor.com", "media3.tenor.com",
                 "media1.giphy.com", "media2.giphy.com", "media3.giphy.com"):
            return True
        return h.endswith(".tenor.com") or h.endswith(".giphy.com")
    # Modern browser User-Agent to avoid Tenor/Giphy "Bot Blocked" pages
    _USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    _BROWSER_HEADERS = {
        "User-Agent": _USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def _is_view_page(host: str, path: str) -> bool:
        """True if URL is a Tenor/Giphy view page (needs og: scraping), not direct media."""
        path = (path or "").lower()
        if "tenor.com" in host and "/view/" in path:
            return True
        if "giphy.com" in host and "/gifs/" in path:
            return True
        return False

    def _resolve_og_media(page_url: str, referer: str) -> str | None:
        """Scrape page for og:video or og:image meta tags; return actual media URL (mp4 preferred)."""
        try:
            headers = {**_BROWSER_HEADERS, "Referer": referer}
            r = requests.get(page_url, timeout=12, headers=headers)
            r.raise_for_status()
            html = r.text
            # Prefer og:video (usually mp4)
            for pattern in (
                r'<meta\s+property="og:video"[^>]*content="([^"]+)"',
                r'<meta\s+content="([^"]+)"[^>]*property="og:video"',
            ):
                m = re.search(pattern, html, re.I)
                if m:
                    u = m.group(1).strip()
                    if u and u.startswith(("http://", "https://")) and ".mp4" in u.lower():
                        return u
            # Fallback to og:image (often .gif; convert to .mp4 for video)
            for pattern in (
                r'<meta\s+property="og:image"[^>]*content="([^"]+)"',
                r'<meta\s+content="([^"]+)"[^>]*property="og:image"',
            ):
                m = re.search(pattern, html, re.I)
                if m:
                    u = m.group(1).strip()
                    if u and u.startswith(("http://", "https://")):
                        if ".mp4" in u.lower():
                            return u
                        u = re.sub(r"\.gif(\?|$)", r".mp4\1", u, flags=re.I)
                        return u
        except Exception:
            pass
        return None

    @app.route("/media-proxy")
    def media_proxy():
        """Media resolver + proxy: resolves Tenor/Giphy view pages to raw media, streams with correct headers."""
        url = request.args.get("url")
        if not url or not url.startswith(("http://", "https://")):
            return jsonify({"error": "Invalid url"}), 400
        try:
            parsed = urlparse(url)
            host = (parsed.netloc or "").lower()
            if not _is_allowed_media_host(host):
                return jsonify({"error": "Domain not allowed"}), 403
        except Exception:
            return jsonify({"error": "Invalid url"}), 400
        path = (parsed.path or "").lower()
        fetch_url = url
        # Identify view pages: must scrape og:video/og:image to get real media URL
        if _is_view_page(host, path):
            referer = "https://tenor.com/" if "tenor.com" in host else "https://giphy.com/"
            resolved = _resolve_og_media(url, referer)
            if not resolved:
                return jsonify({"error": "Could not resolve media from page"}), 502
            fetch_url = resolved
        try:
            fetch_host = (urlparse(fetch_url).netloc or "").lower()
            referer = "https://giphy.com/" if "giphy.com" in fetch_host else "https://tenor.com/"
            req_headers = {
                "User-Agent": _USER_AGENT,
                "Referer": referer,
                "Accept": "*/*",
            }
            range_hdr = request.headers.get("Range")
            if range_hdr:
                req_headers["Range"] = range_hdr
            r = requests.get(fetch_url, stream=True, timeout=15, headers=req_headers)
            r.raise_for_status()
            content_type = r.headers.get("Content-Type") or "application/octet-stream"
            resp = Response(
                stream_with_context(r.iter_content(chunk_size=1024)),
                content_type=content_type,
                status=r.status_code,
            )
            if "Content-Length" in r.headers:
                resp.headers["Content-Length"] = r.headers["Content-Length"]
            if "Content-Range" in r.headers:
                resp.headers["Content-Range"] = r.headers["Content-Range"]
            if "Accept-Ranges" in r.headers:
                resp.headers["Accept-Ranges"] = r.headers["Accept-Ranges"]
            return resp
        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 502

    @app.route("/health")
    def health():
        """Simple uptime check for deployment / load balancers. No auth required."""
        return jsonify({"status": "ok"}), 200

    @app.route("/export")
    def export_messages():
        """Export room history or all messages as JSON or HTML. Requires login; all rooms requires Super Admin."""
        if not session.get("user_id"):
            return redirect(url_for("login_page"))
        user = get_user_by_id(session["user_id"])
        if not user:
            session.clear()
            return redirect(url_for("login_page"))
        room_id = request.args.get("room_id")
        fmt = (request.args.get("format") or "json").strip().lower()
        if fmt not in ("json", "html"):
            fmt = "json"
        if room_id:
            try:
                room_id = int(room_id)
            except (TypeError, ValueError):
                return jsonify({"error": "Invalid room_id"}), 400
            room = Room.query.get(room_id)
            if not room:
                return jsonify({"error": "Room not found"}), 404
            messages = Message.query.filter_by(room_id=room_id).order_by(Message.created_at.asc()).all()
            room_name = room.name
            export_all = False
        else:
            if not _can_export_all(user):
                return jsonify({"error": "Admin only (or your role needs export_all permission)"}), 403
            messages = Message.query.order_by(Message.room_id, Message.created_at.asc()).all()
            room_name = None
            export_all = True
        if export_all:
            room_ids = {m.room_id for m in messages}
            rooms_by_id = {r.id: r for r in Room.query.filter(Room.id.in_(room_ids)).all()}
        else:
            rooms_by_id = {}
        if fmt == "json":
            out = []
            for m in messages:
                d = m.to_dict()
                if rooms_by_id:
                    d["room_name"] = rooms_by_id.get(m.room_id).name if rooms_by_id.get(m.room_id) else None
                out.append(d)
            resp = make_response(jsonify({"room_name": room_name, "exported_at": __import__("datetime").datetime.utcnow().isoformat() + "Z", "messages": out}))
            resp.headers["Content-Type"] = "application/json"
            resp.headers["Content-Disposition"] = "attachment; filename=no-homers-club-export.json"
            return resp
        # HTML
        lines = [
            "<!DOCTYPE html><html><head><meta charset='UTF-8'><title>No Homers Club export</title>",
            "<style>body{font-family:system-ui;max-width:720px;margin:1rem auto;padding:0 1rem;} .m{border-bottom:1px solid #eee;padding:0.5rem 0;} .m .u{color:#666;font-size:0.9em;} .m .t{color:#999;font-size:0.85em;}</style></head><body>",
            "<h1>No Homers Club export" + (" – " + escape(room_name) if room_name else " – all rooms") + "</h1>",
        ]
        for m in messages:
            r = rooms_by_id.get(m.room_id)
            room_label = (" [" + escape(r.name) + "]" if r else "") if export_all else ""
            u = escape((getattr(m.user, "display_name", None) or m.user.username) if m.user else "?")
            created = m.created_at.isoformat() if m.created_at else ""
            content = escape(m.content or "")
            lines.append(f"<div class='m'><span class='u'>{u}</span> <span class='t'>{created}</span>{room_label}<br>{content}</div>")
        lines.append("</body></html>")
        resp = make_response("\n".join(lines))
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        resp.headers["Content-Disposition"] = "attachment; filename=no-homers-club-export.html"
        return resp

    @app.route("/login", methods=["GET", "POST"])
    def login_page():
        if session.get("user_id"):
            return redirect(url_for("chat"))
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            remember = request.form.get("remember") == "1"
            user = get_user_by_credentials(username, password)
            if user:
                return _login_success_response(user, remember)
            return render_template("login.html", error="Invalid username or password.")
        return render_template("login.html", reset_success=request.args.get("reset") == "1")

    @app.route("/reset-password", methods=["GET", "POST"])
    def reset_password_page():
        if session.get("user_id"):
            return redirect(url_for("chat"))
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            invite_code = (request.form.get("invite_code") or "").strip()
            new_password = request.form.get("new_password") or ""
            confirm = request.form.get("confirm_password") or ""
            if new_password != confirm:
                return render_template("reset_password.html", error="Passwords do not match.")
            ok, err = reset_password(username, invite_code, new_password)
            if ok:
                return redirect(url_for("login_page") + "?reset=1")
            return render_template("reset_password.html", error=err)
        return render_template("reset_password.html")

    @app.route("/register", methods=["GET", "POST"])
    def register_page():
        if session.get("user_id"):
            return redirect(url_for("chat"))
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            invite_code = (request.form.get("invite_code") or "").strip()
            remember = request.form.get("remember") == "1"
            user, err = register_user(username, password, invite_code)
            if user:
                try:
                    from app.sockets import broadcast_user_list_updated
                    broadcast_user_list_updated()
                except Exception:
                    pass
                return _login_success_response(user, remember)
            return render_template("register.html", error=err)
        return render_template("register.html")

    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear()
        clear_remember_token_from_disk()
        resp = make_response(redirect(url_for("login_page")))
        resp.set_cookie(_REMEMBER_COOKIE_NAME, "", max_age=0, path="/")
        return resp

    @app.route("/chat")
    def chat():
        if not session.get("user_id"):
            return redirect(url_for("login_page"))
        user = get_user_by_id(session["user_id"])
        if not user:
            session.clear()
            return redirect(url_for("login_page"))
        user_perms = _user_permissions(user)
        return render_template(
            "chat.html",
            user=user,
            user_bio=getattr(user, "bio", None) or "",
            user_avatar_bg_color=getattr(user, "avatar_bg_color", None) or "",
            message_retention_days=getattr(user, "message_retention_days", None),
            server_name=getattr(Config, "SERVER_NAME", "No Homers Club"),
            user_permissions=user_perms,
            socket_polling_only=getattr(Config, "SOCKET_POLLING_ONLY", False),
        )

    @app.route("/delete-account", methods=["GET", "POST"])
    def delete_account():
        """Delete the current user's account and all associated data (App Store compliance)."""
        if not session.get("user_id"):
            return redirect(url_for("login_page"))
        user_id = session["user_id"]
        user = get_user_by_id(user_id)
        if not user:
            session.clear()
            return redirect(url_for("login_page"))
        if request.method != "POST":
            return render_template("delete_account.html", user=user)
        confirm = (request.form.get("confirm") or "").strip()
        if confirm != "DELETE":
            return render_template("delete_account.html", user=user, error="Type DELETE (all caps) to confirm.")
        # Remove all data associated with this user, then delete the user.
        # Order matters: clear FKs before deleting user.
        MessageReport.query.filter_by(reported_by_user_id=user_id).delete()
        IgnoreList.query.filter(
            (IgnoreList.user_id == user_id) | (IgnoreList.ignored_user_id == user_id)
        ).delete(synchronize_session=False)
        RoomMute.query.filter(
            (RoomMute.muted_user_id == user_id) | (RoomMute.muted_by_id == user_id)
        ).delete(synchronize_session=False)
        AcroScore.query.filter_by(user_id=user_id).delete()
        AuditLog.query.filter_by(user_id=user_id).delete()
        # Delete DM rooms where user is a participant (so "DM: Chachi" disappears for others)
        dm_rooms = Room.query.filter(
            Room.dm_with_id.isnot(None),
            (Room.created_by_id == user_id) | (Room.dm_with_id == user_id),
        ).all()
        dm_room_ids = [r.id for r in dm_rooms]
        if dm_room_ids:
            RoomMute.query.filter(RoomMute.room_id.in_(dm_room_ids)).delete(synchronize_session=False)
        for dm_room in dm_rooms:
            db.session.delete(dm_room)
        Message.query.filter_by(user_id=user_id).delete()
        Room.query.filter(Room.created_by_id == user_id).update({"created_by_id": None})
        Room.query.filter(Room.topic_set_by_id == user_id).update({"topic_set_by_id": None})
        Room.query.filter(Room.dm_with_id == user_id).update({"dm_with_id": None})
        db.session.delete(user)
        db.session.commit()
        session.clear()
        clear_remember_token_from_disk()
        resp = make_response(redirect(url_for("login_page") + "?deleted=1"))
        resp.set_cookie(_REMEMBER_COOKIE_NAME, "", max_age=0, path="/")
        return resp

    @app.route("/api/set-user-roles", methods=["POST"])
    def api_set_user_roles():
        """Set user roles. Requires set_user_rank permission. Accepts JSON: { changes: [{ user_id, rank }, ...] }."""
        if not session.get("user_id"):
            return jsonify({"ok": False, "error": "Not authenticated"}), 401
        user = get_user_by_id(session["user_id"])
        if not user:
            return jsonify({"ok": False, "error": "User not found"}), 401
        perms = _user_permissions(user)
        if not perms.get("set_user_rank"):
            return jsonify({"ok": False, "error": "Only admins can set user roles"}), 403
        data = request.get_json(silent=True) or {}
        changes = data.get("changes") or []
        if not isinstance(changes, list):
            return jsonify({"ok": False, "error": "changes must be an array"}), 400
        results = []
        for item in changes:
            target_id = item.get("user_id") if isinstance(item, dict) else None
            rank = (item.get("rank") or "").strip().lower() if isinstance(item, dict) else ""
            if target_id is None or not rank:
                results.append({"user_id": target_id, "ok": False, "error": "user_id and rank required"})
                continue
            try:
                target_id = int(target_id)
            except (TypeError, ValueError):
                results.append({"user_id": target_id, "ok": False, "error": "Invalid user_id"})
                continue
            if rank not in ("rookie", "bro", "fam", "super_admin"):
                results.append({"user_id": target_id, "ok": False, "error": "rank must be rookie, bro, fam, or super_admin"})
                continue
            target = User.query.get(target_id)
            if not target:
                results.append({"user_id": target_id, "ok": False, "error": "User not found"})
                continue
            target.rank = rank
            target.is_super_admin = rank == "super_admin"
            db.session.add(AuditLog(
                user_id=session["user_id"],
                action="set_user_rank",
                target_type="user",
                target_id=target_id,
                details=json.dumps({"target_username": target.username, "rank": rank}),
            ))
            results.append({"user_id": target_id, "ok": True, "target_username": target.username, "rank": rank})
        db.session.commit()
        try:
            from app.sockets import broadcast_user_list_updated
            broadcast_user_list_updated()
        except Exception:
            pass
        return jsonify({"ok": True, "results": results})

    @app.route("/api/set-role-permissions", methods=["POST"])
    def api_set_role_permissions():
        """Set role permissions. Super Admin only. Accepts JSON: { permissions: { role: { permission: bool }, ... } }."""
        if not session.get("user_id"):
            return jsonify({"ok": False, "error": "Not authenticated"}), 401
        user = get_user_by_id(session["user_id"])
        if not user:
            return jsonify({"ok": False, "error": "User not found"}), 401
        if not getattr(user, "is_super_admin", False):
            return jsonify({"ok": False, "error": "Only Super Admin can configure role permissions"}), 403
        data = request.get_json(silent=True) or {}
        perms = data.get("permissions") or {}
        if not isinstance(perms, dict):
            return jsonify({"ok": False, "error": "permissions must be an object"}), 400
        valid_roles = ("rookie", "bro", "fam")
        valid_perms = ("create_room", "update_room", "delete_room", "kick_user", "set_user_rank", "acrobot_control", "homer_control", "frink_control", "reset_stats", "export_all")
        for role, role_perms in perms.items():
            if role not in valid_roles:
                continue
            if not isinstance(role_perms, dict):
                continue
            for permission, allowed in role_perms.items():
                if permission not in valid_perms:
                    continue
                rp = RolePermission.query.filter_by(role=role, permission=permission).first()
                if rp:
                    rp.allowed = bool(allowed)
                else:
                    db.session.add(RolePermission(role=role, permission=permission, allowed=bool(allowed)))
        db.session.add(AuditLog(
            user_id=session["user_id"],
            action="set_role_permissions",
            target_type=None,
            target_id=None,
            details=json.dumps({"permissions": perms}),
        ))
        db.session.commit()
        return jsonify({"ok": True})

    @app.errorhandler(OperationalError)
    def handle_operational_error(e):
        """If DB error looks like missing column (e.g. rank), return friendly 'run migrations' page."""
        if _is_schema_out_of_date_error(e):
            return _schema_error_response()
        raise

    @app.context_processor
    def inject_user():
        uid = session.get("user_id")
        if uid:
            user = get_user_by_id(uid)
            return {"current_user": user}
        return {"current_user": None}
