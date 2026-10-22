//! Cancellation registry for long-running operations, keyed by a job id chosen by the UI.

use crate::error::AppResult;
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};

#[derive(Default)]
pub struct JobRegistry {
    jobs: Mutex<HashMap<String, Arc<AtomicBool>>>,
}

impl JobRegistry {
    pub fn register(&self, id: &str) -> Arc<AtomicBool> {
        let flag = Arc::new(AtomicBool::new(false));
        self.jobs.lock().unwrap().insert(id.to_string(), flag.clone());
        flag
    }

    /// Returns true if a running job with this id was found and signalled.
    pub fn cancel(&self, id: &str) -> bool {
        match self.jobs.lock().unwrap().get(id) {
            Some(f) => {
                f.store(true, Ordering::SeqCst);
                true
            }
            None => false,
        }
    }

    pub fn finish(&self, id: &str) {
        self.jobs.lock().unwrap().remove(id);
    }
}

/// E2E test hook (only with the `e2e-hooks` cargo feature): waits `UNIONPDF_E2E_DELAY_MS`
/// while honouring cancellation, so UI tests can press "Batalkan" during a job.
pub fn e2e_delay(cancel: &AtomicBool) -> AppResult<()> {
    #[cfg(feature = "e2e-hooks")]
    if let Some(ms) = std::env::var("UNIONPDF_E2E_DELAY_MS").ok().and_then(|v| v.parse::<u64>().ok()) {
        let end = std::time::Instant::now() + std::time::Duration::from_millis(ms);
        while std::time::Instant::now() < end {
            if cancel.load(Ordering::SeqCst) {
                return Err(crate::error::AppError::Cancelled);
            }
            std::thread::sleep(std::time::Duration::from_millis(25));
        }
    }
    let _ = cancel;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cancel_signals_registered_job_only() {
        let r = JobRegistry::default();
        let f = r.register("a");
        assert!(!r.cancel("b"));
        assert!(r.cancel("a"));
        assert!(f.load(Ordering::SeqCst));
        r.finish("a");
        assert!(!r.cancel("a"));
    }
}
