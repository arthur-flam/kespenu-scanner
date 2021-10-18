// shim to insulate apps from spec changes and prefix differences in WebRTC.
import { useRef, useState, useEffect } from 'react';
import adapter from 'webrtc-adapter';
import axios from 'axios'

import Head from 'next/head'
import Image from 'next/image'
import styles from '../styles/Home.module.css'

const api_prefix = "/api/v1"

// we only want to identify barcodes commonly found in retail
// https://developer.mozilla.org/en-US/docs/Web/API/Barcode_Detection_API#supported_barcode_formats
const formats_1d = [
  'upc_a',
  'upc_e',
  'ean_13',
  'ean_8',
  'itf',
  // 'code_128',
  // 'code_39',
  // 'code_93',
]


// prefer the back-facing camera
// https://developer.mozilla.org/fr/docs/Web/API/MediaDevices/getUserMedia
const media_constraints = {
  audio: false,
  video: {
    facingMode: "environment"
  }
};


  
const Scanner = () => {
  // controls and debug the barcode detection
  const [barcode, setBarcode] = useState(null);
  const [status, setStatus] = useState('standby');
  const videoElement = useRef(null);
  const [debug_message, setDebugMessage] = useState(null);
  const [video_error, setVideoError] = useState(null);
  const [barcode_error, setBarcodeError] = useState(null);
  const requestRef = useRef();
  const previousTimeRef = useRef();

  // getting data about a specific barcode
  const [barcode_data, setBarcodeData] = useState(null);
  const [is_loading, setLoading] = useState(false);

  useEffect(() => {
    const InitScan = async () => {
      setBarcode(null)

      // if (!window.isSecureContext) {
      //   setVideoError({name: 'Video Unavailable', message: 'navigator.mediaDevices is only available in Secure Contexts: https://developer.mozilla.org/en-US/docs/Web/Security/Secure_Contexts'})
      //   setStatus('standby')
      //   return
      // }

      // will ask the user to authorize access to the camera
      navigator.mediaDevices.getUserMedia(media_constraints)
      .then(stream => {
        videoElement.current.onloadedmetadata = e => {videoElement.current.play()};
        videoElement.current.srcObject = stream;
        setVideoError(null)
      }).catch(err => {
        setVideoError(err)
        setStatus('standby')
      })

      if (!('BarcodeDetector' in window)) {
        // https://developer.mozilla.org/en-US/docs/Web/API/BarcodeDetector#browser_compatibility
        setBarcodeError('This browser cannot detect barcodes. Please try in Android with Chrome/Opera/Webview. We will add support for iOS/Firefox/Desktop in the near future.');
      } else {
        let formats = await BarcodeDetector.getSupportedFormats()
        formats = formats.filter(f => formats_1d.includes(f))
        var barcodeDetector = new BarcodeDetector({formats});

        const animate = time => {
          let first_loop = previousTimeRef.current === undefined
          if (!first_loop) {
            var detected_barcode = false
            barcodeDetector
              .detect(videoElement.current)
              .then(barcodes => {
                setBarcodeError(null)
                if (barcodes.length > 0) {
                  setBarcode(barcodes[0].rawValue) // .rawValue
                  setBarcodeError(null)
                  detected_barcode = true
                  setStatus('standby')
                }
              })
              .catch(error => {
                setBarcodeError(JSON.stringify([error.name, error.message]))
                // setBarcode(null)
              })
              .finally(e => {
                // const deltaTime = time - previousTimeRef.current
                // setDebugMessage(`${Math.round(1000/(deltaTime))}FPS ${Math.round(deltaTime)}ms detected_barcode:${detected_barcode}`)
                if (!detected_barcode)
                  requestAnimationFrame(animate)
                // requestRef.current = requestAnimationFrame(animate)
              });
          }
          previousTimeRef.current = time;
          if (first_loop) {
            requestRef.current = requestAnimationFrame(animate);
          }
        }
      
        requestRef.current = requestAnimationFrame(animate);
        return () => cancelAnimationFrame(requestRef.current);
      }
    }

    if (status === "scan") {
      InitScan()
    } else {
      videoElement.current.srcObject = null
      if (requestRef.current)
        cancelAnimationFrame(requestRef.current)
    }
  }, [status])

  useEffect(() => {
    const fetchBarcodeData = async () => {
      if (barcode === null)
        return
      setLoading(true)
      try {
        const result = await axios.get(`${api_prefix}/barcode/${barcode}`)
        setBarcodeData(result.data);
        setLoading(false)  
      } catch (err) {
        setDebugMessage(JSON.stringify(err))
      }
      setLoading(false)
      return
    }
    fetchBarcodeData()
  }, [barcode])

  return (
    <div className={styles.card}>
      <h2 style={{textAlign: 'center'}}><button onClick={() => {setStatus(status === 'scan' ? 'standby' : 'scan')}}>{status === 'scan' ? '⏹️ Stop' : '📷 Barcode'}</button></h2>
      {!!barcode && !!!barcode_data && <p>Scanned <code>{barcode}</code> ! Wait a second for more...</p>}
      <p style={{display: status === 'scan' ? undefined : 'none'}}>
        <video style={{width: "100%"}} ref={videoElement}/>
      </p>
      {/* <p><strong>Status:</strong> {status}</p> */}
      {debug_message && <p>{debug_message}</p>}
      {video_error && <p style={{color: 'red'}}><strong>{video_error.name}</strong> {video_error.message}</p>}
      {barcode_error && <p style={{color: 'red'}}><strong>Barcode Error:</strong> {barcode_error}</p>}
      {!!barcode_data && <p><Barcode data={barcode_data} /></p>}
    </div>
  );
}

