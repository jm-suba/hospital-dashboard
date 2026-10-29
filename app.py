from pathlib import Path
import sqlite3
from datetime import date

from flask import Flask, request, redirect, render_template_string, url_for, flash

app = Flask(__name__)
app.secret_key = "replace-this-secret-before-deployment"

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "hospital.db"


def connect_db():
    con = sqlite3.connect(str(DB_PATH), timeout=10)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    """Create or safely upgrade the SQLite table without deleting existing rows."""
    with connect_db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                phone TEXT,
                disease TEXT,
                created_on TEXT NOT NULL
            )
        """)
        cols = {r["name"] for r in con.execute("PRAGMA table_info(patients)")}
        migrations = {
            "gender": "ALTER TABLE patients ADD COLUMN gender TEXT",
            "phone": "ALTER TABLE patients ADD COLUMN phone TEXT",
            "created_on": "ALTER TABLE patients ADD COLUMN created_on TEXT",
        }
        for column, sql in migrations.items():
            if column not in cols:
                con.execute(sql)
        con.execute(
            "UPDATE patients SET created_on = ? WHERE created_on IS NULL OR TRIM(created_on) = ''",
            (date.today().isoformat(),),
        )


DASHBOARD_HTML = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>CarePoint | Hospital Dashboard</title>
<style>
:root{--navy:#10233f;--blue:#2864dc;--teal:#0f9f91;--bg:#f3f6fb;--text:#1d2b43;--muted:#718096;--line:#e5eaf2;--white:#fff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);font-family:Inter,Segoe UI,Arial,sans-serif;color:var(--text)}
.layout{display:flex;min-height:100vh}.sidebar{width:245px;background:var(--navy);color:#fff;padding:26px 16px;display:flex;flex-direction:column;flex-shrink:0}
.brand{display:flex;align-items:center;gap:11px;padding:0 12px 30px;font-weight:800;font-size:20px;letter-spacing:.2px}.brand-icon{width:39px;height:39px;border-radius:12px;background:#21b6a8;display:grid;place-items:center;font-size:24px}
.nav-label{padding:10px 12px;color:#90a3c1;font-size:11px;letter-spacing:1.4px;font-weight:700}.nav-link{display:flex;align-items:center;gap:12px;padding:13px 14px;border-radius:10px;margin:3px 0;color:#d7e1f0;text-decoration:none;font-size:14px}.nav-link.active,.nav-link:hover{background:#203b61;color:#fff}.nav-link .ico{width:22px;text-align:center;font-size:17px}.sidebar-bottom{margin-top:auto;padding:18px 12px 0;color:#9bb0cb;font-size:12px;line-height:1.6}
.main{min-width:0;flex:1}.topbar{height:78px;background:#fff;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 clamp(18px,4vw,42px);gap:15px}.crumb{font-size:13px;color:var(--muted)}.crumb strong{color:var(--text)}.user{display:flex;align-items:center;gap:11px;font-size:13px}.avatar{width:39px;height:39px;background:#e1eaff;color:#2456b5;border-radius:50%;display:grid;place-items:center;font-weight:800}
.content{max-width:1450px;margin:auto;padding:30px clamp(16px,4vw,42px) 45px}.welcome{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;flex-wrap:wrap;margin-bottom:25px}.welcome h1{font-size:28px;margin:0 0 8px;letter-spacing:-.5px}.welcome p{margin:0;color:var(--muted);font-size:14px}.primary{border:0;border-radius:10px;padding:13px 18px;background:var(--blue);color:#fff;font-size:14px;font-weight:700;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;justify-content:center;gap:8px;box-shadow:0 5px 12px #2864dc22}.primary:hover{background:#1f50bb}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}.stat{background:#fff;border:1px solid var(--line);border-radius:15px;padding:21px;box-shadow:0 4px 14px #24385805}.stat-head{display:flex;align-items:center;justify-content:space-between;color:var(--muted);font-size:13px;gap:10px}.stat-icon{height:40px;width:40px;border-radius:12px;display:grid;place-items:center;font-size:19px}.blue{background:#e9f0ff}.green{background:#dff8f1}.orange{background:#fff0db}.purple{background:#f0e8ff}.stat-value{font-size:29px;font-weight:800;margin:15px 0 5px;letter-spacing:-.7px}.stat-note{font-size:12px;color:var(--muted)}.positive{color:#0b9b79;font-weight:700}
.section-head{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin:31px 0 15px}.section-head h2{margin:0;font-size:18px}.section-head p{margin:5px 0 0;color:var(--muted);font-size:13px}
.panel{background:#fff;border:1px solid var(--line);border-radius:15px;padding:23px;box-shadow:0 4px 14px #24385805}.quick-grid{display:grid;grid-template-columns:1.25fr 1fr;gap:18px}.activity{display:flex;gap:13px;padding:12px 0;border-bottom:1px solid var(--line);align-items:flex-start}.activity:last-child{border:0}.activity-dot{width:10px;height:10px;border-radius:50%;background:var(--teal);margin-top:5px;box-shadow:0 0 0 4px #dff8f1}.activity b{font-size:13px}.activity small{display:block;color:var(--muted);margin-top:5px}.action-list{display:grid;gap:11px}.action-card{display:flex;align-items:center;gap:13px;padding:14px;border:1px solid var(--line);border-radius:12px;text-decoration:none;color:var(--text)}.action-card:hover{border-color:#9ab5f5;background:#f8faff}.action-icon{width:42px;height:42px;border-radius:11px;background:#e9f0ff;display:grid;place-items:center;font-size:20px}.action-card b{font-size:13px}.action-card small{display:block;color:var(--muted);margin-top:4px}
.table-tools{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}.search{flex:1 1 240px}.field,select{width:100%;padding:12px 13px;border:1px solid #dbe2ec;border-radius:9px;background:#fff;font:inherit;font-size:13px;color:var(--text)}.field:focus,select:focus{outline:2px solid #c9d8ff;border-color:#7b9ef1}.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px}table{border-collapse:collapse;width:100%;min-width:700px}th,td{padding:14px 16px;text-align:left;border-bottom:1px solid var(--line);font-size:13px}th{background:#f8faff;color:#66758c;font-size:11px;text-transform:uppercase;letter-spacing:.7px}tbody tr:hover{background:#f9fbff}tbody tr:last-child td{border-bottom:0}.patient{display:flex;align-items:center;gap:10px}.patient-avatar{width:34px;height:34px;border-radius:10px;background:#e7efff;color:#2b58ad;display:grid;place-items:center;font-weight:800}.patient-name{font-weight:700}.subtext{display:block;font-size:11px;color:var(--muted);margin-top:4px}.pill{display:inline-block;padding:5px 9px;border-radius:30px;background:#e2f8f0;color:#087f61;font-size:11px;font-weight:700}.empty{text-align:center;padding:35px;color:var(--muted)}
.flash{padding:13px 16px;border-radius:10px;background:#dcfce7;color:#166534;margin-bottom:18px;font-size:13px}.flash.error{background:#fee2e2;color:#991b1b}.footer{text-align:center;color:#8a96a8;font-size:11px;margin-top:25px}
.modal{display:none;position:fixed;inset:0;background:#0d1b2e99;z-index:10;padding:18px;overflow-y:auto;align-items:center;justify-content:center}.modal.open{display:flex}.modal-box{width:min(650px,100%);background:#fff;border-radius:18px;box-shadow:0 25px 80px #07132944;overflow:hidden}.modal-head{padding:23px 25px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center}.modal-head h2{margin:0;font-size:20px}.close{border:0;background:#eef2f7;border-radius:8px;width:35px;height:35px;font-size:22px;cursor:pointer}.modal-body{padding:24px}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.form-group label{display:block;font-size:12px;font-weight:700;color:#53627a;margin-bottom:7px}.form-group.full{grid-column:1/-1}.modal-foot{display:flex;justify-content:flex-end;gap:10px;margin-top:22px}.secondary{border:1px solid #dbe2ec;background:#fff;border-radius:9px;padding:12px 17px;cursor:pointer;font-weight:700;color:#53627a}
@media(max-width:1100px){.stats{grid-template-columns:repeat(2,minmax(0,1fr))}.quick-grid{grid-template-columns:1fr}}@media(max-width:700px){.sidebar{width:64px;padding:20px 8px}.brand{padding:0 4px 28px}.brand-name,.nav-label,.nav-link span:not(.ico),.sidebar-bottom{display:none}.nav-link{justify-content:center;padding:13px 5px}.topbar{height:65px}.welcome h1{font-size:24px}.stats{gap:10px}.stat{padding:16px}.stat-value{font-size:24px}.form-grid{grid-template-columns:1fr}.form-group.full{grid-column:auto}.panel{padding:16px}}
</style>
</head>
<body>
<div class="layout">
<aside class="sidebar">
  <div class="brand"><div class="brand-icon">✚</div><span class="brand-name">CarePoint</span></div>
  <div class="nav-label">WORKSPACE</div>
  <a class="nav-link active" href="{{ url_for('dashboard') }}"><span class="ico">▦</span><span>Dashboard</span></a>
  <a class="nav-link" href="#patients"><span class="ico">♙</span><span>Patients</span></a>
  <a class="nav-link" href="#quick-actions" onclick="openRegister(event)"><span class="ico">＋</span><span>Register Patient</span></a>
  <div class="nav-label">SYSTEM</div>
  <a class="nav-link" href="{{ url_for('health') }}"><span class="ico">◉</span><span>System Status</span></a>
  <div class="sidebar-bottom">CarePoint Hospital<br>Management System<br><br>Demo version · SQLite</div>
</aside>
<div class="main">
  <div class="topbar">
    <div class="crumb">Workspace &nbsp;›&nbsp; <strong>Dashboard</strong></div>
    <div class="user"><div class="avatar">CP</div><div><b>Hospital Admin</b><div class="subtext">Administrator</div></div></div>
  </div>
  <main class="content">
    {% for category, msg in get_flashed_messages(with_categories=true) %}
      <div class="flash {{ 'error' if category == 'error' else '' }}">{{ msg }}</div>
    {% endfor %}
    <div class="welcome">
      <div><h1>Hospital Dashboard</h1><p>Welcome back. Here is your hospital overview for today.</p></div>
      <button class="primary" onclick="openRegister()">＋ &nbsp; Register New Patient</button>
    </div>
    <section class="stats">
      <div class="stat"><div class="stat-head">Total Patients <span class="stat-icon blue">♙</span></div><div class="stat-value">{{ total }}</div><div class="stat-note">All registered patient records</div></div>
      <div class="stat"><div class="stat-head">Registered Today <span class="stat-icon green">↗</span></div><div class="stat-value">{{ today }}</div><div class="stat-note"><span class="positive">Today</span> · New registrations</div></div>
      <div class="stat"><div class="stat-head">Patient Conditions <span class="stat-icon orange">♡</span></div><div class="stat-value">{{ conditions }}</div><div class="stat-note">Unique conditions recorded</div></div>
      <div class="stat"><div class="stat-head">System Status <span class="stat-icon purple">✓</span></div><div class="stat-value" style="font-size:24px">Operational</div><div class="stat-note"><span class="positive">● Online</span> · SQLite connected</div></div>
    </section>

    <div class="section-head"><div><h2>Quick Actions</h2><p>Common tasks to manage your hospital records.</p></div></div>
    <section class="quick-grid" id="quick-actions">
      <div class="panel">
        <div class="action-list">
          <a class="action-card" href="#register" onclick="openRegister(event)"><div class="action-icon">＋</div><div><b>Register a new patient</b><small>Add a patient and save their details to the database.</small></div></a>
          <a class="action-card" href="#patients"><div class="action-icon">▤</div><div><b>View patient records</b><small>Search and review saved patient registrations.</small></div></a>
          <a class="action-card" href="{{ url_for('health') }}"><div class="action-icon">◉</div><div><b>Check system status</b><small>Verify that the application and database respond.</small></div></a>
        </div>
      </div>
      <div class="panel">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px"><h3 style="font-size:16px;margin:0">Recent Registrations</h3><a href="#patients" style="font-size:12px;color:#2864dc;text-decoration:none">View all ↓</a></div>
        {% for p in recent %}
          <div class="activity"><div class="activity-dot"></div><div><b>{{ p["name"] }}</b><small>{{ p["disease"] or "Condition not specified" }} · {{ p["created_on"] or "Date unavailable" }}</small></div></div>
        {% else %}
          <div class="empty">No registrations yet. Use “Register New Patient” to add the first record.</div>
        {% endfor %}
      </div>
    </section>

    <section id="patients">
      <div class="section-head"><div><h2>Patient Directory</h2><p>Patient records stored in your local SQLite database.</p></div><span style="font-size:12px;color:#718096">{{ patients|length }} record(s) displayed</span></div>
      <div class="panel">
        <form class="table-tools" method="get" action="{{ url_for('dashboard') }}">
          <div class="search"><input class="field" name="q" value="{{ q }}" placeholder="Search name, condition, phone or patient ID..."></div>
          <button class="primary" type="submit">⌕ Search</button>
          <a class="secondary" style="text-decoration:none;display:inline-flex;align-items:center" href="{{ url_for('dashboard') }}">Reset</a>
        </form>
        <div class="table-wrap"><table>
          <thead><tr><th>Patient</th><th>Patient ID</th><th>Age / Gender</th><th>Condition</th><th>Phone</th><th>Registered</th><th>Status</th></tr></thead>
          <tbody>
          {% for p in patients %}
            <tr>
              <td><div class="patient"><div class="patient-avatar">{{ p["name"][:1]|upper }}</div><div class="patient-name">{{ p["name"] }}</div></div></td>
              <td>PT-{{ "%04d"|format(p["id"]) }}</td>
              <td>{{ p["age"] if p["age"] is not none else "—" }} / {{ p["gender"] or "—" }}</td>
              <td>{{ p["disease"] or "Not specified" }}</td>
              <td>{{ p["phone"] or "—" }}</td>
              <td>{{ p["created_on"] or "—" }}</td>
              <td><span class="pill">Registered</span></td>
            </tr>
          {% else %}
            <tr><td colspan="7" class="empty">No matching patients found. Register a patient or clear your search.</td></tr>
          {% endfor %}
          </tbody>
        </table></div>
      </div>
    </section>
    <div class="footer">CarePoint Hospital Management · Demo application · Data stored locally in hospital.db</div>
  </main>
</div>
</div>
<div class="modal" id="registerModal" role="dialog" aria-modal="true" aria-labelledby="modalTitle">
  <div class="modal-box">
    <div class="modal-head"><div><h2 id="modalTitle">Register New Patient</h2><div class="subtext">Enter the patient details below. Required fields are marked *.</div></div><button class="close" type="button" onclick="closeRegister()" aria-label="Close">×</button></div>
    <form method="post" action="{{ url_for('register_patient') }}">
      <div class="modal-body"><div class="form-grid">
        <div class="form-group full"><label for="name">Patient Full Name *</label><input class="field" id="name" name="name" maxlength="100" required placeholder="Enter full name"></div>
        <div class="form-group"><label for="age">Age</label><input class="field" id="age" name="age" type="number" min="0" max="120" placeholder="Age in years"></div>
        <div class="form-group"><label for="gender">Gender</label><select id="gender" name="gender"><option value="">Select gender</option><option>Female</option><option>Male</option><option>Other</option><option>Prefer not to say</option></select></div>
        <div class="form-group"><label for="phone">Phone Number</label><input class="field" id="phone" name="phone" maxlength="25" placeholder="Contact number"></div>
        <div class="form-group"><label for="disease">Condition / Reason for Visit</label><input class="field" id="disease" name="disease" maxlength="200" placeholder="e.g. General check-up"></div>
      </div>
      <div class="modal-foot"><button type="button" class="secondary" onclick="closeRegister()">Cancel</button><button type="submit" class="primary">Save Patient to SQL</button></div></div>
    </form>
  </div>
</div>
<script>
const modal = document.getElementById('registerModal');
function openRegister(e){if(e)e.preventDefault();modal.classList.add('open');setTimeout(()=>document.getElementById('name').focus(),60)}
function closeRegister(){modal.classList.remove('open')}
modal.addEventListener('click',e=>{if(e.target===modal)closeRegister()});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeRegister()});
</script>
</body></html>
"""


