import tkinter as tk
from tkinter import messagebox
import sys

from core.exec import Execution
from core.orchestrator import Orchestrator
from storage.database import Database
from core.config import APP_CONFIG

# ----------------------------
# Build config from UI
# ----------------------------

def build_config_from_ui():
    return {
        "modules": {
            "subdomains": subdomains_var.get(),
            "whois": whois_var.get(),
            "dns": dns_var.get(),
            "security_headers": security_headers_var.get(),
            "emails_passive": emails_var.get(),
            "crawler": crawler_var.get(),
            "js_parsing": js_var.get(),
            "scraping": scraping_var.get(),
            "wayback": wayback_var.get(),
        },
        "limits": {
            "subdomain_max": max_subdomains_var.get(),
            "dns_max_domains": dns_max_domains_var.get(),
            "crawler_live_max_pages": crawler_live_max_pages_var.get(),
            "crawler_wayback_max_pages": crawler_wayback_max_pages_var.get(),
            "wayback_max_snapshots": wayback_max_snapshots_var.get(),
            "wayback_min_year": wayback_min_year_var.get(),
            "js_max_scripts": js_max_scripts_var.get(),
            "sitemap_max_urls": sitemap_max_urls_var.get(),
            "robots_max_urls": robots_max_urls_var.get(),
            "cdx_url_limit": cdx_url_limit_var.get(),
        },
        "timeouts": {
            "http_passive_email": http_email_var.get(),
            "http_subdomains": http_subdomains_var.get(),
            "dns_resolution": dns_timeout_var.get(),
            "http_security_headers": http_security_headers_var.get(),
            "crawler_live_page": crawler_live_timeout_var.get(),
            "crawler_wayback_page": crawler_wayback_timeout_var.get(),
            "js_connect": js_connect_var.get(),
            "js_read": js_read_var.get(),
            "scraping_page_load": scraping_timeout_var.get(),
            "wayback_cdx_api": wayback_cdx_timeout_var.get(),
            "http_robots": http_robots_timeout_var.get(),
            "http_sitemap": http_sitemap_timeout_var.get(),
        }
    }


# ----------------------------
# Run
# ----------------------------

def run_erebus():
    target = entry_target.get().strip()

    if not target:
        messagebox.showerror("Error", "Introduce un dominio")
        return

    output.delete("1.0", tk.END)

    db = Database()
    if APP_CONFIG["debug"]["clear_db_on_run"]:
        db.clear_all()

    orchestrator = Orchestrator(db)
    execution = Execution(target)
    db.insert_execution(execution)

    try:
        cfg = build_config_from_ui()
        orchestrator.run(execution, cfg)
        execution.finish()

    except Exception as e:
        execution.STATUS = "ERROR"
        execution.END = execution.END or execution.START
        print("[ERROR]", e)

    finally:
        db.update_execution(execution)


def on_crawler_toggle():
    state = "normal" if crawler_var.get() else "disabled"

    js_check.config(state=state)
    scraping_check.config(state=state)

    # 🆕 robots / sitemap entries
    for widget in (
            http_robots_timeout_entry,
            http_sitemap_timeout_entry,
            sitemap_max_urls_entry,
            robots_max_urls_entry,
    ):
        widget.config(state=state)

    if not crawler_var.get():
        js_var.set(False)
        scraping_var.set(False)
        wayback_var.set(False)
def on_dns_toggle():
    state = "normal" if dns_var.get() else "disabled"
    security_headers_check.config(state=state)

    if not dns_var.get():
        security_headers_var.set(False)
# ----------------------------
# UI Layout helpers
# ----------------------------
def row_label(text, r):
    tk.Label(options, text=text, font=("Segoe UI", 9, "bold")).grid(row=r, column=0, sticky="w", pady=(8, 2))
def row_check(text, r, var):
    tk.Checkbutton(options, text=text, variable=var).grid(row=r, column=0, sticky="w")
def row_entry(r, c, var, w=6, padx=6):
    e = tk.Entry(options, width=w, textvariable=var)
    e.grid(row=r, column=c, padx=padx)
    return e
def row_hint(text, r, c=2):
    tk.Label(options, text=text).grid(row=r, column=c, sticky="w")

# ----------------------------
# UI
# ----------------------------

