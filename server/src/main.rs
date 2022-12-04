use std::{collections::HashMap, io::Read, thread::sleep};

use lazy_static::lazy_static;
use pretty_env_logger;
use tokio::sync::RwLock;
use warp::{
    hyper::{body::Bytes, StatusCode},
    Filter,
};
const BUFFER_SIZE: usize = 1 << 13;
const ORIGIN: &str = "http://cs5700cdnorigin.ccs.neu.edu:8080/";
lazy_static! {
    static ref RAM_CACHE: RwLock<HashMap<String, Vec<u8>>> = RwLock::new(HashMap::new());
}
#[tokio::main]
async fn main() {
    if std::env::var_os("RUST_LOG").is_none() {
        std::env::set_var("RUST_LOG", "server=debug");
    }
    pretty_env_logger::init_timed();
    let beacon = warp::path!("grading" / "beacon").map(|| StatusCode::NO_CONTENT);
    let preload =
        warp::path!("preload")
            .and(warp::body::bytes())
            .and_then(|body: Bytes| async move {
                let body = String::from_utf8(body.to_vec()).unwrap();
                preload(body).await
            });
    let root = warp::path::end().and_then(|| proxy(String::new()));
    let proxy = warp::path!(String).and_then(proxy);

    let routes = root
        .or(preload)
        .or(beacon)
        .or(proxy)
        .with(warp::log("server"));
    warp::serve(routes).run(([0, 0, 0, 0], 25015)).await;
}

async fn fetch_from_origin(path: &str) -> Result<String, reqwest::Error> {
    dbg!(format!("Fetch: {}",&path));
    let response = reqwest::get(format!("{}{}", ORIGIN, path)).await?;
    return response.text().await;
}

async fn preload(body: String) -> Result<impl warp::Reply, warp::Rejection> {
    let mut ram_cache = RAM_CACHE.write().await;
    for path in body.split(";").into_iter() {
        let response = fetch_from_origin(&path).await.unwrap();
        ram_cache.insert(path.to_string(), compress(&response));
    }
    Ok(StatusCode::NO_CONTENT)
}

fn compress(content: &String) -> Vec<u8> {
    brotli::CompressorReader::new(content.as_bytes(), BUFFER_SIZE, 11, 24)
        .bytes()
        .map(|x| x.unwrap())
        .collect()
}

fn decompress(content: &Vec<u8>) -> String {
    let mut decompressed = String::new();
    brotli::Decompressor::new(&content[..], BUFFER_SIZE)
        .read_to_string(&mut decompressed)
        .expect("decompress failed");
    decompressed
}
async fn proxy(path: String) -> Result<impl warp::Reply, warp::Rejection> {
    sleep(std::time::Duration::from_secs(1));
    let ram_cache = RAM_CACHE.read().await;
    if ram_cache.contains_key(&path) {
        Ok(decompress(ram_cache.get(&path).unwrap()))
    } else {
        match tokio::fs::read(format!("./disk/{}", path)).await {
            Ok(content) => Ok(decompress(&content)),
            Err(_) => Ok(fetch_from_origin(&path).await.unwrap()),
        }
    }
}
