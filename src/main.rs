use sigmaos_desktop_component::{
    Rect, WindowManager, FileManager, Theme, ThemeManager,
};
use anyhow::Result;

fn main() -> Result<()> {
    env_logger::init();
    
    // Demonstrate window management
    let mut wm = WindowManager::new();
    let rect = Rect::new(100, 100, 800, 600);
    let window_id = wm.create_window("Test Window".to_string(), rect);
    wm.focus_window(window_id).map_err(|e| anyhow::anyhow!(e))?;
    println!("Window created and focused: {}", window_id);
    
    // Demonstrate file management
    let fm = FileManager::default();
    let files = fm.list_directory()?;
    println!("Directory listing: {} files", files.len());
    
    // Demonstrate theme management
    let mut tm = ThemeManager::new();
    let theme = Theme::new("SigmaOS Default".to_string());
    tm.add_theme(theme);
    tm.set_current_theme("SigmaOS Default").map_err(|e| anyhow::anyhow!(e))?;
    println!("Theme set successfully");
    
    Ok(())
}
