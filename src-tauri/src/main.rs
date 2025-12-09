#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::{
    env,
    fs::{self, OpenOptions},
    io::Write as IoWrite,
    path::{Path, PathBuf},
    process::{Child, Command, Stdio},
    sync::{Arc, Mutex},
    thread,
};
use tauri::{Emitter, Manager, RunEvent, WindowEvent};

type SharedChild = Arc<Mutex<Option<Child>>>;

fn log_backend(msg: &str) {
    if let Ok(mut f) = OpenOptions::new()
        .create(true)
        .append(true)
        .open("/tmp/deadball-backend.log")
    {
        let _ = writeln!(f, "{}", msg);
    }
}

fn python_cmd(backend_dir: &Path) -> PathBuf {
    // Prefer project venvs if present, fallback to python3 in PATH.
    let repo_root_venv = backend_dir.join("../.venv/bin/python");
    if repo_root_venv.exists() {
        log_backend(&format!(
            "Using repo root venv python at {}",
            repo_root_venv.display()
        ));
        return repo_root_venv;
    }

    let backend_venv = backend_dir.join(".venv/bin/python");
    if backend_venv.exists() {
        log_backend(&format!(
            "Using backend-local venv python at {}",
            backend_venv.display()
        ));
        return backend_venv;
    }

    env::var_os("PYTHON")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("python3"))
}

fn spawn_backend(backend_dir: &Path) -> std::io::Result<Child> {
    let mut cmd = Command::new(python_cmd(backend_dir));
    log_backend(&format!("Spawning backend from dir {}", backend_dir.display()));
    cmd.args([
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ])
    .current_dir(backend_dir)
    // Prefer the project's venv site-packages if available.
    .env("PYTHONPATH", backend_dir)
    // Surface backend logs while developing; swap to Stdio::null() for silence.
    .stdout(Stdio::inherit())
    .stderr(Stdio::inherit());
    cmd.spawn()
}

fn launch_backend(proc_ref: SharedChild, backend_dir: PathBuf, app_handle: tauri::AppHandle) {
    thread::spawn(move || match spawn_backend(&backend_dir) {
        Ok(child) => {
            *proc_ref.lock().unwrap() = Some(child);
            log_backend("Backend started successfully");
        }
        Err(err) => {
            let msg = format!("Failed to start backend: {err}");
            eprintln!("{msg}");
            log_backend(&msg);
            let _ = app_handle.emit("backend-error", err.to_string());
        }
    });
}

fn terminate_backend(proc_ref: &SharedChild) {
    if let Some(mut child) = proc_ref.lock().unwrap().take() {
        let _ = child.kill();
        let _ = child.wait();
    }
}

#[tauri::command]
fn save_scorecard_pdf(path: String, bytes: Vec<u8>) -> Result<(), String> {
    fs::write(path, bytes).map_err(|e| e.to_string())
}

fn prepare_backend(app: &tauri::App) -> PathBuf {
    // Prefer a known development absolute path if it exists (useful when running a local bundle).
    let dev_absolute = PathBuf::from("/Users/steve/dev/web/deadball-web/backend");
    if dev_absolute.exists() {
        log_backend("Using dev backend path: /Users/steve/dev/web/deadball-web/backend");
        return dev_absolute;
    }

    // Choose an app data location for a writable backend copy.
    let app_data_backend = app
        .path()
        .app_data_dir()
        .unwrap_or_else(|_| PathBuf::from("backend"))
        .join("backend");

    if app_data_backend.exists() {
        log_backend(&format!(
            "Using existing app data backend: {}",
            app_data_backend.display()
        ));
        return app_data_backend;
    }

    // Extract from bundled resources/backend-template.tar.gz into app data.
    if let Ok(res_dir) = app.path().resource_dir() {
        let archive = res_dir.join("backend-template.tar.gz");
        if archive.exists() {
            let _ = fs::create_dir_all(app_data_backend.parent().unwrap_or(&app_data_backend));
            let status = Command::new("tar")
                .args([
                    "-xzf",
                    archive
                        .to_str()
                        .unwrap_or("backend-template.tar.gz"),
                    "-C",
                    app_data_backend
                        .parent()
                        .unwrap_or(&app_data_backend)
                        .to_str()
                        .unwrap_or("."),
                ])
                .status();
            match status {
                Ok(s) if s.success() => {
                    log_backend(&format!(
                        "Extracted backend template to app data: {}",
                        app_data_backend.display()
                    ));
                    return app_data_backend;
                }
                Ok(s) => log_backend(&format!("tar exited with status: {}", s)),
                Err(err) => log_backend(&format!("Failed to run tar: {}", err)),
            }
        } else {
            log_backend("No backend-template found in resources");
        }
    } else {
        log_backend("No resource dir available");
    }

    // Fallback to dev-relative path (repo layout).
    if let Ok(exe_path) = env::current_exe() {
        if let Some(parent) = exe_path.parent() {
            let dev = parent.join("../backend");
            if dev.exists() {
                log_backend(&format!(
                    "Using dev-relative backend path next to executable: {}",
                    dev.display()
                ));
                return dev;
            }
        }
    }

    log_backend("Falling back to ../backend");
    PathBuf::from("../backend")
}

fn main() {
    let backend_proc: SharedChild = Arc::new(Mutex::new(None));

    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![save_scorecard_pdf])
        .setup({
            let backend_proc = backend_proc.clone();
            move |app| {
                let backend_path = prepare_backend(app);
                launch_backend(backend_proc.clone(), backend_path, app.handle().clone());
                Ok(())
            }
        })
        .on_window_event({
            let backend_proc = backend_proc.clone();
            move |_window, event| {
                if let WindowEvent::CloseRequested { .. } = event {
                    terminate_backend(&backend_proc);
                }
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    let backend_proc_for_run = backend_proc.clone();
    app.run(move |_app_handle, event| {
        if matches!(event, RunEvent::ExitRequested { .. } | RunEvent::Exit) {
            terminate_backend(&backend_proc_for_run);
        }
    });

    terminate_backend(&backend_proc);
}
