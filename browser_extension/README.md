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

## Chromium-family development install

The same Chromium extension package is used for:

- Google Chrome
- Chromium
- Microsoft Edge
- Opera
- Opera GX
- Brave
- Vivaldi
- Chrome/Edge beta and developer channels

Opera and Opera GX use Chrome-compatible extensions. Opera's Native Messaging
documentation also uses the Google Chrome native-host registration location on
Windows, so UwUConverter registers there automatically.


1. Build/install UwUConverter so `UwUConverterBrowserHost` is installed and registered.
2. Open the browser's extensions page, for example `chrome://extensions`, `edge://extensions`, `chromium://extensions`, `opera://extensions`, `brave://extensions`, or `vivaldi://extensions`.
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

The Chromium ZIP is intentionally shared between Chrome, Edge, Opera, Opera GX,
Brave, Vivaldi, Chromium, and compatible Chromium forks. They all receive the
same pinned development extension ID when loaded from this package.


## Installer-assisted setup

Windows and Linux builds now include `UwUConverterBrowserSetup`.

After a normal install it detects:

- Google Chrome
- Chromium
- Microsoft Edge
- Opera
- Opera GX
- Brave
- Vivaldi
- Firefox

and offers an **Install extension** button for each detected browser.

Until the extension is published in browser stores, the helper opens the
browser's extension manager and the bundled unpacked extension folder. After
store URLs are configured in `browser_setup.py`, the same buttons open the
normal browser-store installation page instead.

The setup window is remembered per browser. Normal application updates do not
keep showing it again for browsers the user has already been offered. It will
appear again automatically if a newly detected browser is installed.

You can reopen it manually with:

```bash
UwUConverter browser-setup
```

### Linux notes

Native package installations of Chrome/Chromium/Edge/Opera/Opera GX/Brave/
Vivaldi/Firefox are registered by the UwUConverter installer. Common user
profile locations are covered.

Flatpak browsers are detected by the browser setup helper too. The extension
itself can be installed, but a Flatpak sandbox can restrict execution of an
external Native Messaging host. If Native Messaging fails in a Flatpak build,
test the browser's native distro package before treating it as an extension bug.
