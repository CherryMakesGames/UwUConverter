# UwUConverter browser integration

This extension adds an `UwUConverter` submenu when you right-click an image in the browser.

Current image actions:

- Download as PNG
- Download as JPG
- Download as JPEG
- Download as WEBP
- Download as ICO
- Download as TIF
- Download as TIFF
- Download as PDF

The extension does not convert the image itself. It sends the image URL and selected output format to the locally installed `com.uwuconverter.browser` native messaging host. The host downloads the image, uses UwUConverter's existing `image_converter.py`, and saves the converted file into the operating system's Downloads folder.

## Current v1 limitations

- Normal `http://` and `https://` image URLs are supported.
- `data:` images are supported.
- `blob:` images are not supported yet.
- Sites whose images require browser cookies/authentication may reject the native host's download request.
- The destination is the operating system Downloads folder. A custom browser download directory cannot currently be discovered by the native host.

## Chromium development install

1. Build/install UwUConverter so `UwUConverterBrowserHost` is installed and registered.
2. Open `chrome://extensions`, `edge://extensions`, or `chromium://extensions`.
3. Enable Developer mode.
4. Choose **Load unpacked**.
5. Select `browser_extension/chromium`.
6. Restart the browser after installing/updating the UwUConverter desktop app if native messaging was not available yet.

The Chromium development manifest contains a fixed public `key`, so the unpacked extension keeps the development ID:

`gdopoipkbfpeojmblonjjmkflahgfihg`

If the extension is later published in a browser store and receives a different ID, update `CHROMIUM_EXTENSION_ID` in `browser_integration.py` and rebuild/reinstall UwUConverter.

## Firefox development install

1. Build/install UwUConverter.
2. Open `about:debugging#/runtime/this-firefox`.
3. Choose **Load Temporary Add-on**.
4. Select `browser_extension/firefox/manifest.json`.

Firefox uses the fixed development add-on ID:

`uwuconverter@pinksakurastudios.com`

Permanent normal Firefox installation requires a signed add-on package when distributed outside development mode.

## Build extension ZIPs

Run:

```bash
python build_browser_extensions.py
```

Generated packages are written under `browser_extension/dist/`.
