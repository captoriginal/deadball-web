#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::{
    env,
    fs,
    path::PathBuf,
    process::{Child, Command, Stdio},
    sync::{Arc, Mutex},
    thread,
};
use tauri::{Emitter, RunEvent, WindowEvent};

type SharedChild = Arc<Mutex<Option<Child>>>;

fn python_cmd() -> PathBuf {
    // Prefer project venv if present, fallback to python3 in PATH.
    let venv_python = PathBuf::from("../backend/.venv/bin/python");
    if venv_python.exists() {
        venv_python
    } else {
        env::var_os("PYTHON")
            .map(PathBuf::from)
            .unwrap_or_else(|| PathBuf::from("python3"))
    }
}

fn spawn_backend() -> std::io::Result<Child> {
    let mut cmd = Command::new(python_cmd());
    cmd.args([
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ])
    .current_dir("../backend")
    // Prefer the project's venv site-packages if available.
    .env("PYTHONPATH", "../backend")
    // Surface backend logs while developing; swap to Stdio::null() for silence.
    .stdout(Stdio::inherit())
    .stderr(Stdio::inherit());
    cmd.spawn()
}

fn launch_backend(proc_ref: SharedChild, app_handle: tauri::AppHandle) {
    thread::spawn(move || match spawn_backend() {
        Ok(child) => {
            *proc_ref.lock().unwrap() = Some(child);
        }
        Err(err) => {
            eprintln!("Failed to start backend: {err}");
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
