use sigmaos_desktop_component::{
    Rect, WindowManager, WindowState, WindowType, Theme, ThemeManager,
};

#[test]
fn test_window_manager_lifecycle_aaa() {
    // Arrange
    let mut wm = WindowManager::new();
    let rect = Rect::new(50, 50, 1024, 768);

    // Act
    let win_id = wm.create_window("Primary Window".to_string(), rect);

    // Assert
    assert_eq!(win_id, 1);
    let win = wm.get_window(win_id).expect("Window should exist");
    assert_eq!(win.title, "Primary Window");
    assert_eq!(win.state, WindowState::Normal);
    assert_eq!(win.window_type, WindowType::Normal);
    assert!(!win.focused);

    // Act - Focus
    wm.focus_window(win_id).expect("Focus should succeed");

    // Assert - Focused
    let win = wm.get_window(win_id).unwrap();
    assert!(win.focused);

    // Act - Close
    wm.close_window(win_id).expect("Close should succeed");

    // Assert - Closed
    assert!(wm.get_window(win_id).is_none());
}

#[test]
fn test_rect_containment_aaa() {
    // Arrange
    let rect = Rect::new(100, 100, 400, 300);

    // Act & Assert
    assert!(rect.contains(100, 100)); // top-left boundary
    assert!(rect.contains(250, 200)); // center
    assert!(rect.contains(499, 399)); // bottom-right boundary
    assert!(!rect.contains(500, 400)); // outside boundary
    assert!(!rect.contains(99, 99)); // outside boundary
}

#[test]
fn test_theme_manager_styling_aaa() {
    // Arrange
    let mut tm = ThemeManager::new();
    let mut dark_theme = Theme::new("Dark Theme".to_string());
    dark_theme.set_property("wallpaper".to_string(), "default_dark.png".to_string());

    // Act
    tm.add_theme(dark_theme);
    let switch_result = tm.set_current_theme("Dark Theme");

    // Assert
    assert!(switch_result.is_ok());
    let active = tm.get_current_theme().expect("Active theme should be present");
    assert_eq!(active.name, "Dark Theme");
    assert_eq!(active.get_property("wallpaper").map(|s| s.as_str()), Some("default_dark.png"));

    // Act & Assert - non-existent theme fails fast
    assert!(tm.set_current_theme("NonExistentTheme").is_err());
}
