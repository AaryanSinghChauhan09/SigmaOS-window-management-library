//! SigmaOS-window-management-library
//!
//! Core window management APIs, compositing support, theme management, and file integration.
//! Follows: Component Isolation, High Cohesion, Low Coupling, Arrange-Act-Assert.

pub mod window;
pub mod file;
pub mod theme;

pub use window::{Window, WindowManager, WindowState, WindowType, Rect};
pub use file::{FileManager, FileMetadata, FileError, FileResult};
pub use theme::{Theme, ThemeManager, Color, ColorPalette};

/// Initialize the window management library.
pub fn init() {
    // Subsystems initialized
}