const not_interesting = ['barcode', 'name']
const Barcode = ({barcode_id, data}) => {
  const src = data.meta?.shufersal?.images?.[0];
  return <>
    <h2>{data.item.name} <code>{barcode_id}</code></h2>
    <p>{data.item.manufacturer_description}</p>
    {src && <img key={src} style={{maxWidth: '100%'}} alt={`photo of ${data.item.name}`} src={src}/>}
    {data.meta?.shufersal?.ingredients && <>
      <h3>Ingredients</h3>
      <p>{data.meta?.shufersal?.ingredients}</p>
    </>}
    {data.meta?.shufersal?.productSymbols && data.meta?.shufersal?.productSymbols.map(src => <img key={src} src={src}/> )}
    {data.meta?.shufersal?.featuresList && <>
      <h3>Allergens</h3>
      <p>{data.meta?.shufersal?.featuresList}</p>
    </>}
    {data.prices.shufersal && <>
      <h3>Shufersal Price</h3>
      <p><strong>{data.prices.shufersal.price}₪</strong> ({data.prices.shufersal.price_per_unit_of_measure}₪ / {data.item.unit_of_measure})</p>
      {!data.prices.shufersal.allow_discount && <p style={{color: 'red'}}>No discount allowed</p>}
      <p style={{color: 'lightgrey'}}>in the <em>Ashdod Hertzel</em> store</p>
      <p style={{color: 'lightgrey'}}>updated 12h ago</p>
      {data.promos.shufersal && data.promos.shufersal.map(p => {
        return <details key={p.promo_id}>
          <summary>Promotion {Math.round(100*p.discount)}% at {Math.round(p.price)}₪</summary>
          <div>
            <p>{p.description}</p>
            <p>{JSON.stringify(data.promos.shufersal)}</p>
          </div>
        </details>
      })}
    </>}
    <h3>Info</h3>
    <ul>
      <li><strong>Quantity:</strong> {data.item.quantity} {data.item.unit}</li>
      <li><strong>Manufacturer:</strong> {data.item.manufacturer_name}</li>
      <li><strong>Country:</strong> {data.item.manufacturer_country}</li>      
    </ul>
    {!!data.openfoodfacts && <p>{JSON.stringify(data.openfoodfacts)}</p>}
    {!!data.openfoodfacts && <ul>
      {Object.entries(data.item ?? {})
          .filter(([k, v]) => !not_interesting.includes(k))
          .map( ([k, v]) => v ? <li key={k}><strong>{k}:</strong> {JSON.stringify(v)}</li> : <></>)}
    </ul>}
  </>
}

export default function Home() {
  return (
    <>
      <Head>
        <title>Create Next App</title>
        <meta name="description" content="Generated by create next app" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className={styles.main}>
        <h1 className={styles.title}>
          <Image src="/kespenu.svg" height={200} width={200} style={{marginTop: '-15px'}}/>
          <br/>
          Scan
        </h1>

        {/* <p className={styles.description}>
          Know more about what you buy
        </p> */}

        <div style={{marginTop: '50px', display: 'flex', justifyContent: 'center'}}>
          <Scanner/>
        </div>
      </main>

      <footer className={styles.footer}>
        Made by <a href="https://www.linkedin.com/in/ArthurFlam">Arthur Flam</a>
      </footer>
    </>
  )
}
