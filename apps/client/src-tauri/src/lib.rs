use std::net::TcpStream;
use std::path::{Path, PathBuf};
use std::process::{Child, Command};
use std::sync::Mutex;
use std::time::{Duration, Instant};

use tauri::Manager;

const API_HOST: &str = "127.0.0.1";
const API_PORT: u16 = 8000;
const API_CONNECT_TIMEOUT: Duration = Duration::from_millis(300);
const API_BOOT_TIMEOUT: Duration = Duration::from_secs(20);

struct ApiProcessState {
    child: Mutex<Option<Child>>,
}

impl ApiProcessState {
    fn new() -> Self {
        Self {
            child: Mutex::new(None),
        }
    }

    fn set_child(&self, child: Child) {
        if let Ok(mut guard) = self.child.lock() {
            *guard = Some(child);
        }
    }

    fn stop(&self) {
        if let Ok(mut guard) = self.child.lock() {
            if let Some(child) = guard.as_mut() {
                let _ = child.kill();
                let _ = child.wait();
            }
            *guard = None;
        }
    }
}

fn is_api_alive() -> bool {
    TcpStream::connect_timeout(
        &format!("{API_HOST}:{API_PORT}")
            .parse()
            .expect("invalid API socket address"),
        API_CONNECT_TIMEOUT,
    )
    .is_ok()
}

fn wait_for_api_ready() -> bool {
    let deadline = Instant::now() + API_BOOT_TIMEOUT;
    while Instant::now() < deadline {
        if is_api_alive() {
            return true;
        }
        std::thread::sleep(Duration::from_millis(250));
    }
    false
}

fn sidecar_file_name() -> &'static str {
    #[cfg(target_os = "windows")]
    {
        "stock-box-api-sidecar.exe"
    }
    #[cfg(not(target_os = "windows"))]
    {
        "stock-box-api-sidecar"
    }
}

fn resolve_sidecar_path(app: &tauri::App) -> Option<PathBuf> {
    let resolver = app.path();
    let binary_name = sidecar_file_name();

    let resource_candidate = resolver
        .resource_dir()
        .ok()
        .map(|dir| dir.join("binaries").join(binary_name));
    if let Some(path) = resource_candidate {
        if path.exists() {
            return Some(path);
        }
    }

    if cfg!(debug_assertions) {
        let debug_candidate = Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("binaries")
            .join(binary_name);
        if debug_candidate.exists() {
            return Some(debug_candidate);
        }
    }

    None
}

fn start_api_sidecar(app: &tauri::App) {
    if cfg!(debug_assertions) {
        // Dev mode uses `pnpm dev:desktop`, which already starts the API service.
        return;
    }
    if is_api_alive() {
        return;
    }

    let Some(sidecar_path) = resolve_sidecar_path(app) else {
        eprintln!("[desktop] API sidecar not found, frontend may fail to connect.");
        return;
    };

    let mut command = Command::new(sidecar_path);
    command
        .env("STOCK_BOX_API_HOST", API_HOST)
        .env("STOCK_BOX_API_PORT", API_PORT.to_string());

    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        command.creation_flags(0x0800_0000);
    }

    match command.spawn() {
        Ok(child) => {
            if let Some(state) = app.try_state::<ApiProcessState>() {
                state.set_child(child);
            }
            if !wait_for_api_ready() {
                eprintln!("[desktop] API sidecar started but readiness check timed out.");
            }
        }
        Err(error) => {
            eprintln!("[desktop] failed to start API sidecar: {error}");
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(ApiProcessState::new())
        .setup(|app| {
            start_api_sidecar(app);
            Ok(())
        })
        .plugin(tauri_plugin_opener::init())
        .build(tauri::generate_context!())
        .expect("failed to build stock-box desktop shell")
        .run(|app, event| {
            if let tauri::RunEvent::Exit = event {
                if let Some(state) = app.try_state::<ApiProcessState>() {
                    state.stop();
                }
            }
        });
}
