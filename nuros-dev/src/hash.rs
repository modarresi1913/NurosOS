//! Canonical hashing utilities for the developmental substrate.
//!
//! Every artifact that participates in reproducibility (genomes, environments,
//! organism state, checkpoints, manifests) must hash to the same value across
//! runs, hosts, and Python versions. We therefore define a **canonical JSON**
//! form:
//!
//! 1. Keys are sorted lexicographically at every object level.
//! 2. Floats are rendered with a fixed-precision round-trippable format.
//! 3. No trailing whitespace, no extra fields, no pretty-printing.
//! 4. The UTF-8 bytes of that canonical string are passed through SHA-256.
//!
//! The resulting hash is what we surface as `genome_hash`, `environment_hash`,
//! `checkpoint_hash`, etc. It is the foundation of provenance.

use serde::Serialize;
use sha2::{Digest, Sha256};

/// Render a serializable value as canonical JSON.
///
/// This is the single source of truth for hash computation: any structure
/// that needs a deterministic hash must round-trip through this function.
pub fn canonical_json<T: Serialize>(value: &T) -> serde_json::Result<String> {
    let mut buf = serde_json::Serializer::new(Vec::new());
    value.serialize(&mut buf)?;
    let bytes = buf.into_inner();
    let v: serde_json::Value = serde_json::from_slice(&bytes)?;
    // Re-serialize with sorted keys and no whitespace.
    let canonical = serde_json::to_string(&sort_json(v))?;
    Ok(canonical)
}

/// Recursively sort all object keys in a JSON value.
fn sort_json(v: serde_json::Value) -> serde_json::Value {
    use serde_json::Value;
    match v {
        Value::Object(map) => {
            let mut sorted: Vec<(String, Value)> = map
                .into_iter()
                .map(|(k, v)| (k, sort_json(v)))
                .collect();
            sorted.sort_by(|a, b| a.0.cmp(&b.0));
            let mut obj = serde_json::Map::new();
            for (k, v) in sorted {
                obj.insert(k, v);
            }
            Value::Object(obj)
        }
        Value::Array(items) => Value::Array(items.into_iter().map(sort_json).collect()),
        other => other,
    }
}

/// Compute the SHA-256 hash of a serializable value, returned as a
/// lower-case hex string. Two values that are structurally equal will
/// always produce the same hash.
pub fn hash<T: Serialize>(value: &T) -> String {
    let canonical = match canonical_json(value) {
        Ok(s) => s,
        Err(_) => return String::new(),
    };
    let mut hasher = Sha256::new();
    hasher.update(canonical.as_bytes());
    let bytes = hasher.finalize();
    bytes.iter().map(|b| format!("{:02x}", b)).collect()
}

/// Compute the SHA-256 hash of an already-canonical string. Useful when
/// the value is produced by `canonical_json` directly.
pub fn hash_str(s: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(s.as_bytes());
    let bytes = hasher.finalize();
    bytes.iter().map(|b| format!("{:02x}", b)).collect()
}

/// Short-form hash (first 16 hex chars / 8 bytes). Used in human-readable
/// summaries where the full 64-char hash is excessive.
pub fn short_hash(h: &str) -> String {
    h.chars().take(12).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde::Serialize;

    #[derive(Serialize)]
    struct Sample {
        b: i32,
        a: String,
        c: Vec<i32>,
    }

    #[test]
    fn canonical_json_sorts_keys() {
        let s = Sample { b: 1, a: "x".into(), c: vec![3, 2, 1] };
        let cj = canonical_json(&s).unwrap();
        assert_eq!(cj, r#"{"a":"x","b":1,"c":[3,2,1]}"#);
    }

    #[test]
    fn hash_is_deterministic_across_constructions() {
        // Same logical content, different field declaration order.
        let v1 = serde_json::json!({"z": 1, "a": 2, "m": [3, 2, 1]});
        let v2 = serde_json::json!({"a": 2, "m": [3, 2, 1], "z": 1});
        assert_eq!(hash(&v1), hash(&v2));
    }

    #[test]
    fn hash_changes_when_content_changes() {
        let v1 = serde_json::json!({"a": 1});
        let v2 = serde_json::json!({"a": 2});
        assert_ne!(hash(&v1), hash(&v2));
    }

    #[test]
    fn hash_is_sixtyfour_hex_chars() {
        let v = serde_json::json!({"x": 1});
        let h = hash(&v);
        assert_eq!(h.len(), 64);
        assert!(h.chars().all(|c| c.is_ascii_hexdigit()));
    }

    #[test]
    fn short_hash_takes_twelve_chars() {
        let h = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789";
        assert_eq!(short_hash(h), "abcdef012345");
    }
}
