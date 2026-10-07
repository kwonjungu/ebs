using System;
using System.IO;
using System.Windows.Forms;

namespace EbsLauncher
{
    static class Program
    {
        [STAThread]
        static int Main(string[] args)
        {
            var opt = Options.Parse(args);
            string root = opt.Root ?? Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "app");
            var server = new StaticServer(root, opt.Port);
            server.Start();
            Application.Run();
            return 0;
        }
    }
}
