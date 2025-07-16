#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tauri::{Manager, State};
use tokio::time::sleep;

// Backend process state
#[derive(Default)]
struct BackendState {
    process: Arc<Mutex<Option<Child>>>,
}

// Health check the backend
async fn wait_for_backend() -> Result<(), Box<dyn std::error::Error>> {
    let client = reqwest::Client::new();
    let mut attempts = 0;
    let max_attempts = 30; // Wait up to 30 seconds
    
    while attempts < max_attempts {
        match client.get("http://localhost:8000/health").send().await {
            Ok(response) if response.status().is_success() => {
                println!("Backend is ready!");
                return Ok(());
            }
            _ => {
                attempts += 1;
                sleep(Duration::from_secs(1)).await;
            }
        }
    }
    
    Err("Backend failed to start within timeout".into())
}

// Start the backend process
async fn start_backend(backend_state: &BackendState) -> Result<(), Box<dyn std::error::Error>> {
    let mut process_guard = backend_state.process.lock().unwrap();
    
    if process_guard.is_some() {
        return Ok(()); // Already running
    }
    
    // Get the path to the backend executable
    let backend_path = if cfg!(debug_assertions) {
        // In development, use the Python script
        let backend_dir = std::env::current_exe()?
            .parent()
            .unwrap()
            .parent()
            .unwrap()
            .parent()
            .unwrap()
            .join("backend");
        
        println!("Starting backend in development mode from: {:?}", backend_dir);
        
        // Start Python backend directly
        let mut child = Command::new("python")
            .arg("main.py")
            .current_dir(backend_dir)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()?;
        
        *process_guard = Some(child);
        drop(process_guard);
        
        // Wait for backend to be ready
        wait_for_backend().await?;
        
        return Ok(());
    } else {
        // In production, use the bundled executable
        let app_dir = std::env::current_exe()?
            .parent()
            .unwrap();
        
        let backend_executable = app_dir.join("echov2-backend");
        
        if !backend_executable.exists() {
            return Err(format!("Backend executable not found at: {:?}", backend_executable).into());
        }
        
        println!("Starting backend from: {:?}", backend_executable);
        
        let mut child = Command::new(&backend_executable)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()?;
        
        *process_guard = Some(child);
        drop(process_guard);
        
        // Wait for backend to be ready
        wait_for_backend().await?;
        
        Ok(())
    }
}

// Stop the backend process
fn stop_backend(backend_state: &BackendState) {
    let mut process_guard = backend_state.process.lock().unwrap();
    
    if let Some(mut child) = process_guard.take() {
        println!("Stopping backend process...");
        let _ = child.kill();
        let _ = child.wait();
    }
}

#[tokio::main]
async fn main() {
    let backend_state = BackendState::default();
    
    // Start the backend process
    if let Err(e) = start_backend(&backend_state).await {
        eprintln!("Failed to start backend: {}", e);
        std::process::exit(1);
    }
    
    let backend_state_for_app = Arc::new(backend_state);
    let backend_state_for_cleanup = backend_state_for_app.clone();
    
    tauri::Builder::default()
        .manage(backend_state_for_app)
        .setup(|_app| {
            println!("EchoV2 frontend started successfully!");
            Ok(())
        })
        .on_window_event(move |event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event.event() {
                println!("Application closing, stopping backend...");
                stop_backend(&backend_state_for_cleanup);
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}