@app.route("/")
def dashboard():
    q = request.args.get("q", "").strip()
    like = f"%{q}%"
    with connect_db() as con:
        if q:
            patients = con.execute(
                """SELECT id, name, age, gender, phone, disease, created_on
                   FROM patients
                   WHERE name LIKE ? OR COALESCE(disease,'') LIKE ?
                      OR COALESCE(phone,'') LIKE ? OR CAST(id AS TEXT) LIKE ?
                   ORDER BY id DESC""",
                (like, like, like, like),
            ).fetchall()
        else:
            patients = con.execute(
                """SELECT id, name, age, gender, phone, disease, created_on
                   FROM patients ORDER BY id DESC"""
            ).fetchall()
        total = con.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
        today = con.execute(
            "SELECT COUNT(*) FROM patients WHERE created_on = ?",
            (date.today().isoformat(),),
        ).fetchone()[0]
        conditions = con.execute(
            """SELECT COUNT(DISTINCT LOWER(TRIM(disease))) FROM patients
               WHERE disease IS NOT NULL AND TRIM(disease) <> ''"""
        ).fetchone()[0]
        recent = con.execute(
            """SELECT id, name, disease, created_on FROM patients ORDER BY id DESC LIMIT 4"""
        ).fetchall()

    return render_template_string(
        DASHBOARD_HTML, patients=patients, total=total, today=today,
        conditions=conditions, recent=recent, q=q
    )


@app.route("/register", methods=["POST"])
def register_patient():
    name = request.form.get("name", "").strip()
    age_text = request.form.get("age", "").strip()
    gender = request.form.get("gender", "").strip()
    phone = request.form.get("phone", "").strip()
    disease = request.form.get("disease", "").strip()

    if not name:
        flash("Patient name is required.", "error")
        return redirect(url_for("dashboard"))
    try:
        age = int(age_text) if age_text else None
        if age is not None and not 0 <= age <= 120:
            raise ValueError
    except ValueError:
        flash("Please enter a valid age between 0 and 120.", "error")
        return redirect(url_for("dashboard"))

    with connect_db() as con:
        con.execute(
            """INSERT INTO patients (name, age, gender, phone, disease, created_on)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, age, gender or None, phone or None, disease or None, date.today().isoformat()),
        )
    flash(f"Patient {name} was saved successfully to the SQL database.", "success")
    return redirect(url_for("dashboard") + "#patients")


@app.route("/health")
def health():
    with connect_db() as con:
        count = con.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    return {"status": "ok", "database": str(DB_PATH), "patient_records": count}


if __name__ == "__main__":
    init_db()

