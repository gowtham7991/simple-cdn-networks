use actix_web::App;
use actix_web::HttpResponse;
use actix_web::HttpServer;
use actix_web::Responder;
use actix_web::get;
use actix_web::web;
use async_std::sync::Mutex;
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

const BUFFER_SIZE:usize = 8192 ;
const ORIGIN: &str = "http://cs5700cdnorigin.ccs.neu.edu:8080/";
lazy_static! {
    static ref REQUEST: reqwest::Client = reqwest::Client::new();
    static ref CACHE: Mutex<HashMap<String, Vec<u8>>> = Mutex::new(HashMap::new());
}


#[get("/")]
async fn beacon() -> impl Responder {
    HttpResponse::NoContent().finish()
}

async fn fetch_from_origin(path: &str) -> Result<String, reqwest::Error> {
    let response = reqwest::get(format!("{}{}", ORIGIN, path)).await?;
    let v = response.text().await;
    return v;
}

fn compress(content: &String) -> Vec<u8> {
    let mut r = content.as_bytes();
    let mut w = Vec::new();
    let mut input_buffer: [u8; BUFFER_SIZE] = [0; BUFFER_SIZE];
    let mut output_buffer: [u8; BUFFER_SIZE] = [0; BUFFER_SIZE];
    let mut params = BrotliEncoderParams::default();
    params.quality = 11;
    params.lgwin = 22;
    params.mode = BrotliEncoderMode::BROTLI_MODE_TEXT;
    params.magic_number = false;
    params.use_dictionary = true;

    let alloc = StandardAlloc::default();
    let mut nop_callback = |_data: &mut interface::PredictionModeContextMap<InputReferenceMut>,
                            _cmds: &mut [interface::StaticCommand],
                            _mb: interface::InputPair,
                            _m: &mut StandardAlloc| ();

    let eof = Error::new(ErrorKind::UnexpectedEof, "Unexpected EOF");
    let dict = "HTTP/1.1 200 OK\r".as_bytes();
    brotli::BrotliCompressCustomIoCustomDict(
        &mut IoReaderWrapper(&mut r),
        &mut IoWriterWrapper(&mut w),
        &mut input_buffer,
        &mut output_buffer,
        &params,
        alloc,
        &mut nop_callback,
        dict,
        eof,
    ).expect("BrotliCompressCustomIoCustomDict failed");
    w
}

fn decompress(content: &Vec<u8>) -> String {
    let d = Vec::from("HTTP/1.1 200 OK\r".as_bytes());
    let dict = <StandardAlloc as Allocator<u8>>::AllocatedMemory::from(d);
    let bytes: Vec<u8> =
        brotli::Decompressor::new_with_custom_dict(&content[..], 1<<20, dict)
            .bytes()
            .map(|x| x.unwrap())
            .collect();
    let ret = String::from_utf8(bytes).unwrap();
    ret
}

// async fn preload(req: &mut Request<()>) -> tide::Result {
//     let body = req.body_string().await?;
//     let mut cache = CACHE.lock().await;
//     for path in body.split(",").into_iter() {
//         let response = fetch_from_origin(&path).await?;
//         cache.insert(path.to_string(), compress(&response));
//     }
//     Ok("OK".into())
// }

#[get("/{path}")]
async fn proxy(path: web::Path<String>) -> actix_web::Result<String>{
    let path = path.into_inner();
    let mut cache = CACHE.lock().await;
    if cache.contains_key(&path) {
        Ok(decompress(cache.get(&path).unwrap()))
    } else {
        let response = fetch_from_origin(&path).await.expect("Origin failed");
        cache.insert(path, compress(&response));
        Ok(response)
    }
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new()
            .service(beacon)
            .service(proxy)
    })
    .bind(("0.0.0.0", 25015))?
    .run()
    .await
}