root = tk.Tk()
root.title("EREBUS")

tk.Label(root, text="Objetivo (dominio):").pack(anchor="w")
entry_target = tk.Entry(root, width=40)
entry_target.pack(anchor="w", pady=4)

options = tk.Frame(root)
options.pack(anchor="w", pady=6)

# Vars
subdomains_var = tk.BooleanVar(value=True)
whois_var = tk.BooleanVar(value=True)
dns_var = tk.BooleanVar(value=True)
security_headers_var = tk.BooleanVar(value=True)
emails_var = tk.BooleanVar(value=True)
crawler_var = tk.BooleanVar(value=True)
js_var = tk.BooleanVar(value=False)
scraping_var = tk.BooleanVar(value=False)
wayback_var = tk.BooleanVar(value=True)

# --- TIMEOUT VARS ---
http_email_var = tk.IntVar(value=APP_CONFIG["timeouts"]["http_passive_email"])
http_subdomains_var = tk.IntVar(value=APP_CONFIG["timeouts"]["http_subdomains"])
dns_timeout_var = tk.IntVar(value=APP_CONFIG["timeouts"]["dns_resolution"])
crawler_live_timeout_var = tk.IntVar(value=APP_CONFIG["timeouts"]["crawler_live_page"])
crawler_wayback_timeout_var = tk.IntVar(value=APP_CONFIG["timeouts"]["crawler_wayback_page"])
js_connect_var = tk.IntVar(value=APP_CONFIG["timeouts"]["js_connect"])
js_read_var = tk.IntVar(value=APP_CONFIG["timeouts"]["js_read"])
scraping_timeout_var = tk.IntVar(value=APP_CONFIG["timeouts"]["scraping_page_load"])
wayback_cdx_timeout_var = tk.IntVar(value=APP_CONFIG["timeouts"]["wayback_cdx_api"])
http_robots_timeout_var = tk.IntVar(value=APP_CONFIG["timeouts"]["http_robots"])
http_sitemap_timeout_var = tk.IntVar(value=APP_CONFIG["timeouts"]["http_sitemap"])
http_security_headers_var = tk.IntVar(value=APP_CONFIG["timeouts"]["http_security_headers"])

# --- LIMIT VARS ---
max_subdomains_var = tk.IntVar(value=APP_CONFIG["limits"]["subdomain_max"])
dns_max_domains_var = tk.IntVar(value=APP_CONFIG["limits"]["dns_max_domains"])
crawler_live_max_pages_var = tk.IntVar(value=APP_CONFIG["limits"]["crawler_live_max_pages"])
crawler_wayback_max_pages_var = tk.IntVar(value=APP_CONFIG["limits"]["crawler_wayback_max_pages"])
wayback_max_snapshots_var = tk.IntVar(value=APP_CONFIG["limits"]["wayback_max_snapshots"])
wayback_min_year_var = tk.IntVar(value=APP_CONFIG["limits"]["wayback_min_year"])
js_max_scripts_var = tk.IntVar(value=APP_CONFIG["limits"]["js_max_scripts"])
sitemap_max_urls_var = tk.IntVar(value=APP_CONFIG["limits"]["sitemap_max_urls"])
robots_max_urls_var = tk.IntVar(value=APP_CONFIG["limits"]["robots_max_urls"])
cdx_url_limit_var = tk.IntVar(value=APP_CONFIG["limits"]["cdx_url_limit"])
r = 0

# =========================
# BÁSICO
# =========================
row_label("Básico", r); r += 1

row_check("Subdominios (crt.sh)", r, subdomains_var)
r += 1
row_hint("timeout (s):", r, 1)
row_entry(r, 2, http_subdomains_var, w=4)
row_hint("limit:", r, 3)
row_entry(r, 4, max_subdomains_var, w=5)
r += 1

row_check("WHOIS", r, whois_var)
r += 1

tk.Checkbutton(
    options,
    text="DNS",
    variable=dns_var,
    command=on_dns_toggle
).grid(row=r, column=0, sticky="w")

row_hint("timeout (s):", r, 1)
row_entry(r, 2, dns_timeout_var, w=4)
row_hint("max:", r, 3)
row_entry(r, 4, dns_max_domains_var, w=5)
security_headers_check = tk.Checkbutton(options,text="Security Headers",variable=security_headers_var)
security_headers_check.grid(row=r, column=6, sticky="w")
row_entry(r, 8, http_security_headers_var, w=4)
row_hint("timeout:", r, 7)
r += 1

