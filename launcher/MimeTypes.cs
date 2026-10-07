using System.Collections.Generic;

namespace EbsLauncher
{
    public static class MimeTypes
    {
        static readonly Dictionary<string, string> Map = new Dictionary<string, string>
        {
            { ".html", "text/html; charset=utf-8" }, { ".htm", "text/html; charset=utf-8" },
            { ".js", "text/javascript; charset=utf-8" }, { ".mjs", "text/javascript; charset=utf-8" },
            { ".css", "text/css; charset=utf-8" }, { ".json", "application/json" },
            { ".txt", "text/plain; charset=utf-8" }, { ".md", "text/plain; charset=utf-8" },
            { ".wasm", "application/wasm" },
            { ".png", "image/png" }, { ".jpg", "image/jpeg" }, { ".jpeg", "image/jpeg" },
            { ".gif", "image/gif" }, { ".svg", "image/svg+xml" }, { ".ico", "image/x-icon" }, { ".webp", "image/webp" },
            { ".woff2", "font/woff2" }, { ".woff", "font/woff" }, { ".ttf", "font/ttf" }, { ".otf", "font/otf" },
            { ".mp3", "audio/mpeg" }, { ".wav", "audio/wav" }, { ".mp4", "video/mp4" },
        };

        // .ent(gzip 원본), .task, .tflite, .bin 등은 모두 octet-stream으로 바이트 그대로 보낸다.
        public static string For(string ext)
        {
            string t;
            return Map.TryGetValue((ext ?? "").ToLowerInvariant(), out t) ? t : "application/octet-stream";
        }
    }
}
