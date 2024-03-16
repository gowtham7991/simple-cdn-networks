use async_std::fs;
use async_std::sync::Mutex;
use async_std::task::sleep;
use brotli;
use brotli::enc::backward_references::BrotliEncoderMode;
use brotli::enc::BrotliEncoderParams;
use brotli::interface;
use brotli::writer::StandardAlloc;
use brotli::Allocator;
use brotli::InputReferenceMut;
use brotli::IoReaderWrapper;
use brotli::IoWriterWrapper;
use lazy_static::lazy_static;
use reqwest;
use std::collections::HashMap;
use std::io::Error;
use std::io::ErrorKind;
use std::io::Read;
use std::time::Duration;
use tide::log;
use tide::Request;
use tide::Response;

const BUFFER_SIZE: usize = 1 << 13;
const ORIGIN: &str = "http://cs5700cdnorigin.ccs.neu.edu:8080";
lazy_static! {
    static ref REQUEST: reqwest::Client = reqwest::Client::new();
    static ref RAM_CACHE: Mutex<HashMap<String, Vec<u8>>> = Mutex::new(HashMap::new());
    static ref DICT: &'static [u8] = include_bytes!("../custom_dict.bin");
}

#[async_std::main]
async fn main() -> tide::Result<()> {
    log::start();
    let mut app = tide::new();
    // app.with(tide_compress::CompressMiddleware::new());
    app.at("/preload").post(preload);
    app.at("/grading/beacon").get(beacon);
    app.at("/").get(proxy);
    app.at("/*").get(proxy);
    app.listen("0.0.0.0:25015").await?;
    Ok(())
}
async fn beacon(_req: Request<()>) -> tide::Result {
    Ok(Response::builder(200).build())
}

async fn fetch_from_origin(path: &str) -> Result<String, reqwest::Error> {
    log::info!("fetching from origin {}", path);
    let response = reqwest::get(format!("{}{}", ORIGIN, path)).await?;
    return response.text().await;
}

fn compress(content: &String) -> Vec<u8> {
    let dict = &DICT[..];
    let mut compressed = Vec::new();
    compressed.reserve(content.len());

    let mut params = BrotliEncoderParams::default();
    params.quality = 11;
    params.lgwin = 22;
    params.mode = BrotliEncoderMode::BROTLI_MODE_TEXT;
    params.magic_number = false;
    params.use_dictionary = true;

    let mut nop_callback = |_data: &mut interface::PredictionModeContextMap<InputReferenceMut>,
                            _cmds: &mut [interface::StaticCommand],
                            _mb: interface::InputPair,
                            _m: &mut StandardAlloc| ();

    brotli::BrotliCompressCustomIoCustomDict(
        &mut IoReaderWrapper(&mut content.as_bytes()),
        &mut IoWriterWrapper(&mut compressed),
        &mut [0u8; BUFFER_SIZE / 2],
        &mut [0u8; BUFFER_SIZE / 2],
        &params,
        StandardAlloc::default(),
        &mut nop_callback,
        dict,
        Error::new(ErrorKind::UnexpectedEof, "Unexpected EOF"),
    )
    .expect("BrotliCompressCustomIoCustomDict failed");
    compressed
}

fn decompress(content: &Vec<u8>) -> String {
    let d = Vec::from(&DICT[..]);
    let dict = <StandardAlloc as Allocator<u8>>::AllocatedMemory::from(d);
    let bytes: Vec<u8> =
        brotli::Decompressor::new_with_custom_dict(&content[..], BUFFER_SIZE, dict)
            .bytes()
            .map(|x| x.unwrap())
            .collect();
    let ret = String::from_utf8(bytes).unwrap();
    ret
}

async fn preload(mut req: Request<()>) -> tide::Result {
    let body = req.body_string().await?;
    let mut ram_cache = RAM_CACHE.lock().await;
    for path in body.split(",").into_iter() {
        let response = fetch_from_origin(&path).await?;
        ram_cache.insert(path.to_string(), compress(&response));
    }
    Ok("OK".into())
}
async fn proxy(req: Request<()>) -> tide::Result {
    // sleep(Duration::from_secs(1)).await;

    let path = req.url().path().to_string();
    let ram_cache = RAM_CACHE.lock().await;

    if ram_cache.contains_key(&path) {
        return Ok(decompress(ram_cache.get(&path).unwrap()).into());
    }
    match fs::read(format!("./disk{}", path)).await {
        Ok(content) => {
            return Ok(decompress(&content).into());
        }
        Err(_) => {
            return Ok(fetch_from_origin(&path).await?.into());
        }
    }
}
