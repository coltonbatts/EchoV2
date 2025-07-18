#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::time::Duration;
use std::collections::HashMap;
use tauri::{Manager, State, command};
use tokio::time::sleep;
use keyring::Entry;
use serde::{Deserialize, Serialize};

const SERVICE_NAME: &str = "com.echov2.app";
const API_KEY_PREFIX: &str = "api_key";

#[derive(Debug, Serialize, Deserialize)]
struct SecureStorageError {
    message: String,
}

impl std::fmt::Display for SecureStorageError {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "{}", self.message)
    }
}

impl std::error::Error for SecureStorageError {}

#[derive(Debug, Serialize, Deserialize)]
struct ApiKeyData {
    provider: String,
    api_key: String,
    custom_endpoint: Option<String>,
}

// Secure storage commands
#[command]
async fn store_api_key(
    provider: String,
    api_key: String,
    custom_endpoint: Option<String>,
) -> Result<(), String> {
    let key_name = format!("{}_{}", API_KEY_PREFIX, provider);
    
    match Entry::new(SERVICE_NAME, &key_name) {
        Ok(entry) => {
            let data = ApiKeyData {
                provider: provider.clone(),
                api_key,
                custom_endpoint,
            };
            
            let serialized = serde_json::to_string(&data)
                .map_err(|e| format!("Failed to serialize API key data: {}", e))?;
            
            entry.set_password(&serialized)
                .map_err(|e| format!("Failed to store API key for {}: {}", provider, e))?;
            
            println!("API key stored securely for provider: {}", provider);
            Ok(())
        }
        Err(e) => Err(format!("Failed to create keyring entry for {}: {}", provider, e)),
    }
}

#[command]
async fn get_api_key(provider: String) -> Result<Option<ApiKeyData>, String> {
    let key_name = format!("{}_{}", API_KEY_PREFIX, provider);
    
    match Entry::new(SERVICE_NAME, &key_name) {
        Ok(entry) => {
            match entry.get_password() {
                Ok(password) => {
                    let data: ApiKeyData = serde_json::from_str(&password)
                        .map_err(|e| format!("Failed to deserialize API key data: {}", e))?;
                    Ok(Some(data))
                }
                Err(keyring::Error::NoEntry) => Ok(None),
                Err(e) => Err(format!("Failed to retrieve API key for {}: {}", provider, e)),
            }
        }
        Err(e) => Err(format!("Failed to create keyring entry for {}: {}", provider, e)),
    }
}

#[command]
async fn delete_api_key(provider: String) -> Result<(), String> {
    let key_name = format!("{}_{}", API_KEY_PREFIX, provider);
    
    match Entry::new(SERVICE_NAME, &key_name) {
        Ok(entry) => {
            match entry.delete_password() {
                Ok(()) => {
                    println!("API key deleted for provider: {}", provider);
                    Ok(())
                }
                Err(keyring::Error::NoEntry) => Ok(()), // Already deleted
                Err(e) => Err(format!("Failed to delete API key for {}: {}", provider, e)),
            }
        }
        Err(e) => Err(format!("Failed to create keyring entry for {}: {}", provider, e)),
    }
}

#[command]
async fn list_stored_providers() -> Result<Vec<String>, String> {
    // Note: Keyring doesn't provide enumeration, so we'll check common providers
    let common_providers = vec!["openai", "anthropic", "google", "ollama"];
    let mut stored_providers = Vec::new();
    
    for provider in common_providers {
        if let Ok(Some(_)) = get_api_key(provider.to_string()).await {
            stored_providers.push(provider.to_string());
        }
    }
    
    Ok(stored_providers)
}

#[command]
async fn migrate_from_localstorage(
    provider: String,
    api_key: String,
    custom_endpoint: Option<String>,
) -> Result<(), String> {
    // Store in secure storage and return success
    store_api_key(provider, api_key, custom_endpoint).await
}

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
        .invoke_handler(tauri::generate_handler![
            store_api_key,
            get_api_key,
            delete_api_key,
            list_stored_providers,
            migrate_from_localstorage
        ])
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