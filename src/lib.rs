#[derive(Debug, Clone)]
pub struct WindowGeometry {
    pub x: i32,
    pub y: i32,
    pub width: u32,
    pub height: u32,
}

pub struct WindowLayoutEngine;
impl WindowLayoutEngine {
    pub fn compute_split_horizontal(w: u32, h: u32) -> (WindowGeometry, WindowGeometry) {
        let half = w / 2;
        (
            WindowGeometry { x: 0, y: 0, width: half, height: h },
            WindowGeometry { x: half as i32, y: 0, width: w - half, height: h },
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_window_horizontal_split() {
        let (left, right) = WindowLayoutEngine::compute_split_horizontal(1920, 1080);
        assert_eq!(left.width, 960);
        assert_eq!(right.width, 960);
    }
}
