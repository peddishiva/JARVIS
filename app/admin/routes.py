"""HTTP and REST controller routes for the JARVIS Admin Dashboard."""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)
from app.admin.auth import (
    admin_exists,
    create_admin_user,
    authenticate_admin,
    login_required,
)
from app.admin.services import (
    ContactsRepository,
    WebCommandsRepository,
    SystemCommandsRepository,
    DashboardService,
)

admin_bp = Blueprint("admin", __name__, template_folder="templates", static_folder="static")


@admin_bp.route("/")
def index():
    """Redirect to dashboard or login/setup."""
    if not admin_exists():
        return redirect(url_for("admin.setup"))
    if session.get("admin_id"):
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("admin.login"))


# ============================================================
# AUTHENTICATION ROUTES
# ============================================================

@admin_bp.route("/setup", methods=["GET", "POST"])
def setup():
    """First-run administrator setup."""
    if admin_exists():
        flash("An administrator account already exists. Please log in.", "info")
        return redirect(url_for("admin.login"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("setup.html", username=username)

        success, err = create_admin_user(username, password)
        if success:
            flash("Administrator account successfully created. Please log in.", "success")
            return redirect(url_for("admin.login"))
        else:
            flash(err, "error")
            return render_template("setup.html", username=username)

    return render_template("setup.html")


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    """Admin login."""
    if not admin_exists():
        return redirect(url_for("admin.setup"))

    if session.get("admin_id"):
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = authenticate_admin(username, password)
        if user:
            session.clear()
            session["admin_id"] = user["id"]
            session["admin_username"] = user["username"]
            flash(f"Welcome back, {user['username']}.", "success")
            next_url = request.args.get("next") or url_for("admin.dashboard")
            return redirect(next_url)
        else:
            flash("Invalid username or password.", "error")
            return render_template("login.html", username=username)

    return render_template("login.html")


@admin_bp.route("/logout", methods=["GET", "POST"])
def logout():
    """Logout current admin session."""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("admin.login"))


# ============================================================
# DASHBOARD HOME
# ============================================================

@admin_bp.route("/dashboard")
@login_required
def dashboard():
    """Dashboard metrics summary page."""
    summary = DashboardService.get_summary()
    return render_template("dashboard.html", summary=summary)


# ============================================================
# CONTACTS MANAGEMENT
# ============================================================

@admin_bp.route("/contacts")
@login_required
def contacts():
    """List and search contacts."""
    q = request.args.get("q", "").strip()
    contacts_list = ContactsRepository.search(q) if q else ContactsRepository.list_all()
    return render_template("contacts.html", contacts=contacts_list, query=q)


@admin_bp.route("/contacts/create", methods=["POST"])
@login_required
def create_contact():
    """Create a new contact."""
    name = request.form.get("name")
    mobile_no = request.form.get("mobile_no")
    email = request.form.get("email")

    success, err = ContactsRepository.create(name, mobile_no, email)
    if success:
        flash(f"Contact '{name}' added successfully.", "success")
    else:
        flash(err, "error")

    return redirect(url_for("admin.contacts"))


@admin_bp.route("/contacts/<int:contact_id>/update", methods=["POST"])
@login_required
def update_contact(contact_id):
    """Update an existing contact."""
    name = request.form.get("name")
    mobile_no = request.form.get("mobile_no")
    email = request.form.get("email")

    success, err = ContactsRepository.update(contact_id, name, mobile_no, email)
    if success:
        flash(f"Contact '{name}' updated successfully.", "success")
    else:
        flash(err, "error")

    return redirect(url_for("admin.contacts"))


@admin_bp.route("/contacts/<int:contact_id>/delete", methods=["POST"])
@login_required
def delete_contact(contact_id):
    """Delete a contact."""
    success, err = ContactsRepository.delete(contact_id)
    if success:
        flash("Contact deleted successfully.", "success")
    else:
        flash(err, "error")

    return redirect(url_for("admin.contacts"))


# ============================================================
# WEB COMMANDS MANAGEMENT
# ============================================================

@admin_bp.route("/web-commands")
@login_required
def web_commands():
    """List and search web commands."""
    q = request.args.get("q", "").strip()
    commands_list = WebCommandsRepository.search(q) if q else WebCommandsRepository.list_all()
    return render_template("web_commands.html", commands=commands_list, query=q)


@admin_bp.route("/web-commands/create", methods=["POST"])
@login_required
def create_web_command():
    """Create a new web shortcut command."""
    name = request.form.get("name")
    url = request.form.get("url")

    success, err = WebCommandsRepository.create(name, url)
    if success:
        flash(f"Web command '{name}' created successfully.", "success")
    else:
        flash(err, "error")

    return redirect(url_for("admin.web_commands"))


@admin_bp.route("/web-commands/<int:cmd_id>/update", methods=["POST"])
@login_required
def update_web_command(cmd_id):
    """Update an existing web shortcut command."""
    name = request.form.get("name")
    url = request.form.get("url")

    success, err = WebCommandsRepository.update(cmd_id, name, url)
    if success:
        flash(f"Web command '{name}' updated successfully.", "success")
    else:
        flash(err, "error")

    return redirect(url_for("admin.web_commands"))


@admin_bp.route("/web-commands/<int:cmd_id>/delete", methods=["POST"])
@login_required
def delete_web_command(cmd_id):
    """Delete a web command."""
    success, err = WebCommandsRepository.delete(cmd_id)
    if success:
        flash("Web command deleted successfully.", "success")
    else:
        flash(err, "error")

    return redirect(url_for("admin.web_commands"))


# ============================================================
# SYSTEM COMMANDS MANAGEMENT
# ============================================================

@admin_bp.route("/system-commands")
@login_required
def system_commands():
    """List and search system application commands."""
    q = request.args.get("q", "").strip()
    commands_list = SystemCommandsRepository.search(q) if q else SystemCommandsRepository.list_all()
    return render_template("system_commands.html", commands=commands_list, query=q)


@admin_bp.route("/system-commands/create", methods=["POST"])
@login_required
def create_system_command():
    """Create a new system application shortcut."""
    name = request.form.get("name")
    path = request.form.get("path")

    success, err = SystemCommandsRepository.create(name, path)
    if success:
        flash(f"System command '{name}' created successfully.", "success")
    else:
        flash(err, "error")

    return redirect(url_for("admin.system_commands"))


@admin_bp.route("/system-commands/<int:cmd_id>/update", methods=["POST"])
@login_required
def update_system_command(cmd_id):
    """Update an existing system application command."""
    name = request.form.get("name")
    path = request.form.get("path")

    success, err = SystemCommandsRepository.update(cmd_id, name, path)
    if success:
        flash(f"System command '{name}' updated successfully.", "success")
    else:
        flash(err, "error")

    return redirect(url_for("admin.system_commands"))


@admin_bp.route("/system-commands/<int:cmd_id>/delete", methods=["POST"])
@login_required
def delete_system_command(cmd_id):
    """Delete a system application command."""
    success, err = SystemCommandsRepository.delete(cmd_id)
    if success:
        flash("System command deleted successfully.", "success")
    else:
        flash(err, "error")

    return redirect(url_for("admin.system_commands"))


@admin_bp.route("/system-commands/<int:cmd_id>/test", methods=["POST"])
@login_required
def test_system_command(cmd_id):
    """Safely test launch an approved stored command."""
    success, msg = SystemCommandsRepository.test_launch(cmd_id)
    if success:
        flash(msg, "success")
    else:
        flash(msg, "error")

    return redirect(url_for("admin.system_commands"))


# ============================================================
# REST API (JSON) ENDPOINTS
# ============================================================

@admin_bp.route("/api/summary", methods=["GET"])
@login_required
def api_summary():
    """Return dashboard summary stats in JSON."""
    return jsonify(DashboardService.get_summary())


@admin_bp.route("/api/contacts", methods=["GET", "POST"])
@login_required
def api_contacts():
    """JSON API for contacts list or creation."""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        success, err = ContactsRepository.create(
            data.get("name"), data.get("mobile_no"), data.get("email")
        )
        if success:
            return jsonify({"success": True}), 201
        return jsonify({"success": False, "error": err}), 400

    q = request.args.get("q")
    items = ContactsRepository.search(q) if q else ContactsRepository.list_all()
    return jsonify(items)


@admin_bp.route("/api/contacts/<int:contact_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def api_contact_detail(contact_id):
    """JSON API for contact retrieval, update, or deletion."""
    if request.method == "GET":
        item = ContactsRepository.get_by_id(contact_id)
        if not item:
            return jsonify({"error": "Not found"}), 404
        return jsonify(item)

    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        success, err = ContactsRepository.update(
            contact_id, data.get("name"), data.get("mobile_no"), data.get("email")
        )
        if success:
            return jsonify({"success": True})
        return jsonify({"success": False, "error": err}), 400

    if request.method == "DELETE":
        success, err = ContactsRepository.delete(contact_id)
        if success:
            return jsonify({"success": True})
        return jsonify({"success": False, "error": err}), 404


@admin_bp.route("/api/web-commands", methods=["GET", "POST"])
@login_required
def api_web_commands():
    """JSON API for web commands list or creation."""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        success, err = WebCommandsRepository.create(data.get("name"), data.get("url"))
        if success:
            return jsonify({"success": True}), 201
        return jsonify({"success": False, "error": err}), 400

    q = request.args.get("q")
    items = WebCommandsRepository.search(q) if q else WebCommandsRepository.list_all()
    return jsonify(items)


@admin_bp.route("/api/web-commands/<int:cmd_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def api_web_command_detail(cmd_id):
    """JSON API for web command retrieval, update, or deletion."""
    if request.method == "GET":
        item = WebCommandsRepository.get_by_id(cmd_id)
        if not item:
            return jsonify({"error": "Not found"}), 404
        return jsonify(item)

    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        success, err = WebCommandsRepository.update(cmd_id, data.get("name"), data.get("url"))
        if success:
            return jsonify({"success": True})
        return jsonify({"success": False, "error": err}), 400

    if request.method == "DELETE":
        success, err = WebCommandsRepository.delete(cmd_id)
        if success:
            return jsonify({"success": True})
        return jsonify({"success": False, "error": err}), 404


@admin_bp.route("/api/system-commands", methods=["GET", "POST"])
@login_required
def api_system_commands():
    """JSON API for system commands list or creation."""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        success, err = SystemCommandsRepository.create(data.get("name"), data.get("path"))
        if success:
            return jsonify({"success": True}), 201
        return jsonify({"success": False, "error": err}), 400

    q = request.args.get("q")
    items = SystemCommandsRepository.search(q) if q else SystemCommandsRepository.list_all()
    return jsonify(items)


@admin_bp.route("/api/system-commands/<int:cmd_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def api_system_command_detail(cmd_id):
    """JSON API for system command retrieval, update, or deletion."""
    if request.method == "GET":
        item = SystemCommandsRepository.get_by_id(cmd_id)
        if not item:
            return jsonify({"error": "Not found"}), 404
        return jsonify(item)

    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        success, err = SystemCommandsRepository.update(cmd_id, data.get("name"), data.get("path"))
        if success:
            return jsonify({"success": True})
        return jsonify({"success": False, "error": err}), 400

    if request.method == "DELETE":
        success, err = SystemCommandsRepository.delete(cmd_id)
        if success:
            return jsonify({"success": True})
        return jsonify({"success": False, "error": err}), 404


@admin_bp.route("/api/system-commands/<int:cmd_id>/test", methods=["POST"])
@login_required
def api_system_command_test(cmd_id):
    """JSON API to test launching a system command."""
    success, msg = SystemCommandsRepository.test_launch(cmd_id)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "error": msg}), 400
