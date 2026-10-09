use base64::Engine;
use std::{fs, path::Path};

fn ico_from_png(png: &[u8]) -> Vec<u8> {
    let mut out = Vec::with_capacity(22 + png.len());
    // ICONDIR
    out.extend_from_slice(&0u16.to_le_bytes()); // reserved
    out.extend_from_slice(&1u16.to_le_bytes()); // image type = icon
    out.extend_from_slice(&1u16.to_le_bytes()); // one image

    // ICONDIRENTRY matches the embedded 64x64 PNG.
    out.push(64);
    out.push(64);
    out.push(0);
    out.push(0);
    out.extend_from_slice(&1u16.to_le_bytes());  // color planes
    out.extend_from_slice(&32u16.to_le_bytes()); // bpp
    out.extend_from_slice(&(png.len() as u32).to_le_bytes());
    out.extend_from_slice(&22u32.to_le_bytes());
    out.extend_from_slice(png);
    out
}

fn main() {
    let icon_dir = Path::new("icons");
    fs::create_dir_all(icon_dir).expect("create icons directory");

    let encoded = "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAABiElEQVR4nO3bQWoCURCE4TLkBFnlAAFdeP+TuNDTJKtAEETndVX/genaD3Z/zrx5r9HDx+fXt3acN7oAOgNAF0BnAOgC6AwAXQCdAaALoDMAdAF0BoAugM776oW368VZRznH03npumWA6ge7Uv0iSo/A8XRG74Tb9VL+AsprAIXgaF4yLYLdCK7mJeNboAvB2bxkfg2mEdzNS4F9QAoh0bwU2gi5EVLNS8GdoAsh2bwU3gpXEdLNSw1ngVWEjualpsPQVoSu5qXG0+CrCJ3NS83H4WcI3c1LwDzgEQLRvAQNRO4RqOYlwzxgNX8RyJnC7kdiGMDvbU8PVRCA+2eeRGgHeLTgUQitAM9WewKhDeDVV103QgvA1vd8J0IcYHWT04UQBaju8DoQYgCu7W0aIQLg3tsnEewAqYNNCsEKkD7VJRBsAF1HWjeCBaD7PO9EKANQwwwXQgmAnORIHoTyROi//VRmaw7zj5GdZwDoAugMAF0AnQGgC6AzAHQBdAaALoDOANAF0PkB/CbJIdFg2AgAAAAASUVORK5CYII=";
    let png = base64::engine::general_purpose::STANDARD
        .decode(encoded)
        .expect("decode embedded PNG");

    fs::write(icon_dir.join("icon.png"), &png).expect("write icon.png");
    fs::write(icon_dir.join("icon.ico"), ico_from_png(&png)).expect("write icon.ico");

    tauri_build::build()
}
