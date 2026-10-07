using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;

namespace EbsLauncher
{
    // app\ 폴더를 127.0.0.1에서만 서빙한다. GET/HEAD만, 요청마다 연결을 닫는다.
    public sealed class StaticServer
    {
        public const string PingPath = "/__ebs_ping";
        public const string PingBody = "ebs-ai-explorer";
        const int MaxHead = 16 * 1024;

        readonly string root;   // 끝에 \ 포함
        readonly TcpListener listener;
        volatile bool running;

        public StaticServer(string root, int port)
        {
            this.root = Path.GetFullPath(root).TrimEnd('\\') + "\\";
            listener = new TcpListener(IPAddress.Loopback, port);
        }

        public void Start()
        {
            listener.Start();   // 포트 사용 중이면 SocketException
            running = true;
            var t = new Thread(AcceptLoop) { IsBackground = true };
            t.Start();
        }

        public void Stop()
        {
            running = false;
            try { listener.Stop(); } catch (SocketException) { }
        }

        void AcceptLoop()
        {
            while (running)
            {
                TcpClient c;
                try { c = listener.AcceptTcpClient(); }
                catch (SocketException) { if (!running) return; continue; }
                catch (ObjectDisposedException) { return; }
                ThreadPool.QueueUserWorkItem(_ => Handle(c));
            }
        }

        void Handle(TcpClient c)
        {
            using (c)
            {
                try
                {
                    c.ReceiveTimeout = 10000;
                    c.SendTimeout = 60000;
                    var s = c.GetStream();
                    string head = ReadHead(s);
                    if (head == null) return;
                    string[] parts = head.Substring(0, head.IndexOf("\r\n", StringComparison.Ordinal)).Split(' ');
                    if (parts.Length != 3) { SendText(s, 400, "Bad Request", false); return; }
                    bool isHead = parts[0] == "HEAD";
                    if (parts[0] != "GET" && !isHead) { SendText(s, 405, "Method Not Allowed", false); return; }
                    Respond(s, parts[1], isHead);
                }
                catch (IOException) { }
                catch (SocketException) { }
                catch (ObjectDisposedException) { }
            }
        }

        static string ReadHead(Stream s)
        {
            var buf = new byte[4096];
            var acc = new MemoryStream();
            while (acc.Length < MaxHead)
            {
                int n = s.Read(buf, 0, buf.Length);
                if (n <= 0) return null;
                acc.Write(buf, 0, n);
                string text = Encoding.ASCII.GetString(acc.GetBuffer(), 0, (int)acc.Length);
                if (text.Contains("\r\n\r\n")) return text;
            }
            return null;
        }

        void Respond(Stream s, string target, bool isHead)
        {
            string path = target;
            int q = path.IndexOfAny(new[] { '?', '#' });
            string query = q >= 0 ? path.Substring(q) : "";
            if (q >= 0) path = path.Substring(0, q);

            if (path == PingPath) { SendText(s, 200, PingBody, isHead); return; }

            string decoded;
            try { decoded = Uri.UnescapeDataString(path); }
            catch (UriFormatException) { SendText(s, 400, "Bad Request", isHead); return; }
            if (decoded.IndexOf('\0') >= 0 || !decoded.StartsWith("/")) { SendText(s, 400, "Bad Request", isHead); return; }

            string full;
            try { full = Path.GetFullPath(Path.Combine(root, decoded.TrimStart('/').Replace('/', '\\'))); }
            catch (ArgumentException) { SendText(s, 400, "Bad Request", isHead); return; }
            catch (NotSupportedException) { SendText(s, 400, "Bad Request", isHead); return; }
            catch (PathTooLongException) { SendText(s, 400, "Bad Request", isHead); return; }
            if (!(full.TrimEnd('\\') + "\\").StartsWith(root, StringComparison.OrdinalIgnoreCase))
            { SendText(s, 403, "Forbidden", isHead); return; }

            if (Directory.Exists(full))
            {
                if (!path.EndsWith("/"))
                {
                    WriteHead(s, 301, "Moved Permanently", "text/plain; charset=utf-8", 0, "Location: " + path + "/" + query + "\r\n");
                    return;
                }
                full = Path.Combine(full, "index.html");
            }
            if (!File.Exists(full)) { SendText(s, 404, "Not Found", isHead); return; }

            using (var fs = new FileStream(full, FileMode.Open, FileAccess.Read, FileShare.Read, 65536))
            {
                WriteHead(s, 200, "OK", MimeTypes.For(Path.GetExtension(full)), fs.Length, "");
                if (!isHead) fs.CopyTo(s, 65536);
            }
        }

        static void SendText(Stream s, int code, string text, bool isHead)
        {
            byte[] b = Encoding.UTF8.GetBytes(text);
            WriteHead(s, code, code == 200 ? "OK" : text, "text/plain; charset=utf-8", b.Length, "");
            if (!isHead) s.Write(b, 0, b.Length);
        }

        static void WriteHead(Stream s, int code, string reason, string type, long length, string extra)
        {
            string h = "HTTP/1.1 " + code + " " + reason + "\r\n" +
                       "Content-Type: " + type + "\r\n" +
                       "Content-Length: " + length + "\r\n" +
                       "Cache-Control: no-cache\r\n" +
                       "X-Content-Type-Options: nosniff\r\n" +
                       "Connection: close\r\n" + extra + "\r\n";
            byte[] b = Encoding.ASCII.GetBytes(h);
            s.Write(b, 0, b.Length);
        }
    }
}
