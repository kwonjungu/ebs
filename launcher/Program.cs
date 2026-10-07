using System;
using System.Drawing;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Windows.Forms;

namespace EbsLauncher
{
    static class Program
    {
        const string Title = "AI 탐험대";

        [STAThread]
        static int Main(string[] args)
        {
            var opt = Options.Parse(args);
            string root = opt.Root ?? Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "app");
            string url = "http://127.0.0.1:" + opt.Port + "/";

            if (!File.Exists(Path.Combine(root, "index.html")))
            {
                Notify(opt, "앱 파일(app 폴더)을 찾을 수 없어요.\n\n압축 파일(zip)을 먼저 [모두 압축 풀기] 한 다음,\n풀린 폴더 안의 AI탐험대.exe를 실행해 주세요.");
                return 2;
            }

            var server = new StaticServer(root, opt.Port);
            try { server.Start(); }
            catch (SocketException)
            {
                if (IsOurServer(url))
                {
                    if (opt.OpenBrowser) BrowserLauncher.Open(url);
                    return 0;
                }
                Notify(opt, "다른 프로그램이 " + opt.Port + "번 포트를 쓰고 있어서 시작할 수 없어요.\n\n컴퓨터를 다시 시작한 뒤 실행하거나, 온라인 주소를 사용해 주세요.\nhttps://kwonjungu.github.io/ebs/");
                return 3;
            }

            if (opt.OpenBrowser) BrowserLauncher.Open(url);
            RunTray(server, url);
            return 0;
        }

        static bool IsOurServer(string url)
        {
            try
            {
                var req = (HttpWebRequest)WebRequest.Create(url.TrimEnd('/') + StaticServer.PingPath);
                req.Proxy = null;          // 학교 프록시로 새지 않게
                req.Timeout = 2000;
                using (var res = req.GetResponse())
                using (var r = new StreamReader(res.GetResponseStream()))
                    return r.ReadToEnd() == StaticServer.PingBody;
            }
            catch (WebException) { return false; }
        }

        static void Notify(Options opt, string message)
        {
            if (!opt.Quiet) MessageBox.Show(message, Title, MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        static void RunTray(StaticServer server, string url)
        {
            var menu = new ContextMenuStrip();
            var tray = new NotifyIcon
            {
                Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath),
                Text = Title + " 실행 중",
                ContextMenuStrip = menu,
                Visible = true,
            };
            menu.Items.Add("다시 열기", null, (s, e) => BrowserLauncher.Open(url));
            menu.Items.Add("종료", null, (s, e) => { server.Stop(); tray.Visible = false; Application.Exit(); });
            tray.DoubleClick += (s, e) => BrowserLauncher.Open(url);
            tray.ShowBalloonTip(3000, Title, "실행 중이에요. 끝낼 때는 이 나침반 아이콘을 오른쪽 클릭 → 종료", ToolTipIcon.Info);
            Application.Run();
            tray.Dispose();
        }
    }
}
