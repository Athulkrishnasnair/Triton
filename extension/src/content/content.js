console.log("[Kirchlen] content script loaded");

let video = null;

function findVideo() {
    const candidate = document.querySelector("video");

    if (candidate && candidate !== video) {
        video = candidate;

        console.log("[Kirchlen] YouTube video detected");

        setupKirchlen();
    }
}

function setupKirchlen() {
    console.log("[Kirchlen] video dimensions:", {
        width: video.videoWidth,
        height: video.videoHeight
    });

    console.log("[Kirchlen] duration:", video.duration);
}

findVideo();

const observer = new MutationObserver(findVideo);

observer.observe(document.body, {
    childList: true,
    subtree: true
});