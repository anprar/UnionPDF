//! Parsing of user page selections such as "1-3, 5, 8-".

use crate::error::{AppError, AppResult};

/// Parses a 1-based selection (e.g. `"1-3, 5, 8-"`) into sorted, unique zero-based indices.
pub fn parse_selection(input: &str, page_count: u32) -> AppResult<Vec<u32>> {
    if page_count == 0 {
        return Err(AppError::InvalidInput("dokumen tidak memiliki halaman".into()));
    }
    let mut out: Vec<u32> = Vec::new();
    let text = input.trim();
    if text.is_empty() {
        return Err(AppError::InvalidInput("pilihan halaman kosong".into()));
    }
    for raw in text.split(',') {
        let part = raw.trim();
        if part.is_empty() {
            continue;
        }
        let parse = |s: &str| -> AppResult<u32> {
            s.trim()
                .parse::<u32>()
                .map_err(|_| AppError::InvalidInput(format!("'{part}' bukan nomor halaman")))
        };
        let (start, end) = match part.split_once('-') {
            Some((a, b)) => {
                let a = if a.trim().is_empty() { 1 } else { parse(a)? };
                let b = if b.trim().is_empty() { page_count } else { parse(b)? };
                (a, b)
            }
            None => {
                let n = parse(part)?;
                (n, n)
            }
        };
        if start == 0 || end == 0 || start > end || end > page_count {
            return Err(AppError::InvalidInput(format!("rentang '{part}' tidak valid untuk dokumen {page_count} halaman")));
        }
        out.extend((start - 1)..end);
    }
    out.sort_unstable();
    out.dedup();
    if out.is_empty() {
        return Err(AppError::InvalidInput("pilihan halaman kosong".into()));
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn single_and_ranges() {
        assert_eq!(parse_selection("1-3, 5", 6).unwrap(), vec![0, 1, 2, 4]);
        assert_eq!(parse_selection(" 2 ", 3).unwrap(), vec![1]);
    }

    #[test]
    fn open_ended_ranges_and_duplicates() {
        assert_eq!(parse_selection("5-", 6).unwrap(), vec![4, 5]);
        assert_eq!(parse_selection("-2", 6).unwrap(), vec![0, 1]);
        assert_eq!(parse_selection("1,1,1-2", 6).unwrap(), vec![0, 1]);
    }

    #[test]
    fn rejects_invalid() {
        for bad in ["", "0", "7", "3-2", "a", "1-x", ",", "2-9"] {
            assert!(parse_selection(bad, 6).is_err(), "harus ditolak: {bad:?}");
        }
        assert!(parse_selection("1", 0).is_err());
    }
}
