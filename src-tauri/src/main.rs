#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::{
    env,
    fs,
    path::{Path, PathBuf},
    process::{Child, Command, Stdio},
    sync::{Arc, Mutex},
    thread,
};
use tauri::{Emitter, Manager, RunEvent, WindowEvent};
use std::io::Write;

fn log_backend(msg: &str) {
    if let Ok(mut f) = fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open("/tmp/deadball-backend.log")
    {
        let _ = writeln!(f, "{}", msg);
    }
}

type SharedChild = Arc<Mutex<Option<Child>>>;

fn resolve_backend_dir(app: Option<&tauri::AppHandle>) -> PathBuf {
    // Prefer a known development absolute path if it exists (useful when running a local bundle).
    let dev_absolute = PathBuf::from("/Users/steve/dev/web/deadball-web/backend");
    if dev_absolute.exists() {
        log_backend("Using dev backend path: /Users/steve/dev/web/deadball-web/backend");
        return dev_absolute;
    }
    // Prefer bundled Resources/backend when packaged.
    if let Some(handle) = app {
        if let Ok(res_dir) = handle.path().resource_dir() {
            let bundled = res_dir.join("backend");
            if bundled.exists() {
                log_backend(&format!(
                    "Using bundled backend path from resources: {}",
                    bundled.display()
                ));
                return bundled;
            }
        }
    }
    // Fallback to dev relative path (repo layout).
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
    PathBuf::from("../backend")
}

fn python_cmd(backend_dir: &Path) -> PathBuf {
    // Prefer project venv if present, fallback to python3 in PATH.
    let venv_python = backend_dir.join(".venv/bin/python");
    if venv_python.exists() {
        log_backend(&format!("Using venv python at {}", venv_python.display()));
        venv_python
    } else {
        env::var_os("PYTHON")
            .map(PathBuf::from)
            .unwrap_or_else(|| PathBuf::from("python3"))
    }
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

fn launch_backend(proc_ref: SharedChild, app_handle: tauri::AppHandle) {
    thread::spawn(move || {
        let backend_dir = resolve_backend_dir(Some(&app_handle));
        match spawn_backend(&backend_dir) {
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

fn main() {
    let backend_proc: SharedChild = Arc::new(Mutex::new(None));

    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![save_scorecard_pdf])
        .setup({
            let backend_proc = backend_proc.clone();
            move |app| {
                launch_backend(backend_proc.clone(), app.handle().clone());
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