row_check("Emails pasivos (HTML)", r, emails_var)
row_hint("timeout (s):", r, 1)
row_entry(r, 2, http_email_var, w=4)
r += 1


# =========================
# CRAWLER LIVE
# =========================
row_label("Crawler (LIVE)", r); r += 1

crawler_check = tk.Checkbutton(
    options,
    text="Crawler HTML",
    variable=crawler_var,
    command=on_crawler_toggle
)
crawler_check.grid(row=r, column=0, sticky="w")

row_hint("timeout (s):", r, 1)
row_entry(r, 2, crawler_live_timeout_var, w=4)

row_hint("max pages:", r, 3)
row_entry(r, 4, crawler_live_max_pages_var, w=6)
r += 1

# --- ROBOTS & SITEMAP ---
tk.Label(options, text="robots.txt / sitemap", font=("Segoe UI", 8, "italic"))\
    .grid(row=r, column=0, sticky="w", pady=(4, 2))
r += 1

row_hint("robots timeout (s):", r, 0)
http_robots_timeout_entry = row_entry(r, 1, http_robots_timeout_var, w=4)

row_hint("sitemap timeout (s):", r, 2)
http_sitemap_timeout_entry = row_entry(r, 3, http_sitemap_timeout_var, w=4)

row_hint("max sitemap URLs:", r, 4)
sitemap_max_urls_entry   = row_entry(r, 5, sitemap_max_urls_var, w=6)

row_hint("max robots URLs:", r, 6)
robots_max_urls_entry = row_entry(r, 7, robots_max_urls_var, w=6)

r += 1

# =========================
# WAYBACK
# =========================
row_label("Wayback Machine", r); r += 1

wayback_check = tk.Checkbutton(
    options,
    text="Snapshots históricos",
    variable=wayback_var
)
wayback_check.grid(row=r, column=0, sticky="w")

row_hint("CDX timeout (s):", r, 1)
row_entry(r, 2, wayback_cdx_timeout_var, w=4)

row_hint("max snapshots:", r, 3)
row_entry(r, 4, wayback_max_snapshots_var, w=6)
r += 1

tk.Label(options, text="Año mínimo:").grid(row=r, column=0, sticky="w")
row_entry(r, 1, wayback_min_year_var, w=6)

tk.Label(options, text="timeout snapshot (s):").grid(row=r, column=2, sticky="w")
row_entry(r, 3, crawler_wayback_timeout_var, w=4)

tk.Label(options, text="max pages:").grid(row=r, column=4, sticky="w")
row_entry(r, 5, crawler_wayback_max_pages_var, w=6)

tk.Label(options, text="max url cdx:").grid(row=r, column=6, sticky="w")
row_entry(r, 7, cdx_url_limit_var, w=6)
r += 1


# =========================
# JS + SCRAPING
# =========================
row_label("JS + Scraping (requiere Crawler LIVE)", r); r += 1

js_check = tk.Checkbutton(
    options,
    text="Parsing JS",
    variable=js_var
)
js_check.grid(row=r, column=0, sticky="w")

row_hint("max scripts:", r, 1)
row_entry(r, 2, js_max_scripts_var, w=5)

row_hint("conn / read:", r, 3)
row_entry(r, 4, js_connect_var, w=3)
row_entry(r, 5, js_read_var, w=3)
r += 1

scraping_check = tk.Checkbutton(
    options,
    text="Scraping activo (Playwright)",
    variable=scraping_var
)
scraping_check.grid(row=r, column=0, sticky="w")

row_hint("timeout (ms):", r, 1)
row_entry(r, 2, scraping_timeout_var, w=7)
r += 1

# =========================
# RUN BUTTON
# =========================
run_button = tk.Button(
    root,
    text="Ejecutar análisis",
    command=run_erebus
)
run_button.pack(pady=10)

# =========================
# OUTPUT
# =========================
output = tk.Text(root, width=100, height=20)
output.pack(pady=8)

# sincronizar estados iniciales
on_crawler_toggle()


root.mainloop()
