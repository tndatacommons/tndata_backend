import _ from 'lodash';

function debug(msg) {
    const debugEl = document.getElementById("extra-debug");
    if(debugEl) {
        debugEl.innerHTML = debugEl.innerHTML +
            "<p style='border-top:1px solid #aaa;margin:0;padding:5px;font-family:monospace;'>" + msg + "</p>";
    }
}

/*
 * Stolen from:
 * https://gist.github.com/mathewbyrne/1280286
 *
 */
function slugify(text)
{
  return text.toString().toLowerCase()
    .replace(/\s+/g, '-')           // Replace spaces with -
    .replace(/[^\w\-]+/g, '')       // Remove all non-word chars
    .replace(/\-\-+/g, '-')         // Replace multiple - with single -
    .replace(/^-+/, '')             // Trim - from start of text
    .replace(/-+$/, '');            // Trim - from end of text
}

/*
 * If the given text contains a link to a youtube video, this function
 * will parse the text and extract two bits of data:
 *
 * 1. The video URL, and
 * 2. The video ID.
 *
 * If matched, this function returns an object of the form:
 *
 *  {
 *      videoId: '...',
 *      embedUrl: '...',
 *  }
 *
 * Otherwise, it returns a false value.
 *
 * This current works for both short, and long share urls:
 * - https://www.youtube.com/watch?v=fd6clpIvrfg
 * - https://youtu.be/fd6clpIvrfg
 */
function extractVideo(text) {
    let result = false;
    let videoId = null;
    let videoLink = null;
    const short_re = /https:\/\/youtu.be\/(\w+)/;
    const long_re = /https:\/\/www.youtube.com\/watch\?v=(\w+)/;

    if(short_re.test(text)) {
        // Note: returns ["https://youtu.be/fd6clpIvrfg", "fd6clpIvrfg"]
        [videoLink, videoId] = short_re.exec(text);
        result = {
            videoId: videoId,
            videoLink: videoLink,
            embedUrl: "https://www.youtube.com/embed/" + videoId
        }
    }
    else if(long_re.test(text)) {
        [videoLink, videoId] = long_re.exec(text);
        result = {
            videoId: videoId,
            videoLink: videoLink,
            embedUrl: "https://www.youtube.com/embed/" + videoId
        }
    }
    return result;
}

export { debug, slugify, extractVideo };
