using System;
using System.Diagnostics;
using System.IO;
using Microsoft.Win32;

namespace EbsLauncher
{
    // Edge → Chrome → 기본 브라우저 순으로 앱 창(--app)을 연다.
    public static class BrowserLauncher
    {
        public static void Open(string url)
        {
            string browser = Find("msedge.exe", @"Microsoft\Edge\Application\msedge.exe")
                          ?? Find("chrome.exe", @"Google\Chrome\Application\chrome.exe");
            if (browser != null)
            {
                try
                {
                    Process.Start(new ProcessStartInfo(browser, "--app=" + url + " --window-size=1280,860") { UseShellExecute = false });
                    return;
                }
                catch (System.ComponentModel.Win32Exception) { }
            }
            Process.Start(url);
        }

        static string Find(string exe, string rel)
        {
            foreach (var env in new[] { "ProgramFiles(x86)", "ProgramFiles", "LocalAppData" })
            {
                string dir = Environment.GetEnvironmentVariable(env);
                if (string.IsNullOrEmpty(dir)) continue;
                string p = Path.Combine(dir, rel);
                if (File.Exists(p)) return p;
            }
            foreach (var hive in new[] { Registry.CurrentUser, Registry.LocalMachine })
            {
                using (var k = hive.OpenSubKey(@"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\" + exe))
                {
                    string p = k == null ? null : k.GetValue(null) as string;
                    if (!string.IsNullOrEmpty(p) && File.Exists(p)) return p;
                }
            }
            return null;
        }
    }
}
