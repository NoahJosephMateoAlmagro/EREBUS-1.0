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
            "emails_passive": emails_var.get(),
            "crawler": crawler_var.get(),
            "js_parsing": js_var.get(),
            "scraping": scraping_var.get(),
            "wayback": wayback_var.get(),
        },
        "limits": {
            "max_dns": APP_CONFIG["limits"]["max_dns"],
            "max_pages": APP_CONFIG["limits"]["max_pages"],
            "max_scripts": APP_CONFIG["limits"]["max_scripts"],
        },
        "timeouts": {
        "http_crawler_page": http_crawler_var.get(),
        "http_email_passive": http_email_var.get(),
        "http_subdomains": http_subdomains_var.get(),
        "dns_resolution": dns_timeout_var.get(),
        "js_connect": js_connect_var.get(),
        "js_read": js_read_var.get(),
        "scraping_page_load": scraping_timeout_var.get(),
        "wayback_timeout": wayback_timeout_var.get(),    }

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

    if not crawler_var.get():
        js_var.set(False)
        scraping_var.set(False)


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
emails_var = tk.BooleanVar(value=True)
crawler_var = tk.BooleanVar(value=True)
js_var = tk.BooleanVar(value=False)
scraping_var = tk.BooleanVar(value=False)
wayback_var = tk.BooleanVar(value=True)

http_crawler_var = tk.IntVar(value=APP_CONFIG["timeouts"]["http_crawler_page"])
http_email_var = tk.IntVar(value=APP_CONFIG["timeouts"]["http_email_passive"])
http_subdomains_var = tk.IntVar(value=APP_CONFIG["timeouts"]["http_subdomains"])
dns_timeout_var = tk.IntVar(value=APP_CONFIG["timeouts"]["dns_resolution"])
js_connect_var = tk.IntVar(value=APP_CONFIG["timeouts"]["js_connect"])
js_read_var = tk.IntVar(value=APP_CONFIG["timeouts"]["js_read"])
scraping_timeout_var = tk.IntVar(value=APP_CONFIG["timeouts"]["scraping_page_load"])
wayback_timeout_var = tk.IntVar( value=APP_CONFIG["timeouts"]["wayback_timeout"])


def add_row(row, text, var, timeout_var=None):
    tk.Checkbutton(options, text=text, variable=var).grid(row=row, column=0, sticky="w")
    if timeout_var:
        tk.Entry(options, width=6, textvariable=timeout_var).grid(row=row, column=1, padx=20)

add_row(0, "Subdominios (crt.sh)", subdomains_var, http_subdomains_var)
add_row(1, "WHOIS", whois_var)
add_row(2, "DNS", dns_var, dns_timeout_var)
add_row(3, "Emails passive", emails_var, http_email_var)
add_row(4, "Wayback (URLS históricas)", wayback_var, wayback_timeout_var)

crawler_check = tk.Checkbutton(
    options, text="Crawler HTML", variable=crawler_var, command=on_crawler_toggle
)
crawler_check.grid(row=5, column=0, sticky="w")
tk.Entry(options, width=6, textvariable=http_crawler_var).grid(row=5, column=1, padx=6)

js_check = tk.Checkbutton(options, text="Parsing JS", variable=js_var)
js_check.grid(row=6, column=0, sticky="w")
tk.Label(options, text="conn/read").grid(row=6, column=1, sticky="w")
tk.Entry(options, width=3, textvariable=js_connect_var).grid(row=6, column=2)
tk.Entry(options, width=3, textvariable=js_read_var).grid(row=6, column=3)

scraping_check = tk.Checkbutton(options, text="Scraping", variable=scraping_var)
scraping_check.grid(row=7, column=0, sticky="w")
tk.Entry(options, width=6, textvariable=scraping_timeout_var).grid(row=7, column=1, padx=6)

on_crawler_toggle()

tk.Button(root, text="Ejecutar análisis", command=run_erebus).pack(pady=8)

output = tk.Text(root, width=100, height=20)
output.pack()

root.mainloop()
