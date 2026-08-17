const API = globalThis.browser ?? globalThis.chrome;
const HOST_NAME = "com.uwuconverter.browser";
const ROOT_MENU_ID = "uwuconverter-root";

const OUTPUT_FORMATS = [
  ["png", "PNG"],
  ["jpg", "JPG"],
  ["jpeg", "JPEG"],
  ["webp", "WEBP"],
  ["ico", "ICO"],
  ["tif", "TIF"],
  ["tiff", "TIFF"],
  ["pdf", "PDF"],
];

function notify(title, message) {
  try {
    const result = API.notifications.create({
      type: "basic",
      iconUrl: API.runtime.getURL("icons/icon-128.png"),
      title,
      message,
    });

    if (result && typeof result.catch === "function") {
      result.catch(() => {});
    }
  } catch (_) {
    // Notification failure should never make conversion fail.
  }
}

async function createMenus() {
  await API.contextMenus.removeAll();

  API.contextMenus.create({
    id: ROOT_MENU_ID,
    title: "UwUConverter",
    contexts: ["image"],
  });

  for (const [format, label] of OUTPUT_FORMATS) {
    API.contextMenus.create({
      id: `uwuconverter-image-${format}`,
      parentId: ROOT_MENU_ID,
      title: `Download as ${label}`,
      contexts: ["image"],
    });
  }
}

API.runtime.onInstalled.addListener(() => {
  createMenus().catch((error) => {
    console.error("UwUConverter menu setup failed", error);
  });
});

API.contextMenus.onClicked.addListener(async (info) => {
  const menuId = String(info.menuItemId);
  const prefix = "uwuconverter-image-";

  if (!menuId.startsWith(prefix)) {
    return;
  }

  const format = menuId.slice(prefix.length);
  const sourceUrl = info.srcUrl;

  if (!sourceUrl) {
    notify(
      "UwUConverter",
      "This image does not expose a downloadable source URL."
    );
    return;
  }

  try {
    const response = await API.runtime.sendNativeMessage(
      HOST_NAME,
      {
        action: "download_image",
        url: sourceUrl,
        pageUrl: info.pageUrl ?? null,
        format,
      }
    );

    if (!response || response.ok !== true) {
      throw new Error(
        response?.error ?? "UwUConverter did not return a valid response."
      );
    }

    notify(
      "UwUConverter",
      `Saved ${response.filename ?? `image.${format}`} to Downloads.`
    );
  } catch (error) {
    let message = error?.message ?? String(error);

    if (
      message.includes("native messaging host") ||
      message.includes("Native host") ||
      message.includes("not found")
    ) {
      message =
        "UwUConverter's browser host is not registered. Reinstall or refresh UwUConverter, then restart the browser.";
    }

    notify("UwUConverter conversion failed", message);
  }
});
