// Integration test for SigmaOS-window-management-library
// Verifies the crate builds and links as a dependency.
#![allow(unused_imports)]

use sigmaos_window_management_library as _;

#[test]
fn crate_links_and_runs() {
    assert_eq!(2 + 2, 4);
}
