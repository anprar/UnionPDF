//! Atomic "Save As": produce into a temp file in the destination folder, verify it,
//! then rename over the destination. The input file is never a valid destination.

use crate::error::{AppError, AppResult};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

/// Normalises a path for "is this the same file?" comparisons (case-insensitive on Windows).
fn same_file(a: &Path, b: &Path) -> bool {
    let ca = std::fs::canonicalize(a).unwrap_or_else(|_| a.to_path_buf());
    let cb = std::fs::canonicalize(b).unwrap_or_else(|_| b.to_path_buf());
    if cfg!(windows) {
        ca.to_string_lossy().to_lowercase() == cb.to_string_lossy().to_lowercase()
    } else {
        ca == cb
    }
}

pub fn temp_path_for(dest: &Path) -> PathBuf {
    let nanos = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_nanos()).unwrap_or(0);
    let name = dest.file_name().map(|n| n.to_string_lossy().to_string()).unwrap_or_else(|| "output.pdf".into());
    dest.with_file_name(format!(".{name}.unionpdf-{}-{nanos}.tmp", std::process::id()))
}

/// Runs `produce(temp)` then `verify(temp)`, and only then renames temp -> dest.
/// On any failure or cancellation the temp file is removed and `dest` is left untouched.
pub fn write_atomic<V>(
    dest: &Path,
    inputs: &[&Path],
    cancel: &AtomicBool,
    produce: impl FnOnce(&Path) -> AppResult<()>,
    verify: impl FnOnce(&Path) -> AppResult<V>,
) -> AppResult<V> {
    if dest.as_os_str().is_empty() {
        return Err(AppError::InvalidInput("path tujuan kosong".into()));
    }
    for input in inputs {
        if same_file(dest, input) {
            return Err(AppError::WouldOverwriteInput(dest.to_path_buf()));
        }
    }
    let parent = dest.parent().filter(|p| !p.as_os_str().is_empty()).unwrap_or(Path::new("."));
    if !parent.is_dir() {
        return Err(AppError::Io(format!("folder tujuan tidak ada: {}", parent.display())));
    }
    let temp = temp_path_for(dest);
    let cleanup = |t: &Path| {
        let _ = std::fs::remove_file(t);
    };
    if cancel.load(Ordering::SeqCst) {
        return Err(AppError::Cancelled);
    }
    if let Err(e) = produce(&temp) {
        cleanup(&temp);
        return Err(e);
    }
    if cancel.load(Ordering::SeqCst) {
        cleanup(&temp);
        return Err(AppError::Cancelled);
    }
    let verified = match verify(&temp) {
        Ok(v) => v,
        Err(e) => {
            cleanup(&temp);
            return Err(match e {
                AppError::VerificationFailed(_) | AppError::Cancelled => e,
                other => AppError::VerificationFailed(other.to_string()),
            });
        }
    };
    if cancel.load(Ordering::SeqCst) {
        cleanup(&temp);
        return Err(AppError::Cancelled);
    }
    if let Err(e) = std::fs::rename(&temp, dest) {
        cleanup(&temp);
        return Err(AppError::Io(format!("gagal memfinalisasi berkas tujuan: {e}")));
    }
    Ok(verified)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    fn scratch(name: &str) -> PathBuf {
        let d = std::env::temp_dir().join(format!("unionpdf-atomic-test-{}-{name}", std::process::id()));
        let _ = fs::remove_dir_all(&d);
        fs::create_dir_all(&d).unwrap();
        d
    }

    fn leftover_temps(dir: &Path) -> usize {
        fs::read_dir(dir).unwrap().filter(|e| e.as_ref().unwrap().file_name().to_string_lossy().ends_with(".tmp")).count()
    }

    #[test]
    fn success_writes_destination_and_removes_temp() {
        let d = scratch("ok");
        let dest = d.join("out.pdf");
        let never = AtomicBool::new(false);
        let r = write_atomic(&dest, &[], &never, |t| Ok(fs::write(t, b"%PDF-new")?), |t| Ok(fs::read(t)?.len()));
        assert_eq!(r.unwrap(), 8);
        assert_eq!(fs::read(&dest).unwrap(), b"%PDF-new");
        assert_eq!(leftover_temps(&d), 0);
    }

    #[test]
    fn verification_failure_keeps_existing_destination() {
        let d = scratch("verify");
        let dest = d.join("out.pdf");
        fs::write(&dest, b"OLD").unwrap();
        let never = AtomicBool::new(false);
        let r: AppResult<()> = write_atomic(
            &dest,
            &[],
            &never,
            |t| Ok(fs::write(t, b"%PDF-bad")?),
            |_| Err(AppError::VerificationFailed("jumlah halaman berbeda".into())),
        );
        assert!(matches!(r, Err(AppError::VerificationFailed(_))));
        assert_eq!(fs::read(&dest).unwrap(), b"OLD");
        assert_eq!(leftover_temps(&d), 0);
    }

    #[test]
    fn produce_failure_leaves_no_partial_file() {
        let d = scratch("produce");
        let dest = d.join("out.pdf");
        let never = AtomicBool::new(false);
        let r: AppResult<()> = write_atomic(
            &dest,
            &[],
            &never,
            |t| {
                fs::write(t, b"%PDF-partial")?;
                Err(AppError::Io("disk penuh (simulasi)".into()))
            },
            |_| Ok(()),
        );
        assert!(matches!(r, Err(AppError::Io(_))));
        assert!(!dest.exists());
        assert_eq!(leftover_temps(&d), 0);
    }

    #[test]
    fn refuses_to_overwrite_input() {
        let d = scratch("input");
        let input = d.join("Input File.pdf");
        fs::write(&input, b"%PDF-src").unwrap();
        let alias = d.join("input file.PDF"); // same file on Windows (case-insensitive)
        let never = AtomicBool::new(false);
        let r: AppResult<()> = write_atomic(&input, &[&input], &never, |_| Ok(()), |_| Ok(()));
        assert!(matches!(r, Err(AppError::WouldOverwriteInput(_))));
        if cfg!(windows) {
            let r2: AppResult<()> = write_atomic(&alias, &[&input], &never, |_| Ok(()), |_| Ok(()));
            assert!(matches!(r2, Err(AppError::WouldOverwriteInput(_))));
        }
        assert_eq!(fs::read(&input).unwrap(), b"%PDF-src");
    }

    #[test]
    fn cancellation_before_finalise_leaves_destination_untouched() {
        let d = scratch("cancel");
        let dest = d.join("out.pdf");
        let cancel = AtomicBool::new(false);
        let r: AppResult<()> = write_atomic(
            &dest,
            &[],
            &cancel,
            |t| {
                fs::write(t, b"%PDF-x")?;
                cancel.store(true, Ordering::SeqCst);
                Ok(())
            },
            |_| Ok(()),
        );
        assert_eq!(r, Err(AppError::Cancelled));
        assert!(!dest.exists());
        assert_eq!(leftover_temps(&d), 0);
    }

    #[test]
    fn missing_destination_folder_is_reported() {
        let d = scratch("nofolder");
        let dest = d.join("tidak-ada").join("out.pdf");
        let never = AtomicBool::new(false);
        let r: AppResult<()> = write_atomic(&dest, &[], &never, |_| Ok(()), |_| Ok(()));
        assert!(matches!(r, Err(AppError::Io(_))));
    }
}
